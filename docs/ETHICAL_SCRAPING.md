# Ethical Scraping Checklist

## Legal Compliance

- [ ] Check robots.txt before scraping
- [ ] Review Terms of Service
- [ ] Respect rate limits (max 1 req/sec recommended)
- [ ] Identify your bot with User-Agent

## Technical Best Practices

1. **Rate Limiting**
   - Add delays between requests (1-2 seconds minimum)
   - Implement exponential backoff on errors
   - Respect Retry-After headers

2. **Identification**
   - Use descriptive User-Agent string
   - Include contact email in headers
   - Register with site admin if required

3. **Data Handling**
   - Cache responses locally
   - Don't scrape personal data without consent
   - Delete data when no longer needed

## Common Sites

| Site | robots.txt | Rate Limit | Notes |
|------|------------|------------|-------|
| Indeed | /robots.txt | 1 req/3s | No login required |
| LinkedIn | Blocked | N/A | Use API instead |
| Glassdoor | /robots.txt | 1 req/5s | Public pages only |

## Red Flags

- Sites that block all bots
- Login-required content
- CAPTCHA-protected pages
- Sites with explicit no-scrape policies
