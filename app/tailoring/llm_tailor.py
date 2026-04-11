import ollama
import json
from bs4 import BeautifulSoup

def clean_html(html):
    return BeautifulSoup(html, "html.parser").get_text()

def load_resume():
    with open("data/base_resume.json") as f:
        return json.load(f)

def tailor_resume(job):
    resume = load_resume()

    # ✅ FIX: clean HTML here
    job_desc = clean_html(job['description'])[:2000]

    prompt = f"""
Rewrite resume bullets for this job.

JOB DESCRIPTION:
{job_desc}

CANDIDATE SKILLS:
{', '.join(resume['skills'])}

Rules:
- Output EXACTLY 3 bullet points
- Each bullet must be 1.5–2 lines (not short, not too long)
- Each bullet must follow THIS structure:
  Action verb + what was built + technologies used + impact/result
- Keep length consistent across all bullets
- Avoid very long paragraphs
- No intro text
- No explanations
- No phrases like "Here are" or "Based on"
"""
    response = ollama.chat(
        model="llama3.1:8b",
        messages=[{"role": "user", "content": prompt}]
    )

    return response["message"]["content"]