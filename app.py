import json
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

from app.collectors.greenhouse import fetch_greenhouse
from app.collectors.web_scraper import fetch_job_from_url
from app.filters.job_filter import filter_jobs
from app.scoring.matcher import rank_jobs
from app.tailoring.resume_generator import generate_resume
from app.tailoring.pdf_generator import html_to_pdf
from app.utils.location_parser import is_us_location


DATA_DIR = Path("data")
OUTPUT_DIR = Path("output")
SAVED_JOBS_FILE = DATA_DIR / "saved_jobs.json"
COMPANIES_FILE = DATA_DIR / "companies.json"

DATA_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)


def load_json_file(path, default):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def save_json_file(path, payload):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)


def load_saved_jobs():
    return load_json_file(SAVED_JOBS_FILE, [])


def save_job(job, status="saved"):
    saved = load_saved_jobs()
    job_url = (job.get("job_url") or "").strip()

    if job_url and any((j.get("job_url") or "").strip() == job_url for j in saved):
        return False

    record = deepcopy(job)
    record["status"] = status
    record["updated_at"] = datetime.now().isoformat()

    saved.append(record)
    save_json_file(SAVED_JOBS_FILE, saved)
    return True


def mark_job_status(job_url, status):
    saved = load_saved_jobs()
    updated = False

    for item in saved:
        if (item.get("job_url") or "").strip() == (job_url or "").strip():
            item["status"] = status
            item["updated_at"] = datetime.now().isoformat()
            updated = True

    if updated:
        save_json_file(SAVED_JOBS_FILE, saved)

    return updated


def parse_posted_at(posted_at):
    if not posted_at:
        return None
    try:
        return datetime.fromisoformat(str(posted_at).replace("Z", "+00:00"))
    except Exception:
        return None


def is_recent(job, hours):
    posted = parse_posted_at(job.get("posted_at"))
    if not posted:
        return False
    now = datetime.now(posted.tzinfo or timezone.utc)
    return (now - posted) <= timedelta(hours=hours)


def get_posted_time(job):
    posted = parse_posted_at(job.get("posted_at"))
    return posted if posted else datetime.min.replace(tzinfo=timezone.utc)


@st.cache_data(show_spinner=False, ttl=1800)
def fetch_all_greenhouse_jobs():
    companies = load_json_file(COMPANIES_FILE, {})
    jobs = []

    for board in companies.get("greenhouse", []):
        try:
            jobs.extend(fetch_greenhouse(board))
        except Exception:
            continue

    return jobs


def apply_job_filters(jobs, location_filter, skill_filter, time_filter):
    filtered = []

    for job in jobs:
        description = (job.get("description") or "")
        location = job.get("location") or ""

        if time_filter == "Last 24 Hours" and not is_recent(job, 24):
            continue

        if time_filter == "Last 3 Days" and not is_recent(job, 72):
            continue

        if location_filter == "US Only" and not is_us_location(location):
            continue

        if skill_filter and skill_filter.lower().strip() not in description.lower():
            continue

        filtered.append(job)

    filtered.sort(key=get_posted_time, reverse=True)
    return filtered


def build_resume_pdf(html, file_path):
    html_to_pdf(html, str(file_path))
    with open(file_path, "rb") as f:
        return f.read()


def render_resume_block(job, key_prefix):
    generate_key = f"{key_prefix}_generate"
    preview_key = f"{key_prefix}_preview_html"
    pdf_key = f"{key_prefix}_pdf_bytes"
    resume_json_key = f"{key_prefix}_resume_json"
    pdf_name_key = f"{key_prefix}_pdf_name"

    if st.button("✨ Generate Resume", key=generate_key):
        with st.spinner("Generating tailored resume..."):
            html, tailored_resume = generate_resume(job)

            pdf_filename = f"{key_prefix}_resume.pdf"
            pdf_path = OUTPUT_DIR / pdf_filename
            pdf_bytes = build_resume_pdf(html, pdf_path)

            st.session_state[preview_key] = html
            st.session_state[pdf_key] = pdf_bytes
            st.session_state[resume_json_key] = tailored_resume
            st.session_state[pdf_name_key] = pdf_filename

    if preview_key in st.session_state:
        components.html(st.session_state[preview_key], height=700, scrolling=True)

        col_a, col_b = st.columns(2)

        with col_a:
            st.download_button(
                label="⬇️ Download Resume PDF",
                data=st.session_state[pdf_key],
                file_name=st.session_state.get(pdf_name_key, "resume.pdf"),
                mime="application/pdf",
                key=f"{key_prefix}_download_pdf",
                on_click="ignore"
            )

        with col_b:
            st.download_button(
                label="⬇️ Download Resume JSON",
                data=json.dumps(st.session_state[resume_json_key], indent=2, ensure_ascii=False),
                file_name=f"{key_prefix}_resume.json",
                mime="application/json",
                key=f"{key_prefix}_download_json",
                on_click="ignore"
            )


st.set_page_config(page_title="AI Resume Tailor", layout="wide")
st.title("🚀 AI Resume Tailor")

page = st.sidebar.radio("Menu", ["Job Search", "Manual Job", "Saved Jobs", "Dashboard"])
location_filter = st.sidebar.selectbox("Location", ["All", "US Only"])
skill_filter = st.sidebar.text_input("Skill")
time_filter = st.sidebar.selectbox("Posted Time", ["All", "Last 24 Hours", "Last 3 Days"])


if page == "Job Search":
    st.subheader("Search Recent Jobs")

    top_col1, top_col2 = st.columns([1, 1])

    with top_col1:
        if st.button("Fetch Jobs", use_container_width=True):
            with st.spinner("Fetching jobs..."):
                st.session_state["jobs"] = fetch_all_greenhouse_jobs()

    with top_col2:
        if st.button("Clear Jobs", use_container_width=True):
            st.session_state.pop("jobs", None)

    jobs = st.session_state.get("jobs", [])

    if jobs:
        filtered = apply_job_filters(jobs, location_filter, skill_filter, time_filter)

        try:
            ranked = rank_jobs(filter_jobs(filtered))
        except Exception:
            ranked = filtered

        st.subheader(f"🎯 Jobs available: {len(ranked)}")

        for i, job in enumerate(ranked[:20]):
            title = job.get("title", "Untitled Role")
            company = job.get("company", "Unknown Company")
            location = job.get("location", "Unknown Location")
            job_url = job.get("job_url", "")
            posted_at = job.get("posted_at", "")

            st.markdown(f"### {title}")
            st.write(f"{company} • {location}")

            if posted_at:
                st.caption(f"Posted: {posted_at}")

            col1, col2, col3 = st.columns(3)

            with col1:
                if st.button("⭐ Save", key=f"save_{i}", use_container_width=True):
                    ok = save_job(job, "saved")
                    if ok:
                        st.success("Job saved")
                    else:
                        st.info("Job already saved")

            with col2:
                if job_url:
                    if st.link_button("🚀 Apply", job_url, use_container_width=True):
                        mark_job_status(job_url, "applied")
                else:
                    st.button("🚀 Apply", disabled=True, key=f"disabled_apply_{i}", use_container_width=True)

            with col3:
                render_resume_block(job, key_prefix=f"job_{i}")

            st.divider()
    else:
        st.info("Click 'Fetch Jobs' to load jobs.")


elif page == "Manual Job":
    st.subheader("🔗 Manual Job Input")

    tab1, tab2 = st.tabs(["🌐 URL", "📝 Paste JD"])

    with tab1:
        url = st.text_input("Paste Job URL")

        if st.button("Fetch Job", key="fetch_manual_url"):
            if not url.strip():
                st.warning("Please paste a job URL.")
            else:
                with st.spinner("Extracting job details..."):
                    try:
                        job = fetch_job_from_url(url.strip())
                    except Exception:
                        job = None

                if job and len((job.get("description") or "").strip()) > 300:
                    st.session_state["manual_job"] = job
                    st.success("✅ Job extracted")
                else:
                    st.warning("⚠️ Weak extraction — description too short. Paste the JD manually for better tailoring.")

    with tab2:
        jd = st.text_area("Paste Job Description", height=260)
        manual_title = st.text_input("Job Title", value="Custom Job")
        manual_company = st.text_input("Company", value="Manual Entry")
        manual_location = st.text_input("Location", value="")

        if st.button("Use JD", key="use_manual_jd"):
            if jd.strip():
                st.session_state["manual_job"] = {
                    "title": manual_title.strip() or "Custom Job",
                    "company": manual_company.strip() or "Manual Entry",
                    "location": manual_location.strip(),
                    "description": jd.strip(),
                    "job_url": "manual",
                    "posted_at": datetime.now().isoformat()
                }
                st.success("✅ Job description loaded")
            else:
                st.warning("Paste a job description first.")

    manual_job = st.session_state.get("manual_job")

    if manual_job:
        st.subheader("🧾 Job Preview")
        st.write(f"**Title:** {manual_job.get('title', '')}")
        st.write(f"**Company:** {manual_job.get('company', '')}")
        if manual_job.get("location"):
            st.write(f"**Location:** {manual_job.get('location', '')}")

        preview_text = manual_job.get("description", "")
        st.text_area("Description Preview", value=preview_text[:2500], height=250, disabled=True)

        render_resume_block(manual_job, key_prefix="manual")


elif page == "Saved Jobs":
    st.subheader("⭐ Saved Jobs")

    saved = load_saved_jobs()

    if not saved:
        st.info("No saved jobs yet.")
    else:
        for idx, job in enumerate(saved):
            title = job.get("title", "Untitled Role")
            company = job.get("company", "Unknown Company")
            status = job.get("status", "saved")
            location = job.get("location", "")
            job_url = job.get("job_url", "")
            updated_at = job.get("updated_at", "")

            st.markdown(f"### {title}")
            st.write(f"{company} • {location}")
            st.write(f"Status: **{status}**")
            if updated_at:
                st.caption(f"Updated: {updated_at}")

            col1, col2 = st.columns(2)

            with col1:
                if job_url and job_url != "manual":
                    st.link_button("Open Job Post", job_url, use_container_width=True)
                else:
                    st.button("Open Job Post", disabled=True, key=f"saved_open_{idx}", use_container_width=True)

            with col2:
                render_resume_block(job, key_prefix=f"saved_{idx}")

            st.divider()


elif page == "Dashboard":
    st.subheader("📊 Dashboard")

    saved = load_saved_jobs()
    applied_count = len([j for j in saved if j.get("status") == "applied"])
    saved_count = len(saved)

    col1, col2 = st.columns(2)
    col1.metric("Saved", saved_count)
    col2.metric("Applied", applied_count)

    if saved:
        st.write("Recent saved jobs:")
        recent = sorted(saved, key=lambda x: x.get("updated_at", ""), reverse=True)[:10]
        for job in recent:
            st.write(f"- {job.get('title', 'Untitled Role')} — {job.get('company', 'Unknown Company')} ({job.get('status', 'saved')})")
    else:
        st.info("No dashboard data yet.")