import ollama
import json


def load_resume():
    with open("data/base_resume.json") as f:
        return json.load(f)


def generate_summary(job):
    resume = load_resume()

    prompt = f"""
Write a professional resume summary.

JOB DESCRIPTION:
{job['description'][:1500]}

CANDIDATE SKILLS:
{', '.join(resume['skills'])}

Rules:
- 3–4 lines
- Focus on backend, AI/ML, and cloud systems
- Include technologies (Python, AWS, etc.)
- No headings
- No quotes
- No explanations
- Do NOT start with phrases like "Here is" or "This is"
- Output ONLY the summary text
"""

    response = ollama.chat(
        model="llama3.1:8b",
        messages=[{"role": "user", "content": prompt}]
    )

    return response["message"]["content"].strip()