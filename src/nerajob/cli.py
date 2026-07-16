from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from nerajob import __version__
from nerajob.apply.assistant import prepare_application
from nerajob.cv.builder import write_cv_files
from nerajob.match import DEFAULT_MATCH_WEIGHTS, MatchWeights
from nerajob.models import JobPosting
from nerajob.scrapers.registry import available_scrapers, get_scraper
from nerajob.storage import (
    default_profile,
    get_job,
    load_jobs,
    load_profile,
    save_profile,
    upsert_jobs,
)

app = typer.Typer(help="NeraJob — scan jobs, build CV, prepare applications.", no_args_is_help=True)
profile_app = typer.Typer(help="Manage your profile / CV source data.")
jobs_app = typer.Typer(help="Inspect saved jobs.")
app.add_typer(profile_app, name="profile")
app.add_typer(jobs_app, name="jobs")
console = Console()


@app.callback()
def main() -> None:
    """NeraJob CLI."""


@app.command("version")
def version_cmd() -> None:
    console.print(f"NeraJob {__version__}")


@app.command("skills")
def skills_cmd() -> None:
    """List skill alias groups used by match scoring."""
    from nerajob.match import SKILL_ALIASES

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
    remote_only: bool = typer.Option(False, "--remote-only", help="Keep only remote jobs"),
    min_score: float = typer.Option(
        0.0,
        "--min-score",
        help="If profile exists, drop jobs below this match score (0–100)",
    ),
    min_salary: int = typer.Option(
        0,
        "--min-salary",
        help="Filter jobs by minimum annual salary (e.g. 50000 for 50k)",
    ),
) -> None:
    """Scan job sources and save matches under data/jobs.json."""
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

    # Dedupe across sources (scan --all): prefer first occurrence, keep stable order
    before = len(collected)
    seen_keys: set[str] = set()
    deduped: list[JobPosting] = []
    for job in collected:
        key = f"{job.title.strip().lower()}|{job.company.strip().lower()}|{job.url.strip().lower()}"
        if key in seen_keys:
            continue
        seen_keys.add(key)
        deduped.append(job)
    collected = deduped
    if all_sources and before != len(collected):
        console.print(f"[dim]Deduped[/dim] {before} → {len(collected)} unique jobs")

    if remote_only:
        collected = [
            j
            for j in collected
            if j.remote or "remote" in (j.location or "").lower()
        ]
        console.print(f"[dim]remote-only[/dim] {len(collected)} jobs")

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
def jobs_list(limit: int = typer.Option(30, min=1, max=200)) -> None:
    jobs = load_jobs()[:limit]
    if not jobs:
        console.print("[yellow]No jobs yet. Run: nerajob scan -q python[/yellow]")
        raise typer.Exit()
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
) -> None:
    """Build Markdown + text CV from your profile."""
    profile = load_profile()
    if not profile:
        console.print("[red]No profile. Run: nerajob profile init[/red]")
        raise typer.Exit(code=1)
    paths = write_cv_files(profile, target_role=target)
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
    from nerajob.storage import load_jobs, load_profile

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


if __name__ == "__main__":
    app()
