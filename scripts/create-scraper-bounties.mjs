import { execSync } from 'node:child_process';
import { mkdtempSync, writeFileSync, rmSync } from 'node:fs';
import { join } from 'node:path';
import { tmpdir } from 'node:os';

const REPO = 'mergeos-bounties/NeraJob';

function sh(cmd) {
  return execSync(cmd, { encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'] }).trim();
}

function ensureLabel(name, color, description) {
  try {
    sh(
      `gh label create ${JSON.stringify(name)} --repo ${REPO} --color ${color} --description ${JSON.stringify(description)}`,
    );
  } catch {
    try {
      sh(
        `gh label edit ${JSON.stringify(name)} --repo ${REPO} --color ${color} --description ${JSON.stringify(description)}`,
      );
    } catch {
      // ignore
    }
  }
}

function createIssue(title, body, labels) {
  const dir = mkdtempSync(join(tmpdir(), 'nerajob-issue-'));
  const file = join(dir, 'body.md');
  try {
    writeFileSync(file, body, 'utf8');
    const labelFlags = labels.map((l) => `--label ${JSON.stringify(l)}`).join(' ');
    const out = sh(
      `gh issue create --repo ${REPO} --title ${JSON.stringify(title)} --body-file ${JSON.stringify(file)} ${labelFlags}`,
    );
    console.log(out);
    return out;
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
}

const labels = [
  ['bounty', '5319E7', 'Eligible for MergeOS MRG bounty'],
  ['bounty: feature', 'A2EEEF', 'Feature bounty'],
  ['bounty: bug', 'D73A4A', 'Bug bounty'],
  ['scraper', '0E8A16', 'Job board / scraper adapter work'],
  ['reward:25-mrg', 'FEF2C0', 'Target 25 MRG'],
  ['reward:50-mrg', 'FEF2C0', 'Target 50 MRG'],
  ['reward:100-mrg', 'FEF2C0', 'Target 100 MRG'],
  ['good first issue', '7057FF', 'Good for newcomers'],
  ['api', '1D76DB', 'Official or public API integration'],
];

for (const [name, color, description] of labels) {
  ensureLabel(name, color, description);
}

const footer = `

## Claim (MergeOS MRG)

1. Star https://github.com/mergeos-bounties/NeraJob and https://github.com/mergeos-bounties/mergeos  
2. Comment on **this issue**: \`I claim this bounty\`  
3. Comment on MergeOS [Claim Token #1](https://github.com/mergeos-bounties/mergeos/issues/1) with a link to this issue  
4. Open a PR to **NeraJob** with \`Fixes #<this-issue>\`

Policy: [docs/BOUNTY.md](../blob/master/docs/BOUNTY.md)

## Acceptance

- [ ] New scraper implements \`BaseScraper.search(query, location, limit)\`
- [ ] Registered in \`src/nerajob/scrapers/registry.py\`
- [ ] Prefer official/public API; document rate limits + ToS notes in PR
- [ ] Tests with **mocked** HTTP (CI must not depend on live network)
- [ ] \`nerajob scan --source <name> -q python -n 5\` works when live (or degrades gracefully)
- [ ] No secrets committed

## Payout

Maintainer reviews PR → merge on NeraJob → **MRG credit** on MergeOS ledger to \`github:<author>\` (25/50/100/200 scale).
`;

const issues = [
  {
    title: '[25 MRG] Scraper: Remotive public API job feed',
    labels: ['bounty', 'bounty: feature', 'scraper', 'reward:25-mrg', 'api', 'good first issue'],
    reward: 25,
    body: `## Bounty: 25 MRG

Add a **Remotive** job scraper using their public jobs API (or documented public JSON feed).

## Why

Expand global remote coverage beyond RemoteOK/sample.

## Hints

- Module: \`src/nerajob/scrapers/remotive.py\`
- Map fields into \`JobPosting\`
- Graceful empty list on network/API failure
${footer}`,
  },
  {
    title: '[25 MRG] Scraper: Arbeitnow public API job feed',
    labels: ['bounty', 'bounty: feature', 'scraper', 'reward:25-mrg', 'api', 'good first issue'],
    reward: 25,
    body: `## Bounty: 25 MRG

Integrate **Arbeitnow** public jobs API as a NeraJob scraper source.

## Hints

- \`src/nerajob/scrapers/arbeitnow.py\`
- Support query/limit filters as well as possible
- Mocked unit tests required
${footer}`,
  },
  {
    title: '[25 MRG] Scraper: Jobicy remote jobs API',
    labels: ['bounty', 'bounty: feature', 'scraper', 'reward:25-mrg', 'api', 'good first issue'],
    reward: 25,
    body: `## Bounty: 25 MRG

Add **Jobicy** public remote jobs API adapter.

## Hints

- Register as \`jobicy\`
- Normalize tags/location/remote flag into \`JobPosting\`
${footer}`,
  },
  {
    title: '[25 MRG] Scraper: Himalayas.app public remote jobs API',
    labels: ['bounty', 'bounty: feature', 'scraper', 'reward:25-mrg', 'api', 'good first issue'],
    reward: 25,
    body: `## Bounty: 25 MRG

Add **Himalayas** remote jobs public API scraper.

## Hints

- Source name: \`himalayas\`
- Handle pagination if API supports it (keep limit respected)
${footer}`,
  },
  {
    title: '[25 MRG] Scraper: Findwork.dev API adapter',
    labels: ['bounty', 'bounty: feature', 'scraper', 'reward:25-mrg', 'api', 'good first issue'],
    reward: 25,
    body: `## Bounty: 25 MRG

Integrate **Findwork.dev** jobs API (document whether free key is required via env).

## Hints

- Env: \`FINDWORK_API_KEY\` if needed; skip live calls in tests
- Never commit keys
${footer}`,
  },
  {
    title: '[50 MRG] Scraper: Adzuna Jobs API (multi-country)',
    labels: ['bounty', 'bounty: feature', 'scraper', 'reward:50-mrg', 'api'],
    reward: 50,
    body: `## Bounty: 50 MRG

Add **Adzuna** Jobs API scraper with country selection (\`us\`, \`gb\`, \`de\`, \`au\`, \`in\`, etc.).

## Requirements

- Env: \`ADZUNA_APP_ID\`, \`ADZUNA_APP_KEY\`
- CLI: optional \`--country\` flag or config for Adzuna source
- Tests mock HTTP responses for at least 2 countries
- Document free developer signup in PR
${footer}`,
  },
  {
    title: '[50 MRG] Scraper: USAJOBS official API',
    labels: ['bounty', 'bounty: feature', 'scraper', 'reward:50-mrg', 'api'],
    reward: 50,
    body: `## Bounty: 50 MRG

Integrate **USAJOBS** official API for US federal/public listings.

## Requirements

- Env for API key/user agent as required by USAJOBS docs
- Map title, organization, locations, URL
- Mocked tests; graceful failure without credentials
${footer}`,
  },
  {
    title: '[50 MRG] Scraper: Reed.co.uk Jobs API',
    labels: ['bounty', 'bounty: feature', 'scraper', 'reward:50-mrg', 'api'],
    reward: 50,
    body: `## Bounty: 50 MRG

Add **Reed.co.uk** jobs API adapter (UK market coverage).

## Requirements

- Env: Reed API key
- Query + location filters
- Mocked tests
${footer}`,
  },
  {
    title: '[50 MRG] Scraper: The Muse jobs API',
    labels: ['bounty', 'bounty: feature', 'scraper', 'reward:50-mrg', 'api'],
    reward: 50,
    body: `## Bounty: 50 MRG

Integrate **The Muse** public jobs API.

## Requirements

- Pagination + limit
- Company + locations + categories → tags
- Mocked tests
${footer}`,
  },
  {
    title: '[50 MRG] Scraper: Greenhouse public board JSON boards',
    labels: ['bounty', 'bounty: feature', 'scraper', 'reward:50-mrg', 'api'],
    reward: 50,
    body: `## Bounty: 50 MRG

Add a **Greenhouse** public board adapter.

Many companies expose \`https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs\`.

## Requirements

- Accept one or more board tokens via config file or CLI (\`--board\`)
- Ship with 1–2 well-known example board tokens documented as optional demos
- Tests with mocked board payloads
${footer}`,
  },
  {
    title: '[50 MRG] Scraper: Lever public postings API',
    labels: ['bounty', 'bounty: feature', 'scraper', 'reward:50-mrg', 'api'],
    reward: 50,
    body: `## Bounty: 50 MRG

Add **Lever** public postings adapter (\`https://api.lever.co/v0/postings/{company}\`).

## Requirements

- CLI/config list of company site names
- Map text description + categories/tags
- Mocked tests
${footer}`,
  },
  {
    title: '[50 MRG] Scraper: Ashby public job board API',
    labels: ['bounty', 'bounty: feature', 'scraper', 'reward:50-mrg', 'api'],
    reward: 50,
    body: `## Bounty: 50 MRG

Integrate **Ashby** public job board endpoints for companies that publish public boards.

## Requirements

- Configurable board/org identifier
- Mocked tests
- Document compliance notes
${footer}`,
  },
  {
    title: '[50 MRG] Scraper: SmartRecruiters public postings',
    labels: ['bounty', 'bounty: feature', 'scraper', 'reward:50-mrg', 'api'],
    reward: 50,
    body: `## Bounty: 50 MRG

Add **SmartRecruiters** public postings API adapter for participating companies.

## Requirements

- Company identifier config
- Mocked tests + graceful empty results
${footer}`,
  },
  {
    title: '[50 MRG] Scraper: Jooble API multi-region search',
    labels: ['bounty', 'bounty: feature', 'scraper', 'reward:50-mrg', 'api'],
    reward: 50,
    body: `## Bounty: 50 MRG

Integrate **Jooble** job search API for broader international coverage.

## Requirements

- Env API key
- Region/country parameter
- Mocked tests
${footer}`,
  },
  {
    title: '[50 MRG] Scraper: Arbeitnow + EU/EURES-oriented remote listings pack',
    labels: ['bounty', 'bounty: feature', 'scraper', 'reward:50-mrg', 'api'],
    reward: 50,
    body: `## Bounty: 50 MRG

Improve **EU-focused** coverage: polish Arbeitnow (if missing) and add one additional EU-friendly public source (document choice: EURES open data, or another public API).

## Requirements

- At least one new registered scraper beyond existing RemoteOK/sample
- Tests + README section for EU sources
${footer}`,
  },
  {
    title: '[50 MRG] Scraper: Vietnam tech jobs board adapter (TopCV or VietnamWorks public pages — ToS-safe)',
    labels: ['bounty', 'bounty: feature', 'scraper', 'reward:50-mrg'],
    reward: 50,
    body: `## Bounty: 50 MRG

Add a **Vietnam market** job source. Prefer official partner APIs. If only HTML is available, implement a conservative public listing parser with strict rate limiting and document ToS compliance risks.

## Requirements

- Source name e.g. \`vietnamworks\` or \`topcv\`
- Strong rate limiting + User-Agent
- Mocked HTML/API fixtures in tests
- Clear PR note on legality/ToS
${footer}`,
  },
  {
    title: '[50 MRG] Scraper framework: shared HTTP client, retries, rate limit, robots-aware policy',
    labels: ['bounty', 'bounty: feature', 'scraper', 'reward:50-mrg'],
    reward: 50,
    body: `## Bounty: 50 MRG

Add a shared \`nerajob.http\` (or similar) client used by scrapers:

- Configurable timeout + User-Agent
- Simple rate limiter (per host)
- Optional robots.txt check helper
- Retry with backoff for 429/5xx

## Requirements

- RemoteOK (and new scrapers) can migrate to shared client
- Unit tests for rate limit + retry behavior (mocked)
${footer}`,
  },
  {
    title: '[25 MRG] CLI: nerajob scan --all aggregates multi-source with dedupe by URL/title+company',
    labels: ['bounty', 'bounty: feature', 'scraper', 'reward:25-mrg', 'good first issue'],
    reward: 25,
    body: `## Bounty: 25 MRG

Improve multi-source scanning:

- \`--all\` already runs scrapers; add **dedupe** across sources (URL preferred, else title+company)
- Report counts: fetched / unique / saved

## Requirements

- Tests for dedupe helper
- Keep backward compatible CLI
${footer}`,
  },
  {
    title: '[50 MRG] Match score: rank jobs vs profile skills/tags',
    labels: ['bounty', 'bounty: feature', 'reward:50-mrg'],
    reward: 50,
    body: `## Bounty: 50 MRG

Add a simple **match score** (0–100) between \`Profile.skills\` and job title/tags/description.

## Requirements

- \`nerajob jobs list --sort match\` or score column
- Persist optional \`match_score\` on scan upsert
- Unit tests for scorer
${footer}`,
  },
  {
    title: '[50 MRG] PDF CV export from Markdown profile',
    labels: ['bounty', 'bounty: feature', 'reward:50-mrg'],
    reward: 50,
    body: `## Bounty: 50 MRG

Export CV to **PDF** (WeasyPrint, reportlab, or similar optional extra).

## Requirements

- \`nerajob cv build --format pdf\` (or \`--pdf\`)
- Optional dependency group in pyproject
- Test that PDF bytes/path are produced in CI (or skip if system libs missing with clear message)
${footer}`,
  },
  {
    title: '[100 MRG] Multi-source pack: ship 5+ live public scrapers with CI mocks',
    labels: ['bounty', 'bounty: feature', 'scraper', 'reward:100-mrg', 'api'],
    reward: 100,
    body: `## Bounty: 100 MRG

Ship a **pack** of at least **5** production-ready scrapers (beyond sample/RemoteOK), each with mocked tests and registry entries.

## Requirements

- At least 5 new sources registered
- Shared patterns for error handling
- README table of sources + auth needs
- All tests offline-mocked
${footer}`,
  },
  {
    title: '[25 MRG] Docs: SOURCES.md catalog of job boards + API links + claim table',
    labels: ['bounty', 'bounty: feature', 'reward:25-mrg', 'good first issue', 'documentation'],
    reward: 25,
    body: `## Bounty: 25 MRG

Create \`docs/SOURCES.md\` listing:

- Implemented sources
- Planned sources
- API docs links
- Auth/env requirements
- Link to open bounty issues for each planned source

## Requirements

- Keep in sync with registry
- English (optional short VI section)
${footer}`,
  },
];

// documentation label might not exist with that name - ensure it
ensureLabel('documentation', '0075CA', 'Documentation improvements');

const created = [];
for (const issue of issues) {
  created.push({ url: createIssue(issue.title, issue.body, issue.labels), title: issue.title, reward: issue.reward });
}

console.log('\nCreated', created.length, 'issues');
let total = 0;
for (const c of created) {
  total += c.reward;
  console.log(c.reward, c.title);
}
console.log('Marketing total MRG:', total);
