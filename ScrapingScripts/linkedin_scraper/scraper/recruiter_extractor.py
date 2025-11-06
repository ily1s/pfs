from bs4 import BeautifulSoup
from scraper import safe_click
import re


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
                if not re.search(
                    r"recruit|talent|hr|people|human resource", title, re.I
                ):
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
