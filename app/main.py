import json
from app.collectors.greenhouse import fetch_greenhouse
from app.filters.job_filter import filter_jobs
from app.scoring.matcher import rank_jobs
from app.tailoring.resume_generator import generate_resume
from app.tailoring.pdf_generator import html_to_pdf


def load_companies():
    with open("data/companies.json", encoding="utf-8") as f:
        return json.load(f)


def save_jobs(jobs):
    with open("data/jobs.json", "w", encoding="utf-8") as f:
        json.dump(jobs, f, indent=2)


def save_output(text):
    with open("output/tailored_resume.txt", "a", encoding="utf-8") as f:
        f.write(text + "\n\n---\n\n")


def main():
    companies = load_companies()

    all_jobs = []

    # 🔹 Fetch jobs
    for board in companies.get("greenhouse", []):
        print(f"Fetching jobs from {board}...")
        jobs = fetch_greenhouse(board)
        all_jobs.extend(jobs)

    print(f"\nTotal jobs fetched: {len(all_jobs)}")

    # 🔹 Save all jobs
    save_jobs(all_jobs)

    # 🔹 Filter jobs
    filtered_jobs = filter_jobs(all_jobs)
    print(f"\nFiltered jobs: {len(filtered_jobs)}")

    # 🔹 Rank jobs
    ranked = rank_jobs(filtered_jobs)

    # 🔹 Save top jobs
    save_jobs(ranked[:20])

    # 🔹 Debug sample
    print("\nSample normalized job:\n")
    print(all_jobs[0])

    # 🔹 Show top matches
    print("\n🔥 Top Matches:\n")
    for job in ranked[:5]:
        print("\n---")
        print("Score:", job["score"])
        print("Title:", job["title"])
        print("Company:", job["company"])
        print("Location:", job["location"])
        print("URL:", job["job_url"])

    # 🔹 ✅ IMPORTANT: THIS LOOP MUST BE INSIDE main()
    for i, job in enumerate(ranked[:2]):
        print(f"\n--- Generating full resume for job {i+1} ---\n")

        resume_text = generate_resume(job)

        print(resume_text)

        # Save markdown
        with open(f"output/resume_{i+1}.md", "w", encoding="utf-8") as f:
            f.write(resume_text)

        # Convert to PDF
        html_to_pdf(
            resume_text,
            f"output/resume_{i+1}.pdf"
        )

        # Save combined output
        save_output(resume_text)


if __name__ == "__main__":
    main()