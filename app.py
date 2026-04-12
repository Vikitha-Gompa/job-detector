import streamlit as st
import json
from datetime import datetime, timedelta

from app.collectors.greenhouse import fetch_greenhouse
from app.filters.job_filter import filter_jobs
from app.scoring.matcher import rank_jobs
from app.tailoring.resume_generator import generate_resume
from app.tailoring.pdf_generator import html_to_pdf
from app.collectors.web_scraper import fetch_job_from_url
from app.utils.location_parser import is_us_location


# =========================
# STORAGE
# =========================
def load_saved_jobs():
    try:
        with open("data/saved_jobs.json") as f:
            return json.load(f)
    except:
        return []


def save_job(job, status):
    saved = load_saved_jobs()

    if any(j["job_url"] == job["job_url"] for j in saved):
        return

    job["status"] = status
    job["updated_at"] = str(datetime.now())

    saved.append(job)

    with open("data/saved_jobs.json", "w") as f:
        json.dump(saved, f, indent=2)


# =========================
# TIME FILTER
# =========================
def is_recent(job, hours):
    try:
        posted = datetime.fromisoformat(job["posted_at"].replace("Z", "+00:00"))
        now = datetime.now(posted.tzinfo)
        return (now - posted) <= timedelta(hours=hours)
    except:
        return False


def get_posted_time(job):
    try:
        return datetime.fromisoformat(job["posted_at"].replace("Z", "+00:00"))
    except:
        return datetime.min


# =========================
# CONFIG
# =========================
st.set_page_config(layout="wide")
st.title("🚀 AI Resume Tailor")


# =========================
# SIDEBAR
# =========================
page = st.sidebar.radio("Menu", ["Job Search", "Manual Job", "Saved Jobs", "Dashboard"])

location_filter = st.sidebar.selectbox("Location", ["All", "US Only"])
skill_filter = st.sidebar.text_input("Skill")

time_filter = st.sidebar.selectbox(
    "Posted Time",
    ["All", "Last 24 Hours", "Last 3 Days"]
)


# =========================
# JOB SEARCH
# =========================
if page == "Job Search":

    if st.button("Fetch Jobs"):
        with open("data/companies.json") as f:
            companies = json.load(f)

        jobs = []
        for board in companies.get("greenhouse", []):
            jobs.extend(fetch_greenhouse(board))

        st.session_state["jobs"] = jobs

    if "jobs" in st.session_state:

        jobs = st.session_state["jobs"]
        filtered = []

        for j in jobs:

            if time_filter == "Last 24 Hours" and not is_recent(j, 24):
                continue
            if time_filter == "Last 3 Days" and not is_recent(j, 72):
                continue

            if location_filter == "US Only":
                if not is_us_location(j["location"]):
                    continue

            if skill_filter and skill_filter.lower() not in j["description"].lower():
                continue

            filtered.append(j)

        filtered.sort(key=get_posted_time, reverse=True)

        ranked = rank_jobs(filter_jobs(filtered))

        st.subheader(f"🎯 Jobs available: {len(ranked)}")

        for i, job in enumerate(ranked[:20]):

            st.markdown(f"### {job['title']}")
            st.write(f"{job['company']} • {job['location']}")

            col1, col2, col3 = st.columns(3)

            if col1.button("⭐ Save", key=f"save_{i}"):
                save_job(job, "saved")

            if col2.button("🚀 Apply", key=f"apply_{i}"):
                st.markdown(f"[👉 Apply Here]({job['job_url']})")

            if col3.button("✨ Resume", key=f"resume_{i}"):

                html = generate_resume(job)

                # 🔥 PREVIEW
                st.components.v1.html(html, height=700, scrolling=True)

                # 🔥 PDF
                pdf_path = "output/job_resume.pdf"
                html_to_pdf(html, pdf_path)

                with open(pdf_path, "rb") as f:
                    st.download_button(
                        "⬇️ Download Resume PDF",
                        f,
                        file_name="resume.pdf"
                    )

            st.divider()


# =========================
# MANUAL JOB
# =========================
elif page == "Manual Job":

    st.title("🔗 Manual Job Input")

    tab1, tab2 = st.tabs(["🌐 URL", "📝 Paste JD"])

    # URL
    with tab1:
        url = st.text_input("Paste Job URL")

        if st.button("Fetch Job"):
            job = fetch_job_from_url(url)

            if job and len(job["description"]) > 300:
                st.session_state["manual"] = job
                st.success("✅ Job extracted!")
            else:
                st.error("❌ Could not extract job. Use Paste JD.")

    # JD
    with tab2:
        jd = st.text_area("Paste Job Description")

        if st.button("Use JD"):
            if jd.strip():
                st.session_state["manual"] = {
                    "title": "Custom Job",
                    "company": "Manual Entry",
                    "location": "",
                    "description": jd,
                    "job_url": "manual"
                }
                st.success("✅ JD Loaded")
            else:
                st.warning("Paste job description")

    # GENERATE
    if "manual" in st.session_state:
        job = st.session_state["manual"]

        st.subheader("🧾 Job Preview")
        st.write(job["description"][:800])

        if st.button("✨ Generate Resume"):

            html = generate_resume(job)

            # 🔥 PREVIEW
            st.components.v1.html(html, height=700, scrolling=True)

            # 🔥 PDF DOWNLOAD
            pdf_path = "output/manual_resume.pdf"
            html_to_pdf(html, pdf_path)

            with open(pdf_path, "rb") as f:
                st.download_button(
                    "⬇️ Download Resume PDF",
                    f,
                    file_name="Sai_Vikitha_Resume.pdf",
                    use_container_width=True
                )


# =========================
# SAVED JOBS
# =========================
elif page == "Saved Jobs":

    saved = load_saved_jobs()

    for job in saved:
        st.write(job["title"], "-", job["status"])


# =========================
# DASHBOARD
# =========================
elif page == "Dashboard":

    saved = load_saved_jobs()

    st.metric("Saved", len(saved))
    st.metric("Applied", len([j for j in saved if j["status"] == "applied"]))