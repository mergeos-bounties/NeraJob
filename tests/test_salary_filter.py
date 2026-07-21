"""Tests for salary filter."""

import json
from click.testing import CliRunner
from nerajob.cli import cli

def test_scan_with_salary_filter(tmp_path):
    """Test scan with min-salary filter."""
    jobs = [
        {"title": "Junior Dev", "salary": "$60k-$80k"},
        {"title": "Senior Dev", "salary": "$120k-$150k"}
    ]
    jobs_file = tmp_path / 'jobs.json'
    jobs_file.write_text(json.dumps(jobs))
    
    runner = CliRunner()
    result = runner.invoke(cli, ['scan', '--min-salary', '100', '--input', str(jobs_file)])
    assert result.exit_code == 0
    assert 'Senior Dev' in result.output
    assert 'Junior Dev' not in result.output
