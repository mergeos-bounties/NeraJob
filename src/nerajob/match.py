"""Score how well a job posting matches a local profile."""

from __future__ import annotations

from dataclasses import dataclass

from nerajob.models import JobPosting, Profile


@dataclass(frozen=True)
class MatchWeights:
    """Score contribution caps for skills, title, and location matching."""

    skills: float = 70.0
    title: float = 20.0
    location: float = 12.0

    def __post_init__(self) -> None:
        for name, value in self.as_dict().items():
            if value < 0:
                raise ValueError(f"{name} weight must be non-negative")

    def as_dict(self) -> dict[str, float]:
        return {
            "skills": float(self.skills),
            "title": float(self.title),
            "location": float(self.location),
        }


DEFAULT_MATCH_WEIGHTS = MatchWeights()

# Common skill aliases for resume ↔ job matching (offline-friendly).
SKILL_ALIASES: dict[str, set[str]] = {
    "python": {"python", "django", "fastapi", "flask"},
    "javascript": {"javascript", "js", "typescript", "node", "react"},
    "devops": {"devops", "docker", "kubernetes", "k8s", "ci/cd", "terraform", "helm", "ansible", "puppet", "chef", "prometheus", "grafana", "sre", "docker swarm", "nomad", "consul", "vault", "istio", "service mesh", "infrastructure as code", "iac"},
    "security_ops": {"secops", "soc analyst", "incident response", "threat hunting", "siem", "edr", "blue team", "detection"},
    "sales_eng": {"solutions engineer", "sales engineer", "pre-sales", "demo", "poc", "technical account", "se ", "rfp"},
    "customer_success": {"customer success", "csm", "account management", "onboarding", "retention", "support", "helpdesk", "zendesk"},
    "qa_test": {"qa", "quality assurance", "selenium", "cypress", "playwright", "test automation", "sdet", "pytest"},
    "ml_ai": {"machine learning", "ml", "deep learning", "nlp", "computer vision", "pytorch", "tensorflow"},
    "ml": {"ml", "machine learning", "pytorch", "tensorflow"},
    "rust": {"rust", "cargo", "tokio", "actix", "axum"},
    "go": {"go", "golang", "gin", "fiber"},
    "sql": {"sql", "postgres", "postgresql", "mysql", "sqlite", "database"},
    "cloud": {"cloud", "aws", "gcp", "azure", "s3", "lambda", "azure-devops", "gke", "eks", "ecs", "cloudformation", "serverless", "cdn", "vpc", "cloudwatch", "cloud functions", "azure functions", "google cloud", "google cloud platform", "aws lambda", "azure devops", "pulumi", "crossplane"},
    "java": {"java", "spring", "kotlin", "jvm", "maven", "gradle"},
    "mobile": {"mobile", "android", "ios", "flutter", "react native", "swift", "kotlin", "xamarin", "maui", "capacitor", "cordova", "jetpack compose", "ndk", "coreml", "arkit", "arcore", "xcode", "android studio", "mobile dev", "mobile development", "native app", "hybrid app", "pwa", "progressive web app", "app store optimization", "aso"},
    "security": {"security", "infosec", "appsec", "owasp", "penetration testing", "pentest"},
    "data": {"data", "analytics", "etl", "spark", "airflow", "dbt", "pandas"},
    "web3": {"web3", "blockchain", "solidity", "ethereum", "solana", "smart contract", "defi"},
    "design": {"design", "figma", "ui", "ux", "product design", "wireframe"},
    "testing": {"testing", "qa", "selenium", "playwright", "cypress", "pytest", "junit"},
    "embedded": {"embedded", "firmware", "rtos", "arduino", "esp32", "stm32", "c++"},
    "product": {"product", "pm", "product manager", "roadmap", "agile", "scrum"},
    "writing": {"writing", "technical writing", "docs", "copywriting", "content"},
    "ops": {"ops", "operations", "logistics", "supply chain", "sre", "platform"},
    "ux_design": {"ux", "ui", "figma", "wireframe", "prototype", "user research", "product design"},
    "data_engineering": {"data engineering", "etl", "spark", "airflow", "dbt", "warehouse", "pipeline"},
    "cybersecurity": {"cybersecurity", "security", "soc", "siem", "pentest", "iam", "infosec"},
    "hardware": {"hardware", "pcb", "fpga", "asic", "electronics", "schematic"},
    "healthcare": {"healthcare", "nursing", "clinical", "medical", "emr", "healthtech"},
    "education": {
        "education",
        "teaching",
        "curriculum",
        "edtech",
        "lms",
        "learning management system",
        "assessment",
        "tutor",
        "tutoring",
        "instructor",
        "instructional design",
        "e-learning",
    },
    "legal": {"legal", "counsel", "compliance", "contracts", "gdpr", "privacy"},
    "marketing": {"marketing", "growth", "seo", "sem", "content marketing", "demand gen"},
    "hr": {"hr", "human resources", "recruiting", "talent", "people ops", "ats"},
    "game": {"game", "gamedev", "unity", "unreal", "godot", "game design"},
    "support": {"support", "customer support", "helpdesk", "zendesk", "intercom", "cs"},
    "sales": {"sales", "account executive", "sdr", "bdr", "crm", "salesforce"},
    "finance": {"finance", "accounting", "fintech", "cpa", "bookkeeping", "fp&a", "payments", "payment processing", "ledger", "kyc", "know your customer", "aml", "anti money laundering", "risk management", "quant", "quantitative analysis", "trading", "algorithmic trading", "blockchain finance", "defi", "banking api", "payment gateway", "stripe", "paypal", "square", "plaid", "wealth management", "robo advisor", "insurance tech", "insurtech", "regtech", "compliance tech", "financial modeling", "valuation", "portfolio management", "asset management", "cryptocurrency trading", "forex", "fx trading"},
}


def _coerce_weights(weights: MatchWeights | dict[str, float] | None) -> MatchWeights:
    if weights is None:
        return DEFAULT_MATCH_WEIGHTS
    if isinstance(weights, MatchWeights):
        return weights
    return MatchWeights(**weights)


def expand_skills(skills: set[str] | list[str] | tuple[str, ...]) -> set[str]:
    out = {str(s).lower().strip() for s in skills if str(s).strip()}
    for s in list(out):
        for key, aliases in SKILL_ALIASES.items():
            if s == key or s in aliases:
                out |= aliases | {key}
    return out


def match_score(
    profile: Profile,
    job: JobPosting,
    weights: MatchWeights | dict[str, float] | None = None,
) -> dict:
    """
    Lightweight keyword match: skills vs title/description/tags + location soft score.
    Returns 0–100 score with explainable hits.
    """
    score_weights = _coerce_weights(weights)
    base_skills = [s.strip().lower() for s in (profile.skills or []) if s.strip()]
    hay = f"{job.title} {job.description} {' '.join(job.tags)} {job.company}".lower()
    hits: list[str] = []
    for s in base_skills:
        aliases = expand_skills({s})
        if any(a and a in hay for a in aliases):
            hits.append(s)
    skill_score = (
        (len(hits) / max(1, len(base_skills))) * score_weights.skills
        if base_skills
        else score_weights.skills * 0.5
    )

    # headline / target role token overlap with job title
    headline_tokens = {
        t for t in (profile.headline or "").lower().replace("/", " ").split() if len(t) > 2
    }
    title_tokens = {t for t in job.title.lower().replace("/", " ").split() if len(t) > 2}
    role_overlap = headline_tokens & title_tokens
    role_score = min(score_weights.title, len(role_overlap) * (score_weights.title * 0.35))

    loc_score = 0.0
    pl = (profile.location or "").lower()
    jl = (job.location or "").lower()
    prefers_remote = any(
        tok in pl for tok in ("remote", "wfh", "anywhere", "worldwide")
    ) or getattr(profile, "remote_ok", False)
    partial_location_weight = score_weights.location * (10.0 / 12.0)
    if job.remote or "remote" in jl:
        loc_score = score_weights.location if prefers_remote else partial_location_weight
    elif pl and any(part in jl for part in pl.split() if len(part) > 2):
        loc_score = partial_location_weight

    total = min(100.0, skill_score + role_score + loc_score)
    return {
        "job_id": job.id,
        "title": job.title,
        "company": job.company,
        "score": round(total, 1),
        "skill_hits": hits,
        "role_overlap": sorted(role_overlap),
        "remote": job.remote,
        "location_boost": loc_score,
        "score_weights": score_weights.as_dict(),
        "band": "strong" if total >= 70 else "medium" if total >= 40 else "weak",
    }


def rank_jobs(
    profile: Profile,
    jobs: list[JobPosting],
    top_k: int = 20,
    weights: MatchWeights | dict[str, float] | None = None,
) -> list[dict]:
    ranked = [match_score(profile, j, weights=weights) for j in jobs]
    ranked.sort(key=lambda r: r["score"], reverse=True)
    return ranked[: max(1, top_k)]
