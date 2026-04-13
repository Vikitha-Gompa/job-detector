import json
import re
import ast
import textwrap
import ollama
from jinja2 import Template

from app.tailoring.llm_tailor import tailor_resume
from app.tailoring.summary_generator import generate_summary


SUMMARY_MAX_LEN = 350


def load_resume():
    with open("data/base_resume.json", encoding="utf-8") as f:
        return json.load(f)


def load_template():
    with open("templates/resume_template.html", encoding="utf-8") as f:
        return Template(f.read())


def clean_summary_text(summary):
    if not summary:
        return ""

    summary = " ".join(summary.strip().split())

    bad_prefix_patterns = [
        r"^(here is|this is|below is)\s+",
        r"^(a professional software engineer)\s*",
        r"^(professional software engineer)\s*",
        r"^(resume summary)\s*[:\-]?\s*",
        r"^(summary)\s*[:\-]?\s*"
    ]

    for pattern in bad_prefix_patterns:
        summary = re.sub(pattern, "", summary, flags=re.IGNORECASE)

    summary = re.sub(
        r"\b(recruiter-friendly|recruiter friendly|resume|job description)\b",
        "",
        summary,
        flags=re.IGNORECASE
    )

    summary = re.sub(r"\s+", " ", summary).strip(" -:;,.")
    return summary


def looks_cut_off(summary):
    if not summary:
        return True

    bad_endings = (
        "and", "or", "with", "in", "of", "to", "for", "on", "by", "an", "a", "the"
    )

    summary = summary.strip()

    if len(summary) < 50:
        return True

    if summary.endswith("..."):
        return True

    words = summary.lower().split()
    if words and words[-1] in bad_endings:
        return True

    if not re.search(r"[.!?]$", summary):
        return True

    return False


def normalize_summary(summary, max_len=SUMMARY_MAX_LEN):
    summary = clean_summary_text(summary)
    if not summary:
        return ""

    sentences = re.split(r'(?<=[.!?])\s+', summary)
    sentences = [s.strip() for s in sentences if s.strip()]

    if not sentences:
        return ""

    candidate = ""
    for sentence in sentences:
        next_candidate = (candidate + " " + sentence).strip()
        if len(next_candidate) <= max_len:
            candidate = next_candidate
        else:
            break

    if candidate:
        return candidate

    shortened = textwrap.shorten(summary, width=max_len, placeholder="...")
    return shortened


def get_base_summary(resume):
    base_summary = resume.get("summary", "")
    cleaned = normalize_summary(base_summary, max_len=SUMMARY_MAX_LEN)
    return cleaned


def normalize_bullets(bullets, limit=3):
    cleaned = []
    seen = set()

    for b in bullets:
        if not b:
            continue

        b = " ".join(str(b).strip().split())
        b = b.lstrip("-• ").strip()

        if len(b) < 20:
            continue

        key = b.lower()[:140]
        if key not in seen:
            cleaned.append(b)
            seen.add(key)

    return cleaned[:limit]


def trim_for_one_page(resume):
    resume["experience"] = resume.get("experience", [])[:4]

    for exp in resume.get("experience", []):
        exp["bullets"] = normalize_bullets(exp.get("bullets", []), limit=3)

    resume["projects"] = resume.get("projects", [])[:3]

    for project in resume.get("projects", []):
        project["bullets"] = normalize_bullets(project.get("bullets", []), limit=3)

    return resume


def safe_parse_json_like(raw):
    raw = raw.strip()

    try:
        return json.loads(raw)
    except Exception:
        pass

    try:
        return ast.literal_eval(raw)
    except Exception:
        pass

    match = re.search(r"\{.*\}", raw, re.S)
    if match:
        block = match.group(0)

        try:
            return json.loads(block)
        except Exception:
            pass

        try:
            return ast.literal_eval(block)
        except Exception:
            pass

    return None


def extract_project_bullets(parsed):
    if not parsed:
        return []

    if isinstance(parsed, dict):
        if isinstance(parsed.get("bullets"), list):
            return parsed["bullets"]

        candidate_keys = ["bullet1", "bullet2", "bullet3", "bullet_1", "bullet_2", "bullet_3"]
        found = [parsed.get(k) for k in candidate_keys if parsed.get(k)]
        if found:
            return found

    if isinstance(parsed, list):
        return [x for x in parsed if isinstance(x, str)]

    return []


def safe_project_bullets(project, job_description):
    prompt = f"""
Rewrite these project bullets for a Software Engineer role.

RULES:
- Keep the same meaning.
- Improve technical clarity and recruiter readability.
- Use only technologies, scope, and impact already supported by the original content.
- Do not invent tools, metrics, achievements.
- Keep bullets concise and ATS-friendly.
- Each bullet must be 2-3 sentences, as detailed as possible about the explanation of the project point.
- Each project should have 3 bullet points.
- Return only valid JSON.

Return format:
{{
  "bullets": ["...", "...", "..."]
}}

PROJECT NAME:
{project.get("name", "")}

ORIGINAL BULLETS:
{project.get("bullets", [])}

JOB DESCRIPTION:
{job_description[:1300]}
""".strip()

    response = ollama.chat(
        model="llama3.1:8b",
        messages=[
            {"role": "system", "content": "Return strict JSON only. Do not return explanations."},
            {"role": "user", "content": prompt}
        ],
        options={"temperature": 0.1, "num_predict": 160}
    )

    raw = response["message"]["content"].strip()
    parsed = safe_parse_json_like(raw)
    bullets = extract_project_bullets(parsed)
    bullets = normalize_bullets(bullets, limit=3)

    if bullets:
        return bullets

    return normalize_bullets(project.get("bullets", []), limit=3)


def tailor_projects_with_llm(projects, job):
    updated_projects = []

    for project in projects[:3]:
        bullets = safe_project_bullets(project, job.get("description", ""))

        updated_projects.append({
            "name": project.get("name", ""),
            "bullets": bullets if bullets else normalize_bullets(project.get("bullets", []), limit=3)
        })

    return updated_projects


def choose_summary(resume, generated_summary):
    base_summary = get_base_summary(resume)
    cleaned_generated = normalize_summary(generated_summary, max_len=SUMMARY_MAX_LEN)

    if not cleaned_generated:
        return base_summary

    if looks_cut_off(cleaned_generated):
        return base_summary

    return cleaned_generated


def generate_resume(job):
    resume = load_resume()

    try:
        generated_summary = generate_summary(job)
        resume["summary"] = choose_summary(resume, generated_summary)
    except Exception as e:
        print("Summary error:", e)
        resume["summary"] = get_base_summary(resume)

    try:
        tailored = tailor_resume(job)
        for i, exp in enumerate(tailored.get("experience", [])):
            if i < len(resume.get("experience", [])):
                bullets = normalize_bullets(exp.get("bullets", []), limit=3)
                if bullets:
                    resume["experience"][i]["bullets"] = bullets
    except Exception as e:
        print("Experience error:", e)

    try:
        resume["projects"] = tailor_projects_with_llm(resume.get("projects", []), job)
    except Exception as e:
        print("Projects error:", e)
        resume["projects"] = [
            {
                "name": p.get("name", ""),
                "bullets": normalize_bullets(p.get("bullets", []), limit=2)
            }
            for p in resume.get("projects", [])[:3]
        ]

    resume["skills"] = resume.get("skills", [])
    resume = trim_for_one_page(resume)

    template = load_template()
    html = template.render(**resume)
    return html, resume