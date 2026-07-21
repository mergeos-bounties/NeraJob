import argparse
import json
from pathlib import Path
from typing import List, Optional

from nerajob.matcher import match_resume_to_jobs

def add_match_command(subparsers: argparse._SubParsersAction) -> None:
    """Add the 'match' command to the CLI."""
    parser = subparsers.add_parser(
        "match",
        help="Match resumes against job listings using offline files",
    )
    parser.add_argument(
        "--resume-file",
        type=Path,
        required=True,
        help="Path to the JSON file containing resume data",
    )
    parser.add_argument(
        "--jobs-file",
        type=Path,
        required=True,
        help="Path to the JSON file containing job listings",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Path to save the match results (default: print to console)",
    )
    parser.set_defaults(func=handle_match_command)

def handle_match_command(args: argparse.Namespace) -> None:
    """Handle the 'match' command."""
    try:
        with open(args.resume_file, "r") as f:
            resume_data = json.load(f)

        with open(args.jobs_file, "r") as f:
            jobs_data = json.load(f)

        matches = match_resume_to_jobs(resume_data, jobs_data)

        if args.output:
            with open(args.output, "w") as f:
                json.dump(matches, f, indent=2)
            print(f"Match results saved to {args.output}")
        else:
            print(json.dumps(matches, indent=2))

    except FileNotFoundError as e:
        print(f"Error: File not found - {e.filename}")
    except json.JSONDecodeError:
        print("Error: Invalid JSON format in input files")
    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")

def main() -> None:
    parser = argparse.ArgumentParser(description="NeraJob CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Add existing commands
    # ... (existing command setup code)

    # Add the new match command
    add_match_command(subparsers)

    args = parser.parse_args()
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()