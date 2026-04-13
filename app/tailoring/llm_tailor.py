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


def extract_keywords(text, limit=20):
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


def safe_json_load(raw):
    try:
        return json.loads(raw)
    except Exception:
        match = re.search(r"\{.*\}", raw, re.S)
        if match:
            return json.loads(match.group(0))
        raise


def build_bullet_prompt(role, original_bullet, job_text, keywords):
    return f"""
You are rewriting one resume bullet for a Software Engineer.

RULES:
- Use only facts already supported by the original bullet and resume context.
- Do not invent employers, dates, degrees, metrics, or certifications.
- improve wording and recruiter readability.
- Prefer action verb + technical detail + impact.
- Add job keywords to make it recruter and ats friendly.
- Return ONLY valid JSON.

ROLE:
{role}

JOB KEYWORDS:
{", ".join(keywords)}

JOB DESCRIPTION:
{job_text}

ORIGINAL BULLET:
{original_bullet}

Return JSON exactly like this:
{{
  "bullet": "..."
}}
""".strip()


def rewrite_bullet(role, original_bullet, job_text, keywords):
    prompt = build_bullet_prompt(role, original_bullet, job_text, keywords)

    response = ollama.chat(
        model="llama3.1:8b",
        messages=[
            {"role": "system", "content": "You output strict JSON only."},
            {"role": "user", "content": prompt}
        ],
        options={
            "temperature": 0.1,
            "num_predict": 120
        }
    )

    raw = response["message"]["content"].strip()

    try:
        parsed = safe_json_load(raw)
        bullet = parsed.get("bullet", "").strip()
        if bullet and len(bullet) >= 20:
            return bullet
    except Exception:
        pass

    return original_bullet


def tailor_resume(job):
    resume = load_resume()
    job_text = clean_html(job.get("description", ""))[:2500]
    keywords = extract_keywords(job_text, limit=20)

    tailored = []

    for exp in resume.get("experience", []):
        new_exp = dict(exp)
        rewritten = []

        for bullet in exp.get("bullets", [])[:3]:
            rewritten.append(
                rewrite_bullet(
                    role=exp.get("role", ""),
                    original_bullet=bullet,
                    job_text=job_text,
                    keywords=keywords
                )
            )

        new_exp["bullets"] = rewritten
        tailored.append(new_exp)

    resume["experience"] = tailored
    return resume