import json
from jinja2 import Template
from app.tailoring.llm_tailor import tailor_resume


def load_resume():
    with open("data/base_resume.json", encoding="utf-8") as f:
        return json.load(f)


def load_template():
    with open("templates/resume_template.html", encoding="utf-8") as f:
      return Template(f.read())


def generate_resume(job):
    resume = load_resume()

    # ✅ Fix skills formatting
    resume["skills"] = ", ".join(resume["skills"])

    # ✅ Clean AI output
    raw = tailor_resume(job)

    ai_bullets = [
    line.replace("**", "").strip("•-* ").strip()
    for line in raw.split("\n")
    if line.strip()
    and len(line.strip()) > 20
    and not any(
        line.lower().startswith(x)
        for x in ["here", "note", "i've", "i have", "this", "these"]
    )
]
    ai_bullets = ai_bullets[:3]

    # Inject into first experience
    if resume["experience"]:
        resume["experience"][0]["bullets"] = ai_bullets

    template = load_template()
    return template.render(**resume)