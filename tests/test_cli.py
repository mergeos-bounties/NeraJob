import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from nerajob.cli import main

@pytest.fixture
def sample_resume():
    return {
        "name": "John Doe",
        "skills": ["Python", "Django", "JavaScript"]
    }

@pytest.fixture
def sample_jobs():
    return [
        {
            "id": "job1",
            "title": "Python Developer",
            "required_skills": ["Python", "Django"]
        },
        {
            "id": "job2",
            "title": "JavaScript Developer",
            "required_skills": ["JavaScript", "React"]
        }
    ]

def test_match_command_with_files(sample_resume, sample_jobs):
    runner = CliRunner()

    with tempfile.NamedTemporaryFile(mode="w+", suffix=".json") as resume_file, \
         tempfile.NamedTemporaryFile(mode="w+", suffix=".json") as jobs_file:

        json.dump(sample_resume, resume_file)
        json.dump(sample_jobs, jobs_file)
        resume_file.flush()
        jobs_file.flush()

        result = runner.invoke(
            main,
            ["match", "--resume-file", resume_file.name, "--jobs-file", jobs_file.name]
        )

        assert result.exit_code == 0
        assert "Python Developer" in result.output
        assert "JavaScript Developer" in result.output

def test_match_command_with_output_file(sample_resume, sample_jobs):
    runner = CliRunner()

    with tempfile.NamedTemporaryFile(mode="w+", suffix=".json") as resume_file, \
         tempfile.NamedTemporaryFile(mode="w+", suffix=".json") as jobs_file, \
         tempfile.NamedTemporaryFile(mode="w+", suffix=".json") as output_file:

        json.dump(sample_resume, resume_file)
        json.dump(sample_jobs, jobs_file)
        resume_file.flush()
        jobs_file.flush()

        result = runner.invoke(
            main,
            [
                "match",
                "--resume-file", resume_file.name,
                "--jobs-file", jobs_file.name,
                "--output", output_file.name
            ]
        )

        assert result.exit_code == 0
        assert f"Match results saved to {output_file.name}" in result.output

        # Verify the output file was created
        output_file.seek(0)
        output_data = json.load(output_file)
        assert len(output_data) == 2

def test_match_command_missing_file():
    runner = CliRunner()
    result = runner.invoke(
        main,
        ["match", "--resume-file", "nonexistent.json", "--jobs-file", "jobs.json"]
    )
    assert result.exit_code != 0
    assert "Error: File not found" in result.output