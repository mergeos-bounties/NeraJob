from typing import Dict, List, Any

def match_resume_to_jobs(resume_data: Dict[str, Any], jobs_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Match a resume against job listings.

    Args:
        resume_data: Dictionary containing resume information
        jobs_data: List of dictionaries containing job listings

    Returns:
        List of dictionaries containing match results for each job
    """
    matches = []

    for job in jobs_data:
        match_score = calculate_match_score(resume_data, job)
        matches.append({
            "job_id": job.get("id"),
            "job_title": job.get("title"),
            "match_score": match_score,
            "reasons": generate_match_reasons(resume_data, job)
        })

    return matches

def calculate_match_score(resume_data: Dict[str, Any], job_data: Dict[str, Any]) -> float:
    """
    Calculate a match score between a resume and a job listing.

    Args:
        resume_data: Dictionary containing resume information
        job_data: Dictionary containing job listing information

    Returns:
        Match score between 0 and 1
    """
    # Implement your matching algorithm here
    # This is a placeholder implementation
    score = 0.0

    # Example: Check for skill matches
    resume_skills = set(resume_data.get("skills", []))
    job_skills = set(job_data.get("required_skills", []))

    if job_skills:
        common_skills = resume_skills.intersection(job_skills)
        score = len(common_skills) / len(job_skills)

    return min(max(score, 0.0), 1.0)

def generate_match_reasons(resume_data: Dict[str, Any], job_data: Dict[str, Any]) -> List[str]:
    """
    Generate reasons for the match score.

    Args:
        resume_data: Dictionary containing resume information
        job_data: Dictionary containing job listing information

    Returns:
        List of strings explaining the match
    """
    reasons = []

    # Example: Add skill match reasons
    resume_skills = set(resume_data.get("skills", []))
    job_skills = set(job_data.get("required_skills", []))

    if job_skills:
        common_skills = resume_skills.intersection(job_skills)
        if common_skills:
            reasons.append(f"Skills match: {', '.join(common_skills)}")

    return reasons