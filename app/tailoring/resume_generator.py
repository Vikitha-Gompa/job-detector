import json
from jinja2 import Template
from app.tailoring.llm_tailor import tailor_resume
from app.tailoring.summary_generator import generate_summary


def load_resume():
    with open("data/base_resume.json", encoding="utf-8") as f:
        return json.load(f)


def load_template():
    with open("templates/resume_template.html", encoding="utf-8") as f:
        return Template(f.read())


def clean_bullets(raw_text):
    bullets = []

    for line in raw_text.split("\n"):
        line = line.strip()

        if (
            line
            and 70 < len(line) < 260
            and not any(
                line.lower().startswith(x)
                for x in [
                    "here",
                    "note",
                    "i've",
                    "i have",
                    "this",
                    "these",
                    "based on",
                    "the following",
                    "below are"
                ]
            )
        ):
            cleaned = (
                line.replace("**", "")
                    .replace("’", "'")
                    .strip("•-* ")
                    .strip()
            )

            cleaned = cleaned[:260]
            bullets.append(cleaned)

    return bullets[:3]


def generate_resume(job):
    resume = load_resume()

    # =========================================
    # 🔥 1. DYNAMIC SUMMARY
    # =========================================
    try:
        summary = generate_summary(job)
        summary = summary.replace("\n", " ").strip()

        for bad in ["Here is", "This is", "Below is", "Summary:"]:
            summary = summary.replace(bad, "")

        resume["summary"] = summary

    except Exception:
        pass

    # =========================================
    # 🔥 2. SKILLS (SAFE MERGE)
    # =========================================
    base_skills = resume["skills"]

    job_text = job.get("description", "").lower()
    extra_skills = []

    if "kafka" in job_text:
        extra_skills.append("Apache Kafka")
    if "spark" in job_text:
        extra_skills.append("Apache Spark")
    if "airflow" in job_text:
        extra_skills.append("Apache Airflow")

    merged_skills = list(dict.fromkeys(base_skills + extra_skills))
    resume["skills"] = ", ".join(merged_skills)

    # =========================================
    # 🔥 3. BULLET TAILORING (EXPERIENCE + PROJECTS)
    # =========================================
    try:
        raw = tailor_resume(job)
        ai_bullets = clean_bullets(raw)

        if len(ai_bullets) == 3:

            # 🔹 EXPERIENCE
            if resume.get("experience"):
                for i, exp in enumerate(resume["experience"]):

                    if i == 0:
                        # Main experience → strongest tailoring
                        exp["bullets"] = ai_bullets
                    else:
                        # Slight variation for realism
                        exp["bullets"] = [
                            b.replace("Developed", "Worked on")
                             .replace("Built", "Implemented")
                             .replace("Designed", "Contributed to")
                            for b in ai_bullets
                        ]

            # 🔹 PROJECTS
            if resume.get("projects"):
                for proj in resume["projects"]:
                    proj["bullets"] = [
                        b.replace("Developed", "Built")
                         .replace("Worked on", "Engineered")
                         .replace("Contributed to", "Designed")
                        for b in ai_bullets
                    ]

    except Exception:
        pass

    # =========================================
    # 🔥 4. RENDER TEMPLATE
    # =========================================
    template = load_template()
    return template.render(**resume)