import requests
from bs4 import BeautifulSoup


def fetch_job_from_url(url):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0"
        }

        res = requests.get(url, headers=headers, timeout=10)
        res.raise_for_status()

        soup = BeautifulSoup(res.text, "html.parser")

        # Get text from page
        text = soup.get_text(separator="\n")

        # Clean text
        lines = [line.strip() for line in text.split("\n") if len(line.strip()) > 40]

        description = "\n".join(lines[:100])  # limit size

        return {
            "title": "Custom Job",
            "company": "Manual Input",
            "location": "",
            "description": description,
            "job_url": url,
            "posted_at": "",
            "source": "manual"
        }

    except Exception as e:
        print("Error scraping job:", e)
        return None