import json
from rapidfuzz import fuzz

def load_resume():
    with open("data/base_resume.json") as f:
        return json.load(f)

def score_job(job, resume):
    score = 0

    skills_text = " ".join(resume.get("skills", [])).lower()
    job_desc = job.get("description", "").lower()

    score += fuzz.partial_ratio(skills_text, job_desc)

    score += fuzz.partial_ratio(
        resume.get("title", "").lower(),
        job.get("title", "").lower()
    )

    return score / 2

def rank_jobs(jobs):
    resume = load_resume()

    scored = []
    for job in jobs:
        s = score_job(job, resume)
        job["score"] = round(s, 2)
        scored.append(job)

    return sorted(scored, key=lambda x: x["score"], reverse=True)