# Add to existing integration tests
def test_himalayas_scraper_integration(self):
    """Test Himalayas scraper integration."""
    scraper = HimalayasScraper()
    jobs = scraper.search("python", limit=2)

    # Basic validation
    self.assertTrue(len(jobs) <= 2)
    if jobs:
        self.assertIn("title", jobs[0])
        self.assertIn("company", jobs[0])
        self.assertIn("location", jobs[0])
        self.assertIn("url", jobs[0])
        self.assertIn("description", jobs[0])
        self.assertEqual(jobs[0]["source"], "himalayas")