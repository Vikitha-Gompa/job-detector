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
You are a professional resume writer.

Rewrite resume bullets tailored for the job.

JOB DESCRIPTION:
{job_desc}

CANDIDATE SKILLS:
{', '.join(resume['skills'])}

STRICT RULES:
- NEVER add percentages, numbers, or metrics unless explicitly provided
- DO NOT guess achievements
- Use only safe, realistic statements
- Keep bullets concise (1–2 lines)
- Focus on Python, AI, backend relevance

Output ONLY 3 bullet points.
"""
    

    response = ollama.chat(
        model="llama3.1:8b",
        messages=[{"role": "user", "content": prompt}]
    )

    return response["message"]["content"]