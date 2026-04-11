def filter_jobs(jobs):
    include_keywords = ["python", "ai", "machine learning", "backend"]
    exclude_keywords = ["sales", "account executive", "marketing", "recruiter"]

    filtered = []

    for job in jobs:
        text = (job["title"] + job["description"]).lower()

        if any(k in text for k in include_keywords) and not any(e in text for e in exclude_keywords):
            filtered.append(job)

    return filtered