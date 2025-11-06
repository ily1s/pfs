from playwright.sync_api import sync_playwright
from dotenv import load_dotenv
import json
from datetime import datetime
from scraper import (
    navigate_to_linkedin_jobs,
    load_skills_list,
    extract_jobs_with_bs4,
    extract_recruiters,
    enrich_with_descriptions_and_skills,
    scroll_job_list,
    go_to_next_page,
)

# Load environment variables from .env file if present
load_dotenv()

print(f"\nScraping completed on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


def main():
    # Configuration
    keyword = input("Enter job keyword (e.g. Data Engineer): ").strip()
    location = input("Enter location (e.g. Morocco): ").strip()

    search_url = (
        f"https://www.linkedin.com/jobs/search/"
        f"?keywords={keyword.replace(' ','%20')}"
        f"&location={location.replace(' ','%20')}"
    )
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False
        )  # Set to True for no browser UI (for production)
        context = browser.new_context(
            viewport={"width": 1280, "height": 720},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.1 Safari/605.1.15",
        )
        page = context.new_page()
        page = navigate_to_linkedin_jobs(search_url, page)

        all_jobs = []
        skills = load_skills_list()
        seen_jobs = set()
        current_page = 1
        MAX_JOBS = 500

        while len(all_jobs) < MAX_JOBS:
            scroll_job_list(page)
            raw_jobs = extract_jobs_with_bs4(page, max_jobs=MAX_JOBS)
            jobs = []
            for job in raw_jobs:
                identifier = f"{job['job_title']} @ {job['company']}"
                if identifier not in seen_jobs:
                    seen_jobs.add(identifier)
                    jobs.append(job)
            jobs = enrich_with_descriptions_and_skills(page, jobs, skills)
            #jobs = extract_recruiters(page, jobs, search_url)
            all_jobs.extend(jobs)

            partial_filename = f"linkedin_jobs_partial_page_{current_page}.json"
            with open(partial_filename, "w", encoding="utf-8") as f:
                json.dump(all_jobs, f, ensure_ascii=False, indent=2)
            print(f"\nSaved partial data to {partial_filename}")

            if len(all_jobs) >= MAX_JOBS:
                all_jobs = all_jobs[:MAX_JOBS]  # Just in case
                break

            if not go_to_next_page(page, current_page):
                break
            current_page += 1

        print(f"Total jobs collected: {len(all_jobs)}")

        # sanitize keyword/location for filenames
        safe_kw = keyword.replace(" ", "_")
        safe_loc = location.replace(" ", "_")

        filename = (
            f"linkedin_scraper/data/"
            f"linkedin_jobs_{safe_kw}_{safe_loc}_{datetime.now():%Y%m%d_%H%M%S}.json"
        )
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(all_jobs, f, ensure_ascii=False, indent=2)
        print(f"\nSaved {len(all_jobs)} jobs to {filename}")

        browser.close()


if __name__ == "__main__":
    main()
