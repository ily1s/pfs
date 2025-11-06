from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import json
import re
import os
import time
from datetime import datetime

# Load environment variables from .env file if present
load_dotenv()

print(f"\nScraping completed on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


def load_skills_list():
    # Ideally load this from a file
    if not os.path.exists("skills.json"):
        print("Skills file not found!")
        return []
    with open("skills.json", "r") as f:
        skills = json.load(f)
    return skills


def extract_skills(description, skills_list):
    found_skills = []
    for skill in skills_list:
        pattern = r"\b" + re.escape(skill) + r"\b"
        if re.search(pattern, description, re.I):
            found_skills.append(skill.lower())
    return list(set(found_skills))


def login_to_linkedin(page):
    # Get LinkedIn credentials from environment variables or prompt user
    email = os.getenv("LINKEDIN_EMAIL")
    password = os.getenv("LINKEDIN_PASSWORD")

    if not email:
        email = input("Enter your LinkedIn email: ")
    if not password:
        password = input("Enter your LinkedIn password: ")

    # Navigate to LinkedIn login page
    page.goto("https://www.linkedin.com/login")
    print("Logging in to LinkedIn...")

    # Fill in login form
    page.fill("#username", email)
    page.fill("#password", password)
    page.click("button[type='submit']")

    # Wait for login to complete
    page.wait_for_timeout(5000)

    # Check if login was successful
    if "feed" in page.url or "voyager" in page.url:
        print("Login successful!")
        return True
    else:
        print("Login may have failed. Check if there are any security checks.")
        return False


def safe_click(locator, retries=3):
    for attempt in range(retries):
        try:
            locator.click()
            return True
        except Exception as e:
            print(f"Retry {attempt+1}/{retries} for click: {e}")
            time.sleep(2)
    return False


def navigate_to_linkedin_jobs(search_url, page):
    # Login
    if not login_to_linkedin(page):
        input("Resolve login issues, then press Enter to continue...")
    print("Navigating to LinkedIn jobs page...")
    page.goto(search_url)
    page.wait_for_timeout(5000)
    return page


def extract_jobs_with_bs4(page, max_jobs=10):
    html = page.content()  # the fully loaded HTML
    soup = BeautifulSoup(html, "html.parser")
    job_cards = soup.select(".job-card-container")

    jobs = []

    for i, card in enumerate(job_cards[:max_jobs]):
        # print(card.prettify())
        job_title_elem = card.select_one(
            "a.job-card-container__link span[aria-hidden = 'true']"
        )
        company_name_elem = card.select_one("div.artdeco-entity-lockup__subtitle")
        location_elem = card.select_one("ul.job-card-container__metadata-wrapper li")

        job = {
            "job_title": (
                job_title_elem.get_text(strip=True) if job_title_elem else "N/A"
            ),
            "company": (
                company_name_elem.get_text(strip=True) if company_name_elem else "N/A"
            ),
            "location": location_elem.get_text(strip=True) if location_elem else "N/A",
        }
        print(job)
        jobs.append(job)

    return jobs


def enrich_with_descriptions_and_skills(page, jobs, skills_list):
    for i in range(len(jobs)):
        # click  the i-th card
        job_cards = page.locator("div.job-card-container--clickable")
        try:
            if not safe_click(job_cards.nth(i)):
                print(f"Could not click job {i+1}")
                continue
            page.wait_for_timeout(5000)  # Let the details load

        except Exception as e:
            print(f"Could not click job {i+1}: {e}")
            continue

        # Get updated DOM
        html = page.content()
        soup = BeautifulSoup(html, "html.parser")

        company_link = soup.select_one(
            "div.job-details-jobs-unified-top-card__company-name a"
        )
        company_link = company_link.get_text(strip=True) if company_link else "N/A"
        description_elem = soup.select_one(".jobs-description__content")
        description = (
            description_elem.get_text(strip=True) if description_elem else "N/A"
        )

        jobs[i]["company_link"] = company_link
        jobs[i]["description"] = description
        jobs[i]["skills"] = extract_skills(description, skills_list)

        print(f"\n[{i+1}] {jobs[i]['job_title']} | Skills: {jobs[i]['skills']}")
    return jobs


def extract_recruiters(page, jobs, search_url):
    for i in range(len(jobs)):
        print(f"\nProcessing job {i+1} of {len(jobs)}")

        try:
            # Go back to job list (search page)
            page.goto(search_url)
            page.wait_for_timeout(5000)

            # Refresh job cards
            job_cards = page.locator("div.job-card-container--clickable")

            if not safe_click(job_cards.nth(i)):
                print(f"Could not click job {i+1}")
                continue
            page.wait_for_timeout(5000)
        except Exception as e:
            print(f"Could not click job {i+1}: {e}")
            continue

        # Click company link
        company_link = page.locator(
            "div.job-details-jobs-unified-top-card__company-name a"
        )
        try:
            if not safe_click(company_link):
                print(f"Could not click company link for job {i+1}")
                continue
            page.wait_for_timeout(5000)
        except Exception as e:
            print(f"Could not click company: {e}")
            continue

        # Click "People" tab
        people_tab = page.locator("a.org-page-navigation__item-anchor >> text=People")
        try:
            if not safe_click(people_tab):
                print(f"Could not click People tab for job {i+1}")
                continue
            page.wait_for_timeout(5000)
        except Exception as e:
            print(f"Could not click People tab: {e}")
            continue

        # Extract recruiter info from People page using BeautifulSoup
        try:
            html = page.content()
            soup = BeautifulSoup(html, "html.parser")

            people_cards = soup.select(
                "li.org-people-profile-card__profile-card-spacing"
            )
            recruiters = []

            for card in people_cards[:10]:  # Limit to 10 people
                name_tag = card.select_one("div.artdeco-entity-lockup__title")
                title_tag = card.select_one("div.artdeco-entity-lockup__subtitle")
                link_tag = card.select_one("a")

                if not name_tag or not title_tag:
                    continue

                name = name_tag.get_text(strip=True)

                title = title_tag.get_text(strip=True)

                # Skip if title is missing or not related
                if not re.search(r"recruit|talent|hr|people|human resource", title, re.I):
                    continue

                # Allow "LinkedIn Member" if title is relevant
                if name.lower() == "linkedin member":
                    name = "LinkedIn Member (hidden)"

                profile_url = None
                if link_tag and link_tag.get("href"):
                    profile_url = link_tag.get("href")
                    if profile_url.startswith("/"):
                        profile_url = "https://www.linkedin.com" + profile_url

                recruiters.append(
                    {"name": name, "title": title, "profile_url": profile_url}
                )

            if recruiters:
                jobs[i]["recruiters"] = recruiters

            print(f"✅ Found {len(recruiters)} recruiter(s) for job {i+1}")
        except Exception as e:
            print(f"❌ Error extracting recruiters for job {i+1}: {e}")
            continue
    return jobs


def scroll_job_list(page, max_scrolls=10, pause_ms=2000):
    print("Scrolling until all jobs are loaded...")
    previous_count = 0
    stuck_count = 0

    for i in range(max_scrolls):
        job_cards = page.locator("div.job-card-container--clickable")
        current_count = job_cards.count()
        print(f"🔍 Job cards before scroll {i+1}: {current_count}")

        if current_count == previous_count:
            stuck_count += 1
            if stuck_count > 2:
                print("No new jobs loaded after multiple scrolls. Stopping.")
                break
        else:
            stuck_count = 0

        try:
            job_cards.nth(current_count - 1).scroll_into_view_if_needed()
            page.wait_for_timeout(pause_ms)
        except Exception as e:
            print(f"Scroll error: {e}")
            break

        previous_count = current_count

    print(f"Final number of jobs visible: {previous_count}")


def go_to_next_page(page, current_page):
    try:
        next_button = page.locator(f"button[aria-label='Page {current_page + 1}']")
        if next_button.is_visible():
            print(f"Going to page {current_page + 1}")
            next_button.click()
            page.wait_for_timeout(5000)
            return True
        else:
            return False
    except Exception as e:
        print(f"Pagination error: {e}")
        return False


def main():
    # Configuration
    job_search_keyword = "Data"
    location = "Morocco"
    search_url = f"https://www.linkedin.com/jobs/search/?keywords={job_search_keyword.replace(' ', '%20')}&location={location.replace(' ', '%20')}"

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
        MAX_JOBS = 10

        while len(all_jobs) < MAX_JOBS:
            # scroll_job_list(page)
            raw_jobs = extract_jobs_with_bs4(page, max_jobs=MAX_JOBS)
            jobs = []
            for job in raw_jobs:
                identifier = f"{job['job_title']} @ {job['company']}"
                if identifier not in seen_jobs:
                    seen_jobs.add(identifier)
                    jobs.append(job)
            # jobs = enrich_with_descriptions_and_skills(page, jobs, skills)
            extract_recruiters(page, jobs, search_url)
            all_jobs.extend(jobs)

            # partial_filename = f"linkedin_jobs_partial_page_{current_page}.json"
            # with open(partial_filename, "w", encoding="utf-8") as f:
            #     json.dump(all_jobs, f, ensure_ascii=False, indent=2)
            # print(f"\nSaved partial data to {partial_filename}")

            if len(all_jobs) >= MAX_JOBS:
                all_jobs = all_jobs[:MAX_JOBS]  # Just in case
                break

            # if not go_to_next_page(page, current_page):
            #     break
            # current_page += 1

        print(f"Total jobs collected: {len(all_jobs)}")

        with open("linkedin_jobs.json", "w", encoding="utf-8") as f:
            json.dump(all_jobs, f, ensure_ascii=False, indent=2)
        print(f"\nSaved {len(all_jobs)} jobs to linkedin_jobs.json")

        browser.close()


if __name__ == "__main__":
    main()
