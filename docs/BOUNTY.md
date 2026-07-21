# Lever Scraper Documentation

## Rate Limits
Lever's public API has rate limits. The scraper should:
1. Implement exponential backoff for rate-limited requests
2. Cache responses to minimize API calls
3. Document any observed rate limits in the code

## Terms of Service
- Do not scrape Lever's API more than necessary
- Respect the `hostedUrl` links and don't overload their servers
- Comply with Lever's ToS for public API usage

## Configuration
Add the company name to the configuration file under the `lever` section: