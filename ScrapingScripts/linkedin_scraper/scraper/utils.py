import json
import re
import os
import time


def load_skills_list():
    # Ideally load this from a file
    if not os.path.exists("linkedin_scraper/data/skills.json"):
        print("Skills file not found!")
        return []
    with open("linkedin_scraper/data/skills.json", "r") as f:
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


