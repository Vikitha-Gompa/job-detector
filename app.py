import streamlit as st
import json

from app.collectors.greenhouse import fetch_greenhouse
from app.filters.job_filter import filter_jobs
from app.scoring.matcher import rank_jobs
from app.tailoring.resume_generator import generate_resume
from app.tailoring.pdf_generator import html_to_pdf


st.set_page_config(page_title="AI Resume Tailor", layout="wide")

st.title("🚀 AI Resume Tailoring System")

# Load companies
with open("data/companies.json") as f:
    companies = json.load(f)

# Button to fetch jobs
if st.button("Fetch Jobs"):
    all_jobs = []

    for board in companies.get("greenhouse", []):
        jobs = fetch_greenhouse(board)
        all_jobs.extend(jobs)

    st.session_state["jobs"] = all_jobs
    st.success(f"Fetched {len(all_jobs)} jobs")

# If jobs loaded
if "jobs" in st.session_state:
    jobs = st.session_state["jobs"]

    # Filter + rank
    filtered = filter_jobs(jobs)
    ranked = rank_jobs(filtered)

    st.subheader("Top Jobs")

    # Select job
    job_titles = [f"{j['title']} - {j['company']}" for j in ranked[:10]]
    selected = st.selectbox("Choose a job", job_titles)

    selected_job = ranked[job_titles.index(selected)]

    st.write("### Job Details")
    st.write(selected_job["title"])
    st.write(selected_job["company"])
    st.write(selected_job["location"])
    st.write(selected_job["job_url"])

    # Generate resume
    if st.button("Generate Resume"):
        resume_html = generate_resume(selected_job)

        st.subheader("Generated Resume")
        st.code(resume_html, language="html")

        # Save PDF
        pdf_path = "output/streamlit_resume.pdf"
        html_to_pdf(resume_html, pdf_path)

        with open(pdf_path, "rb") as f:
            st.download_button(
                "Download Resume PDF",
                f,
                file_name="resume.pdf"
            )