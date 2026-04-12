import requests
from bs4 import BeautifulSoup


def fetch_job_from_url(url):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        }

        res = requests.get(url, headers=headers, timeout=10)

        if res.status_code != 200:
            print("❌ Failed to fetch:", res.status_code)
            return None

        soup = BeautifulSoup(res.text, "html.parser")

        # =========================
        # 🔹 TITLE EXTRACTION
        # =========================
        title = "Job"
        if soup.title and soup.title.string:
            title = soup.title.string.strip()

        # =========================
        # 🔹 DESCRIPTION EXTRACTION
        # =========================
        # Extract ALL visible text (robust fallback)
        text = soup.get_text(separator="\n")

        # Clean text
        lines = []
        for line in text.split("\n"):
            line = line.strip()

            if (
                len(line) > 40
                and not any(x in line.lower() for x in ["cookie", "privacy", "login", "sign in"])
            ):
                lines.append(line)

        # Join top relevant content
        description = "\n".join(lines[:120])

        # =========================
        # 🔹 SAFETY CHECK
        # =========================
        if len(description) < 300:
            print("⚠️ Weak extraction — description too short")

        # =========================
        # 🔹 RETURN STRUCTURED JOB
        # =========================
        return {
            "title": title,
            "company": "External Job",
            "location": "",
            "description": description,
            "job_url": url,
            "posted_at": "",
            "source": "manual"
        }

    except Exception as e:
        print("❌ SCRAPER ERROR:", e)
        return None