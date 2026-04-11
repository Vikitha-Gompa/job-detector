import requests

def fetch_greenhouse(board):
    url = f"https://boards-api.greenhouse.io/v1/boards/{board}/jobs?content=true"
    
    try:
        res = requests.get(url)
        res.raise_for_status()
        data = res.json()
    except Exception as e:
        print(f"Error fetching {board}: {e}")
        return []

    jobs = []
    
    for j in data.get("jobs", []):
        jobs.append({
            "title": j.get("title", ""),
            "company": board,
            "location": j.get("location", {}).get("name", ""),
            "description": j.get("content", ""),
            "job_url": j.get("absolute_url", ""),   
            "posted_at": j.get("updated_at", ""),   
            "source": "greenhouse"                  
        })

    return jobs