import streamlit as st
import json

from app.collectors.greenhouse import fetch_greenhouse
from app.collectors.web_scraper import fetch_job_from_url
from app.filters.job_filter import filter_jobs
from app.scoring.matcher import rank_jobs
from app.tailoring.resume_generator import generate_resume
from app.tailoring.pdf_generator import html_to_pdf


# 🔥 Page config
st.set_page_config(page_title="AI Resume Tailor", layout="wide")

# 🔥 Sidebar
st.sidebar.title("⚙️ Settings")
st.sidebar.write("AI Resume Tailoring System")

# 🔥 Header
st.markdown("""
# 🚀 AI Resume Tailoring System
### Generate job-specific resumes instantly
""")

st.divider()

# Load companies
with open("data/companies.json") as f:
    companies = json.load(f)

# =========================================================
# 🔗 SECTION 1 — MANUAL INPUT (URL + JD TEXT)
# =========================================================

st.subheader("🧠 Manual Job Input")

tab1, tab2 = st.tabs(["🔗 Paste Job URL", "📄 Paste Job Description"])

# -------------------------
# 🔹 TAB 1: URL INPUT
# -------------------------
with tab1:
    job_url = st.text_input("Enter job URL")

    if st.button("Fetch Job from URL"):
        with st.spinner("Scraping job description..."):
            job = fetch_job_from_url(job_url)

            if job:
                st.session_state["manual_job"] = job
                st.success("✅ Job extracted successfully!")
            else:
                st.error("❌ Failed to fetch job")

# -------------------------
# 🔹 TAB 2: RAW JD INPUT
# -------------------------
with tab2:
    jd_text = st.text_area("Paste Job Description", height=250)

    if st.button("Use This Job Description"):
        if jd_text.strip():
            st.session_state["manual_job"] = {
                "title": "Custom Job",
                "company": "Manual Input",
                "location": "",
                "description": jd_text,
                "job_url": "",
                "posted_at": "",
                "source": "manual"
            }
            st.success("✅ Job description added!")
        else:
            st.warning("⚠️ Please paste job description")

# -------------------------
# 🔹 HANDLE MANUAL JOB
# -------------------------
if "manual_job" in st.session_state:
    job = st.session_state["manual_job"]

    st.divider()
    st.subheader("🧾 Job Preview")

    st.write(job["description"][:1000])

    if st.button("✨ Generate Resume from Manual Input"):
        with st.spinner("Generating resume..."):
            resume_html = generate_resume(job)

            st.success("✅ Resume generated!")

            st.markdown("### 👀 Preview")
            st.components.v1.html(resume_html, height=600, scrolling=True)

            pdf_path = "output/manual_resume.pdf"
            html_to_pdf(resume_html, pdf_path)

            with open(pdf_path, "rb") as f:
                st.download_button(
                    "⬇️ Download PDF",
                    f,
                    file_name="resume.pdf",
                    use_container_width=True
                )

# =========================================================
# 🔍 SECTION 2 — AUTO JOB FETCH
# =========================================================

st.divider()
st.subheader("🌐 Auto Job Fetch (Greenhouse)")

if st.button("🔍 Fetch Jobs"):
    with st.spinner("Fetching jobs..."):
        all_jobs = []

        for board in companies.get("greenhouse", []):
            jobs = fetch_greenhouse(board)
            all_jobs.extend(jobs)

        st.session_state["jobs"] = all_jobs
        st.success(f"✅ {len(all_jobs)} jobs fetched!")

# -------------------------
# 🔹 JOB LIST UI
# -------------------------
if "jobs" in st.session_state:
    jobs = st.session_state["jobs"]

    filtered = filter_jobs(jobs)
    ranked = rank_jobs(filtered)

    st.divider()

    col1, col2 = st.columns([1, 2])

    # LEFT PANEL
    with col1:
        st.subheader("📌 Select Job")

        job_titles = [f"{j['title']} ({j['company']})" for j in ranked[:10]]
        selected = st.selectbox("Choose a job", job_titles)

        selected_job = ranked[job_titles.index(selected)]

        st.markdown("### 🧾 Job Info")
        st.write(f"**Title:** {selected_job['title']}")
        st.write(f"**Company:** {selected_job['company']}")
        st.write(f"**Location:** {selected_job['location']}")

        st.markdown(f"[🔗 View Job Posting]({selected_job['job_url']})")

    # RIGHT PANEL
    with col2:
        st.subheader("📄 Resume Generator")

        if st.button("✨ Generate Resume"):
            with st.spinner("Generating resume..."):
                resume_html = generate_resume(selected_job)

                st.success("✅ Resume generated!")

                st.markdown("### 👀 Preview")
                st.components.v1.html(resume_html, height=600, scrolling=True)

                pdf_path = "output/streamlit_resume.pdf"
                html_to_pdf(resume_html, pdf_path)

                with open(pdf_path, "rb") as f:
                    st.download_button(
                        "⬇️ Download PDF",
                        f,
                        file_name="resume.pdf",
                        use_container_width=True
                    )