# Cybersecurity Skill Aliases

## Purpose

This document defines the cybersecurity domain skill aliases used in NeraJob's matching algorithm.

## Skill Aliases

The following aliases are mapped under the `cybersecurity` key:

```python
"cybersecurity": {"cybersecurity", "security", "soc", "siem", "pentest", "iam", "infosec"}
```

## Alias Breakdown

| Alias | Description |
|-------|-------------|
| `cybersecurity` | Primary domain keyword |
| `security` | General security term |
| `soc` | Security Operations Center |
| `siem` | Security Information and Event Management |
| `pentest` | Penetration Testing |
| `iam` | Identity and Access Management |
| `infosec` | Information Security |

## Usage

When a candidate lists any of these skills on their profile, the matching algorithm will:
1. Expand the skill to include all aliases in the cybersecurity set
2. Match against job postings that mention any of these terms
3. Boost the candidate's score for cybersecurity-related positions

## Example

A candidate with `siem` on their profile will also match jobs requiring:
- cybersecurity
- security
- soc
- pentest
- iam
- infosec

## Testing

Tests are located in `tests/test_skill_aliases.py`:

```python
def test_expand_skills_cybersecurity():
    out = expand_skills({"siem"})
    assert "cybersecurity" in out
    assert "soc" in out
    assert "pentest" in out
    assert "iam" in out
```

## Contributing

To extend this domain:
1. Add new aliases to the `cybersecurity` set in `src/nerajob/match.py`
2. Add corresponding tests in `tests/test_skill_aliases.py`
3. Update this documentation
4. Submit a PR with the label `bounty`

## Related Issues

- Issue #50: [25 MRG] Skill aliases: cybersecurity domain (SKILL_ALIASES)
