import streamlit as st
import json
from datetime import datetime

from app.collectors.greenhouse import fetch_greenhouse
from app.filters.job_filter import filter_jobs
from app.scoring.matcher import rank_jobs
from app.tailoring.resume_generator import generate_resume
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


# =========================
# JOB SEARCH
# =========================
if page == "Job Search":

    # =========================
    # APPLY PANEL (TOP)
    # =========================
    if "apply_job" in st.session_state:
        job = st.session_state["apply_job"]

        st.success("🚀 Complete your application")

        st.markdown(f"### {job['title']}")
        st.write(f"{job['company']} • {job['location']}")

        # ✅ MANUAL LINK ONLY (FIXED)
        st.markdown(f"### 👉 [Click here to apply]({job['job_url']})")
        st.info("Click the link above to apply, then come back and confirm.")

        col1, col2 = st.columns(2)

        if col1.button("✅ I Applied", key="confirm_apply"):
            apply_time = datetime.now()

            job["status"] = "applied"
            job["applied_at"] = str(apply_time)

            if "apply_start_time" in job:
                start = datetime.fromisoformat(job["apply_start_time"])
                job["apply_duration_sec"] = (apply_time - start).seconds

            save_job(job, "applied")

            del st.session_state["apply_job"]
            st.rerun()

        if col2.button("❌ Cancel", key="cancel_apply"):
            del st.session_state["apply_job"]
            st.rerun()

        st.divider()

    # =========================
    # FETCH JOBS
    # =========================
    if st.button("Fetch Jobs"):
        with open("data/companies.json") as f:
            companies = json.load(f)

        jobs = []
        for board in companies.get("greenhouse", []):
            jobs.extend(fetch_greenhouse(board))

        st.session_state["jobs"] = jobs

    # =========================
    # DISPLAY JOBS
    # =========================
    if "jobs" in st.session_state:

        jobs = st.session_state["jobs"]

        filtered = []

        for j in jobs:
            if location_filter == "US Only":
                if not is_us_location(j["location"]):
                    continue

            if skill_filter and skill_filter.lower() not in j["description"].lower():
                continue

            filtered.append(j)

        ranked = rank_jobs(filter_jobs(filtered))

        # ✅ REMOVE APPLIED JOBS
        saved = load_saved_jobs()
        applied_urls = [j["job_url"] for j in saved if j.get("status") == "applied"]
        ranked = [j for j in ranked if j["job_url"] not in applied_urls]

        st.subheader(f"🎯 Jobs available: {len(ranked)}")

        for i, job in enumerate(ranked[:20]):

            st.markdown(f"### {job['title']}")
            st.write(f"{job['company']} • {job['location']}")

            col1, col2, col3 = st.columns(3)

            # Save
            if col1.button("⭐ Save", key=f"save_{i}"):
                save_job(job, "saved")
                st.success("Saved!")

            # Apply
            if col2.button("🚀 Apply", key=f"apply_{i}"):
                job["apply_start_time"] = str(datetime.now())
                st.session_state["apply_job"] = job
                st.rerun()

            # Resume
            if col3.button("✨ Resume", key=f"resume_{i}"):
                html = generate_resume(job)
                st.components.v1.html(html, height=400)

            st.divider()


# =========================
# MANUAL JOB
# =========================
elif page == "Manual Job":

    st.title("🔗 Manual Job Input")

    tab1, tab2 = st.tabs(["🌐 URL", "📝 Paste JD"])

    with tab1:
        url = st.text_input("Paste Job URL")

        if st.button("Fetch Job"):
            job = fetch_job_from_url(url)

            if job:
                st.session_state["manual"] = job
                st.success("Job fetched successfully")
            else:
                st.error("Failed to fetch job")

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
                st.success("JD loaded")
            else:
                st.warning("Paste job description")

    if "manual" in st.session_state:
        job = st.session_state["manual"]

        st.subheader("🧾 Preview")
        st.write(job["description"][:1000])

        if st.button("✨ Generate Resume"):
            html = generate_resume(job)
            st.components.v1.html(html, height=500)


# =========================
# SAVED JOBS
# =========================
elif page == "Saved Jobs":

    st.title("📌 Saved Jobs")

    saved = load_saved_jobs()

    for i, job in enumerate(saved):

        st.markdown(f"### {job['title']}")
        st.write(f"{job['company']} • {job['location']}")
        st.write(f"Status: {job['status']}")

        col1, col2 = st.columns(2)

        if col1.button("Interview", key=i):
            saved[i]["status"] = "interview"

        if col2.button("Rejected", key=str(i) + "r"):
            saved[i]["status"] = "rejected"

        st.divider()

    with open("data/saved_jobs.json", "w") as f:
        json.dump(saved, f, indent=2)


# =========================
# DASHBOARD
# =========================
elif page == "Dashboard":

    st.title("📊 Dashboard")

    saved = load_saved_jobs()

    st.metric("Saved", len(saved))
    st.metric("Applied", len([j for j in saved if j["status"] == "applied"]))
    st.metric("Interview", len([j for j in saved if j["status"] == "interview"]))
    st.metric("Rejected", len([j for j in saved if j["status"] == "rejected"]))