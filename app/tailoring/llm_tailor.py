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

STRICT RULES:
- EXACTLY 3 bullet points
- Each bullet 1–2 lines
- NO explanations
- NO intro text
- NO headings
- ONLY bullet points

Focus:
- Backend systems
- AI / ML
- APIs / scalability

Include:
- Metrics (% improvement, latency, scale)
- Strong action verbs

Job Description:
{job.get("description", "")[:2000]}
"""
    response = ollama.chat(
        model="llama3.1:8b",
        messages=[{"role": "user", "content": prompt}]
    )

    return response["message"]["content"]