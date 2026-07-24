from __future__ import annotations

# ruff: noqa: B008

from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from nerajob import __version__
from nerajob.apply.assistant import prepare_application
from nerajob.cv.builder import write_cv_files
from nerajob.match import DEFAULT_MATCH_WEIGHTS, SKILL_ALIASES, MatchWeights, extract_skills_from_text
from nerajob.models import ApplicationPackage, JobPosting
from nerajob.scrapers.registry import available_scrapers, get_scraper
from nerajob.storage import default_profile, get_job, load_applications, load_jobs, load_profile, load_scan_preset, save_profile, save_scan_preset, upsert_jobs

app = typer.Typer(help="NeraJob — scan jobs, build CV, prepare applications.", no_args_is_help=True)
profile_app = typer.Typer(help="Manage your profile / CV source data.")
jobs_app = typer.Typer(help="Inspect saved jobs.")
app_app = typer.Typer(help="Track application statuses.")
app.add_typer(profile_app, name="profile")
app.add_typer(jobs_app, name="jobs")
app.add_typer(app_app, name="app")
console = Console()


@app.callback()
def main() -> None:
    """NeraJob CLI."""


@app.command("version")
def version_cmd() -> None:
    console.print(f"NeraJob {__version__}")


@app.command("skills")
def skills_cmd(
    text_file: Path | None = typer.Option(
        None,
        "--text-file",
        "-f",
        exists=True,
        readable=True,
        help="Extract skills from a plain-text resume file",
    ),
) -> None:
    """List skill alias groups or extract skills from a text file."""
    if text_file:
        text = text_file.read_text(encoding="utf-8")
        matched = extract_skills_from_text(text)
        if not matched:
            console.print("[yellow]No recognized skills found in text.[/yellow]")
            raise typer.Exit()
        total = sum(len(skills) for skills in matched.values())
        table = Table(title=f"Skills extracted ({total} matches in {len(matched)} domains)")
        table.add_column("Domain")
        table.add_column("Matched skills")
        for domain in sorted(matched):
            table.add_row(domain, ", ".join(sorted(matched[domain])))
        console.print(table)
        return

    table = Table(title=f"Skill aliases ({len(SKILL_ALIASES)})")
    table.add_column("Group")
    table.add_column("Aliases")
    for key, aliases in sorted(SKILL_ALIASES.items()):
        table.add_row(key, ", ".join(sorted(aliases)))
    console.print(table)


@app.command("gui")
def gui_cmd() -> None:
    """Launch the modern Qt desktop app (requires: pip install -e '.[gui]')."""
    from nerajob.gui.app import main as gui_main

    raise SystemExit(gui_main())


@profile_app.command("init")
def profile_init(force: bool = typer.Option(False, help="Overwrite existing profile")) -> None:
    existing = load_profile()
    if existing and not force:
        console.print("[yellow]Profile already exists. Use --force to overwrite.[/yellow]")
        raise typer.Exit(code=1)
    path = save_profile(default_profile())
    console.print(f"[green]Wrote profile template:[/green] {path}")
    console.print("Edit the file, then run: nerajob profile show")


@profile_app.command("show")
def profile_show() -> None:
    profile = load_profile()
    if not profile:
        console.print("[red]No profile. Run: nerajob profile init[/red]")
        raise typer.Exit(code=1)
    console.print_json(profile.model_dump_json(indent=2))


@profile_app.command("preset")
def profile_preset(
    remote_only: bool | None = typer.Option(None, "--remote-only", help="Filter to remote jobs by default"),
    skill_filters: str = typer.Option("", "--skills", help="Comma-separated skills to filter on"),
    min_score: float = typer.Option(-1.0, "--min-score", help="Minimum match score (0–100)"),
    min_salary: int = typer.Option(-1, "--min-salary", help="Minimum annual salary"),
    max_results: int = typer.Option(-1, "--max-results", help="Max results per scan"),
) -> None:
    preset = load_scan_preset()
    if remote_only is not None:
        preset = preset.model_copy(update={"remote_only": remote_only})
    if skill_filters:
        preset = preset.model_copy(update={"skill_filters": [s.strip() for s in skill_filters.split(",") if s.strip()]})
    if min_score >= 0:
        preset = preset.model_copy(update={"min_score": min_score})
    if min_salary >= 0:
        preset = preset.model_copy(update={"min_salary": min_salary})
    if max_results >= 0:
        preset = preset.model_copy(update={"max_results": max_results})
    save_scan_preset(preset)
    console.print("[green]Scan preset saved:[/green]")
    console.print_json(preset.model_dump_json(indent=2))


@app.command("scan")
def scan_cmd(
    query: str = typer.Option("", "--query", "-q", help="Keywords"),
    location: str = typer.Option("", "--location", "-l", help="Location filter"),
    limit: int = typer.Option(20, "--limit", "-n", min=1, max=100),
    source: str = typer.Option(
        "sample",
        "--source",
        "-s",
        help=f"Scraper name: {', '.join(sorted(available_scrapers()))}",
    ),
    all_sources: bool = typer.Option(False, "--all", help="Run all registered scrapers"),
    remote_only: bool | None = typer.Option(None, "--remote-only/--no-remote-only", help="Keep only remote jobs"),
    skill_filters: str = typer.Option("", "--skills", help="Comma-separated skills to filter on"),
    min_score: float = typer.Option(
        -1.0,
        "--min-score",
        help="If profile exists, drop jobs below this match score (0–100)",
    ),
    min_salary: int = typer.Option(
        -1,
        "--min-salary",
        help="Filter jobs by minimum annual salary (e.g. 50000 for 50k)",
    ),
) -> None:
    """Scan job sources and save matches under data/jobs.json."""
    preset = load_scan_preset()
    if remote_only is None:
        remote_only = preset.remote_only
    if not skill_filters:
        skill_filters = ",".join(preset.skill_filters)
    if min_score < 0:
        min_score = preset.min_score
    if min_salary < 0:
        min_salary = preset.min_salary
    if limit == 20 and preset.max_results:
        limit = preset.max_results

    names = list(available_scrapers()) if all_sources else [source]
    collected: list[JobPosting] = []
    for name in names:
        try:
            scraper = get_scraper(name)
        except KeyError as exc:
            console.print(f"[red]{exc}[/red]")
            raise typer.Exit(code=1) from exc
        console.print(f"[cyan]Scanning[/cyan] {name} …")
        found = scraper.search(query=query, location=location, limit=limit)
        console.print(f"  → {len(found)} hits from {name}")
        collected.extend(found)

    if not collected and source != "sample" and not all_sources:
        console.print("[yellow]No hits from live source; falling back to sample feed.[/yellow]")
        collected = get_scraper("sample").search(query=query, location=location, limit=limit)

    # Dedupe across sources: prefer first occurrence, keep stable order
    fetched_count = len(collected)
    seen_keys: set[str] = set()
    deduped: list[JobPosting] = []
    for job in collected:
        key = f"{job.title.strip().lower()}|{job.company.strip().lower()}|{job.url.strip().lower()}"
        if key in seen_keys:
            continue
        seen_keys.add(key)
        deduped.append(job)
    collected = deduped
    if fetched_count != len(collected):
        console.print(f"[dim]Deduped[/dim] {fetched_count} fetched → {len(collected)} unique (dropped {fetched_count - len(collected)} duplicates)")

    if remote_only:
        collected = [
            j
            for j in collected
            if j.remote or "remote" in (j.location or "").lower()
        ]
        console.print(f"[dim]remote-only[/dim] {len(collected)} jobs")

    if skill_filters:
        filter_skills = [s.strip().lower() for s in skill_filters.split(",") if s.strip()]
        before_s = len(collected)
        scored = []
        for job in collected:
            job_tags = [t.lower() for t in (job.tags or [])]
            job_skills = (job.description or "").lower()
            if any(s in job_tags or s in job_skills for s in filter_skills):
                scored.append(job)
        collected = scored
        console.print(f"[dim]skill-filters ({','.join(filter_skills)})[/dim] {before_s} → {len(collected)} jobs")

    if min_score > 0:
        from nerajob.match import match_score

        profile = load_profile()
        if profile:
            before_s = len(collected)
            scored = []
            for job in collected:
                sc = match_score(profile, job)
                if float(sc.get("score") or 0) >= min_score:
                    scored.append(job)
            collected = scored
            console.print(
                f"[dim]min-score {min_score}[/dim] {before_s} → {len(collected)} jobs"
            )
        else:
            console.print("[yellow]--min-score ignored (no profile)[/yellow]")

    if min_salary > 0:
        from nerajob.models import parse_salary_value

        before_s = len(collected)
        filtered = []
        skipped = 0
        for job in collected:
            parsed = parse_salary_value(job.salary or "")
            if parsed is not None and parsed >= min_salary:
                filtered.append(job)
            elif parsed is None:
                # Keep jobs with unparseable salary (don't filter them out)
                filtered.append(job)
            else:
                skipped += 1
        collected = filtered
        console.print(
            f"[dim]min-salary {min_salary}[/dim] {before_s} → {len(collected)} jobs (dropped {skipped} below threshold)"
        )

    merged = upsert_jobs(collected)
    table = Table(title=f"Jobs saved ({len(collected)} new/updated, {len(merged)} total)")
    table.add_column("ID", style="dim")
    table.add_column("Source")
    table.add_column("Title")
    table.add_column("Company")
    table.add_column("Location")
    for job in collected[:limit]:
        table.add_row(job.id, job.source, job.title, job.company, job.location)
    console.print(table)


@jobs_app.command("list")
def jobs_list(
    limit: int = typer.Option(30, min=1, max=200),
    sort: str | None = typer.Option(
        None,
        "--sort",
        help="Sort by 'match' score against profile (requires existing profile)",
    ),
) -> None:
    jobs = load_jobs()[:limit]
    if not jobs:
        console.print("[yellow]No jobs yet. Run: nerajob scan -q python[/yellow]")
        raise typer.Exit()

    if sort == "match":
        profile = load_profile()
        if not profile:
            console.print("[yellow]No profile — can't sort by match score. Showing unsorted.[/yellow]")
        else:
            from nerajob.match import match_score

            scored = [(job, match_score(profile, job)) for job in jobs]
            scored.sort(key=lambda x: x[1]["score"], reverse=True)
            table = Table(title=f"Saved jobs ({len(jobs)}) — sorted by match")
            table.add_column("Score")
            table.add_column("ID")
            table.add_column("Title")
            table.add_column("Company")
            table.add_column("Source")
            for job, m in scored:
                table.add_row(str(m["score"]), job.id, job.title, job.company, job.source)
            console.print(table)
            return

    table = Table(title=f"Saved jobs ({len(jobs)})")
    table.add_column("ID")
    table.add_column("Title")
    table.add_column("Company")
    table.add_column("Source")
    for job in jobs:
        table.add_row(job.id, job.title, job.company, job.source)
    console.print(table)


@app.command("cv")
def cv_cmd(
    target: str = typer.Option("", "--target", "-t", help="Target role title for tailoring"),
    fmt: str = typer.Option("md", "--format", "-f", help="Output format: md or pdf"),
) -> None:
    """Build Markdown + text CV from your profile."""
    profile = load_profile()
    if not profile:
        console.print("[red]No profile. Run: nerajob profile init[/red]")
        raise typer.Exit(code=1)
    paths = write_cv_files(profile, target_role=target, fmt=fmt)
    if fmt == "pdf" and "pdf" not in paths:
        console.print(
            "[yellow]PDF libraries not available.[/yellow] Install optional deps: "
            "[bold]pip install nerajob[pdf][/bold]"
        )
    console.print("[green]CV written:[/green]")
    for kind, path in paths.items():
        console.print(f"  {kind}: {path}")


@app.command("apply")
def apply_cmd(
    job_id: str = typer.Option(..., "--job-id", "-j", help="Job id from nerajob jobs list"),
) -> None:
    """Prepare cover note, checklist, and CV package for a job."""
    profile = load_profile()
    if not profile:
        console.print("[red]No profile. Run: nerajob profile init[/red]")
        raise typer.Exit(code=1)
    job = get_job(job_id)
    if not job:
        console.print(f"[red]Unknown job id:[/red] {job_id}")
        raise typer.Exit(code=1)
    package, path = prepare_application(profile, job)
    console.print(f"[green]Application package saved:[/green] {path}")
    console.print(f"Cover note preview:\n\n{package.cover_note[:500]}…")


@jobs_app.command("export")
def jobs_export(
    out: Path = typer.Option(Path("data/out/jobs.csv"), "--out", "-o"),
    limit: int = typer.Option(500, "--limit", "-n", min=1, max=5000),
) -> None:
    """Export saved jobs to CSV."""
    from nerajob.export_jobs import jobs_to_csv
    from nerajob.storage import load_jobs

    jobs = load_jobs()[:limit]
    if not jobs:
        console.print("[yellow]No jobs. Run: nerajob scan -q python[/yellow]")
        raise typer.Exit()
    path = jobs_to_csv(jobs, out)
    console.print(f"[green]CSV[/green] {path} rows={len(jobs)}")


@jobs_app.command("match")
def jobs_match(
    top: int = typer.Option(10, "--top", "-k", min=1, max=50),
    job_id: str | None = typer.Option(None, "--job-id", "-j"),
    resume_file: Path | None = typer.Option(
        None,
        "--resume-file",
        "-r",
        exists=True,
        readable=True,
        help="Offline: profile JSON file (instead of stored profile)",
    ),
    jobs_file: Path | None = typer.Option(
        None,
        "--jobs-file",
        "-f",
        exists=True,
        readable=True,
        help="Offline: jobs JSON file (instead of stored jobs)",
    ),
    skill_weight: float = typer.Option(
        DEFAULT_MATCH_WEIGHTS.skills,
        "--skill-weight",
        min=0.0,
        help="Maximum score contribution from profile skill matches",
    ),
    title_weight: float = typer.Option(
        DEFAULT_MATCH_WEIGHTS.title,
        "--title-weight",
        min=0.0,
        help="Maximum score contribution from headline/title overlap",
    ),
    location_weight: float = typer.Option(
        DEFAULT_MATCH_WEIGHTS.location,
        "--location-weight",
        min=0.0,
        help="Maximum score contribution from location or remote fit",
    ),
) -> None:
    """Rank saved jobs against your profile (keyword skill match)."""
    from nerajob.match import match_score, rank_jobs
    from nerajob.models import Profile, JobPosting
    from nerajob.storage import load_jobs, load_profile

    profile = None
    jobs: list[JobPosting] = []

    if resume_file and jobs_file:
        import json

        profile_data = json.loads(resume_file.read_text(encoding="utf-8"))
        profile = Profile(**profile_data)
        jobs_data = json.loads(jobs_file.read_text(encoding="utf-8"))
        jobs = [JobPosting(**j) for j in jobs_data]
        console.print(
            f"[dim]Offline match: {len(jobs)} jobs × {len(profile.skills or [])} skills[/dim]"
        )
    else:
        profile = load_profile()
        if not profile:
            console.print("[red]No profile. Run: nerajob profile init[/red]")
            raise typer.Exit(code=1)
        jobs = load_jobs()
        if not jobs:
            console.print("[yellow]No jobs. Run: nerajob scan -q python[/yellow]")
            raise typer.Exit()

    weights = MatchWeights(
        skills=skill_weight,
        title=title_weight,
        location=location_weight,
    )
    if job_id:
        job = next((j for j in jobs if j.id == job_id), None)
        if not job:
            console.print(f"[red]Unknown job id:[/red] {job_id}")
            raise typer.Exit(1)
        console.print_json(data=match_score(profile, job, weights=weights))
        return
    ranked = rank_jobs(profile, jobs, top_k=top, weights=weights)
    table = Table(title=f"Job matches (top {len(ranked)})")
    table.add_column("Score")
    table.add_column("Band")
    table.add_column("Title")
    table.add_column("Company")
    table.add_column("Hits")
    for row in ranked:
        table.add_row(
            str(row["score"]),
            str(row["band"]),
            str(row["title"])[:40],
            str(row["company"])[:24],
            ", ".join(row["skill_hits"][:5]),
        )
    console.print(table)


@app_app.command("list")
def app_list() -> None:
    """List all applications with status, job_id, created_at."""
    packages = load_applications()
    if not packages:
        console.print("[yellow]No applications yet. Run: nerajob apply --job-id <id>[/yellow]")
        raise typer.Exit()
    table = Table(title=f"Applications ({len(packages)})")
    table.add_column("Job ID")
    table.add_column("Status")
    table.add_column("Created")
    table.add_column("Updated")
    for pkg in packages:
        table.add_row(pkg.job_id, pkg.status, pkg.created_at, pkg.updated_at)
    console.print(table)


@app_app.command("show")
def app_show(
    job_id: str = typer.Argument(..., help="Job ID to show application details for"),
) -> None:
    """Show application details."""
    from nerajob.storage import load_application

    pkg = load_application(job_id)
    if not pkg:
        console.print(f"[red]No application found for job id:[/red] {job_id}")
        raise typer.Exit(code=1)
    console.print_json(pkg.model_dump_json(indent=2))


@app_app.command("status")
def app_status(
    job_id: str = typer.Argument(..., help="Job ID"),
    status_value: str | None = typer.Option(
        None,
        "--set",
        help=f"Set status: {sorted(ApplicationPackage.VALID_STATUSES)}",
    ),
) -> None:
    """Get or update application status."""
    from nerajob.storage import load_application

    pkg = load_application(job_id)
    if not pkg:
        console.print(f"[red]No application found for job id:[/red] {job_id}")
        raise typer.Exit(code=1)
    if status_value:
        try:
            pkg.set_status(status_value)
            from nerajob.storage import save_application

            save_application(pkg)
        except ValueError as e:
            console.print(f"[red]{e}[/red]")
            raise typer.Exit(code=1)
        console.print(f"[green]Status updated:[/green] {pkg.job_id} → {pkg.status}")
    else:
        console.print(f"{pkg.job_id}: {pkg.status}")


@app_app.command("stats")
def app_stats() -> None:
    """Show summary of application statuses."""
    packages = load_applications()
    if not packages:
        console.print("[yellow]No applications yet.[/yellow]")
        raise typer.Exit()
    counts: dict[str, int] = {}
    for pkg in packages:
        counts[pkg.status] = counts.get(pkg.status, 0) + 1
    parts = [f"{count} {status}" for status, count in sorted(counts.items())]
    console.print("Application summary:")
    console.print(", ".join(parts))


if __name__ == "__main__":
    app()
