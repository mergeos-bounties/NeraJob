# Skill Aliases Contributor Guide

NeraJob uses `SKILL_ALIASES` in `src/nerajob/match.py` to expand profile skills
before ranking jobs. A profile that says `k8s`, for example, should still match
jobs that mention `kubernetes`.

Use this guide when adding a new skill domain or extending an existing alias
group.

## When to add a domain

Add a new `SKILL_ALIASES` key when a group of terms represents the same hiring
signal and improves matching quality. Good examples are:

- common abbreviations, such as `k8s` for `kubernetes`
- framework names that imply a language or skill area
- job-market synonyms, such as `customer success` and `csm`

Avoid adding aliases that are too broad. Terms such as `engineer`, `developer`,
or `manager` match too many jobs and reduce ranking quality.

## Alias map rules

Use a stable lowercase key:

```python
"data_engineering": {"data engineering", "etl", "spark", "airflow", "dbt"}
```

Keep each alias set focused:

- include the canonical phrase and common short forms
- use lowercase strings only
- prefer 4-8 high-signal aliases over long keyword dumps
- include punctuation only when it is part of a common search term, such as
  `ci/cd`
- avoid duplicates across unrelated domains unless the overlap is intentional

If a new domain overlaps an existing one, add a short note in the PR explaining
why the overlap is useful for matching.

## Test pattern

Add or extend tests in `tests/test_skill_aliases.py`.

Each test should call `expand_skills()` with one canonical term or one synonym,
then assert that the expanded set includes the domain key and at least one
high-value alias:

```python
def test_expand_skills_data_engineering():
    out = expand_skills({"airflow"})
    assert "data_engineering" in out
    assert "spark" in out
```

For broad domains, prefer several small tests over one large assertion block.
This keeps failures easy to read.

## Local verification

Run the focused alias tests first:

```powershell
pytest tests/test_skill_aliases.py -q
```

Then run the normal project checks:

```powershell
pytest -q
ruff check src tests
```

CI must stay offline-friendly. Do not add live network calls for alias tests.

## PR checklist

- Update `SKILL_ALIASES` in `src/nerajob/match.py`
- Add or update focused tests in `tests/test_skill_aliases.py`
- Keep aliases lowercase and specific
- Mention any intentional overlap with existing domains in the PR body
