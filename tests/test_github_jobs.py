"""Tests for GitHub Jobs scraper."""
import sys
from pathlib import Path
from unittest.mock import Mock, patch

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from nerajob.scrapers.github_jobs import GitHubJobsScraper


def test_github_jobs_offline_mode():
    """Test offline mode returns sample data."""
    import os
    os.environ["NERAJOB_GITHUB_OFFLINE"] = "1"
    
    try:
        scraper = GitHubJobsScraper()
        results = scraper.search("python", limit=5)
        
        assert len(results) > 0
        assert any("Python" in r.title for r in results)
        assert all(r.source == "github_jobs" for r in results)
    finally:
        del os.environ["NERAJOB_GITHUB_OFFLINE"]


def test_github_jobs_offline_filtering():
    """Test offline mode filters by query."""
    import os
    os.environ["NERAJOB_GITHUB_OFFLINE"] = "1"
    
    try:
        scraper = GitHubJobsScraper()
        results = scraper.search("devops", limit=5)
        
        assert len(results) > 0
        assert any("DevOps" in r.title for r in results)
    finally:
        del os.environ["NERAJOB_GITHUB_OFFLINE"]


def test_github_jobs_offline_limit():
    """Test offline mode respects limit."""
    import os
    os.environ["NERAJOB_GITHUB_OFFLINE"] = "1"
    
    try:
        scraper = GitHubJobsScraper()
        results = scraper.search("engineer", limit=2)
        
        assert len(results) <= 2
    finally:
        del os.environ["NERAJOB_GITHUB_OFFLINE"]


def test_github_jobs_online_success():
    """Test online mode with mocked HTTP response."""
    import os
    if "NERAJOB_GITHUB_OFFLINE" in os.environ:
        del os.environ["NERAJOB_GITHUB_OFFLINE"]
    
    mock_response = Mock()
    mock_response.raise_for_status = Mock()
    mock_response.json.return_value = [
        {
            "id": "12345",
            "title": "Python Developer",
            "company": "Test Corp",
            "location": "Remote",
            "description": "Test job",
            "type": "Full-time",
            "url": "https://example.com/job/12345",
            "salary": "$100k",
        }
    ]
    
    with patch("nerajob.scrapers.github_jobs.httpx.get", return_value=mock_response):
        scraper = GitHubJobsScraper()
        results = scraper.search("python", limit=5)
        
        assert len(results) == 1
        assert results[0].title == "Python Developer"
        assert results[0].company == "Test Corp"
        assert results[0].source == "github_jobs"


def test_github_jobs_online_failure():
    """Test online mode falls back to offline on error."""
    import os
    if "NERAJOB_GITHUB_OFFLINE" in os.environ:
        del os.environ["NERAJOB_GITHUB_OFFLINE"]
    
    with patch("nerajob.scrapers.github_jobs.httpx.get", side_effect=Exception("Network error")):
        scraper = GitHubJobsScraper()
        results = scraper.search("python", limit=5)
        
        # Should fall back to offline
        assert len(results) > 0
        assert any("Python" in r.title for r in results)


def test_github_jobs_job_posting_fields():
    """Test JobPosting fields are correctly populated."""
    import os
    os.environ["NERAJOB_GITHUB_OFFLINE"] = "1"
    
    try:
        scraper = GitHubJobsScraper()
        results = scraper.search("python", limit=1)
        
        assert len(results) == 1
        job = results[0]
        
        assert job.id.startswith("github_offline_")
        assert job.source == "github_jobs"
        assert job.title
        assert job.company
        assert job.location
        assert job.tags
        assert job.url
    finally:
        del os.environ["NERAJOB_GITHUB_OFFLINE"]


if __name__ == "__main__":
    test_github_jobs_offline_mode()
    test_github_jobs_offline_filtering()
    test_github_jobs_offline_limit()
    test_github_jobs_online_success()
    test_github_jobs_online_failure()
    test_github_jobs_job_posting_fields()
    print("✅ All GitHub Jobs scraper tests passed!")
