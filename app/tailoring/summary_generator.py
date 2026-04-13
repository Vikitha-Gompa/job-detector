import json
import re
import ollama
from bs4 import BeautifulSoup


def clean_html(html):
    if not html:
        return ""
    return BeautifulSoup(html, "html.parser").get_text(" ", strip=True)


def load_resume():
    with open("data/base_resume.json", encoding="utf-8") as f:
        return json.load(f)


def extract_keywords(text, limit=12):
    words = re.findall(r"\b[A-Za-z][A-Za-z0-9+\-]{2,}\b", text.lower())
    stop = {
        "with", "that", "this", "have", "from", "your", "will", "the", "and", "for",
        "are", "was", "were", "you", "our", "job", "role", "work", "team", "years",
        "experience", "using", "into", "must", "may", "can", "able", "required",
        "description", "responsibilities", "qualifications"
    }

    out = []
    for w in words:
        if w not in stop and w not in out:
            out.append(w)
    return out[:limit]


def post_clean_summary(summary):
    if not summary:
        return ""

    summary = " ".join(summary.strip().split())

    bad_phrases = [
        "here is a recruiter-friendly resume summary for a software engineer",
        "here is a recruiter-friendly resume summary",
        "recruiter-friendly resume summary",
        "resume summary",
        "recruiter-friendly",
        "recruiter friendly",
        "job description",
        "here is",
        "summary:"
    ]

    for phrase in bad_phrases:
        summary = re.sub(re.escape(phrase), "", summary, flags=re.IGNORECASE)

    summary = re.sub(r"^(here is|this is|below is)\s+", "", summary, flags=re.IGNORECASE)
    summary = re.sub(r"\s+", " ", summary).strip(" -:;,.")
    return summary[:220]


def fallback_summary():
    return (
        "Software Engineer with experience in Python, AI, backend systems, and cloud infrastructure. "
        "Skilled in building scalable applications, APIs, and machine learning solutions."
    )


def generate_summary(job):
    resume = load_resume()
    job_desc = clean_html(job.get("description", ""))[:1800]
    keywords = extract_keywords(job_desc, limit=12)

    base_experience = []
    for exp in resume.get("experience", []):
        base_experience.append(f"{exp.get('role', '')} at {exp.get('company', '')}")

    prompt = f"""
Write a professional software engineer summary.

RULES:
- Output only the summary text.
- 3 sentences maximum.
- update the summary everytime based on the JD
- Do not say anything like recruter friendly or anything of that kind 
- Do not mention "resume", "recruiter", "summary", or "job description" keywords.
- Do not use filler phrases like "highly passionate", "results-driven", or "dynamic".
- Focus on backend, AI, APIs, cloud, and scalable systems.
- Use only facts supported by the base experience.
- Naturally include a few relevant keywords if they fit.
- Do not invent experience.

BASE EXPERIENCE:
{"; ".join(base_experience)}

JOB KEYWORDS:
{", ".join(keywords)}

JOB DESCRIPTION:
{job_desc}
""".strip()

    response = ollama.chat(
        model="llama3.1:8b",
        messages=[
            {"role": "system", "content": "You write concise professional summaries only."},
            {"role": "user", "content": prompt}
        ],
        options={
            "temperature": 0.1,
            "num_predict": 100
        }
    )

    raw = response["message"]["content"].strip()
    cleaned = post_clean_summary(raw)

    if len(cleaned) < 35:
        return fallback_summary()

    return cleaned