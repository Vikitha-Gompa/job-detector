import json
from jinja2 import Template
from app.tailoring.llm_tailor import tailor_resume
from app.tailoring.summary_generator import generate_summary


# =========================
# LOAD BASE RESUME
# =========================
def load_resume():
    with open("data/base_resume.json", encoding="utf-8") as f:
        return json.load(f)


def load_template():
    with open("templates/resume_template.html", encoding="utf-8") as f:
        return Template(f.read())


# =========================
# CLEAN BULLETS (CONTROLLED)
# =========================
def clean_bullets(raw_text):
    bullets = []

    for line in raw_text.split("\n"):
        line = line.strip()

        if line and len(line) > 40:
            cleaned = (
                line.replace("**", "")
                .replace("’", "'")
                .strip("•-* ")
                .strip()
            )

            # keep short but meaningful
            cleaned = " ".join(cleaned.split()[:20])

            bullets.append(cleaned)

    return bullets[:3]


# =========================
# CLEAN SUMMARY
# =========================
def clean_summary(summary):
    summary = summary.replace("\n", " ").strip()

    for bad in ["Here is", "This is", "Below is", "Summary:", "This summary"]:
        summary = summary.replace(bad, "")

    return " ".join(summary.split()[:35])


# =========================
# MAIN FUNCTION
# =========================
def generate_resume(job):

    # 🔥 ALWAYS START FROM BASE
    resume = load_resume()

    # =========================================
    # 🔥 1. SUMMARY (ONLY UPDATE FIELD)
    # =========================================
    try:
        summary = generate_summary(job)
        resume["summary"] = clean_summary(summary)
    except:
        pass

    # =========================================
    # 🔥 2. SKILLS (DO NOT MODIFY LIST)
    # =========================================
    skills_list = resume["skills"][:]   # preserve original
    resume["skills"] = ", ".join(skills_list)

    # =========================================
    # 🔥 3. EXPERIENCE (ONLY FIRST ROLE MODIFIED)
    # =========================================
    try:
        raw = tailor_resume(job)
        bullets = clean_bullets(raw)

        if bullets:
            resume["experience"][0]["bullets"] = bullets

    except:
        pass

    # =========================================
    # 🔥 4. DO NOT TOUCH PROJECTS / EDUCATION
    # =========================================
    # (this is key — keeps your base structure)

    # =========================================
    # 🔥 5. RENDER USING YOUR TEMPLATE
    # =========================================
    template = load_template()
    html = template.render(**resume)

    return html