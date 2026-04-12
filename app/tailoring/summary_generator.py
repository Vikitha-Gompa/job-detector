import ollama
import json


def load_resume():
    with open("data/base_resume.json") as f:
        return json.load(f)


def generate_summary(job):
    resume = load_resume()

    prompt = f"""
Write a professional resume summary.

STRICT RULES:
- ONLY output the summary (no explanations)
- 2–3 sentences only
- No bullet points
- No headings
- No meta commentary
- No phrases like "this summary"

Focus:
- Backend engineering
- AI / ML systems
- Scalability and performance

Job Description:
{job.get("description", "")[:2000]}
"""

    response = ollama.chat(
        model="llama3.1:8b",
        messages=[{"role": "user", "content": prompt}]
    )

    return response["message"]["content"].strip()