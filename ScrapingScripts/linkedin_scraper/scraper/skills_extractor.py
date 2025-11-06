from bs4 import BeautifulSoup
from scraper import safe_click, extract_skills


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

        # company_link = soup.select_one(
        #     "div.job-details-jobs-unified-top-card__company-name a"
        # )
        # company_link = company_link.get_text(strip=True) if company_link else "N/A"
        description_elem = soup.select_one(".jobs-description__content")
        description = (
            description_elem.get_text(strip=True) if description_elem else "N/A"
        )

        # jobs[i]["company_link"] = company_link
        jobs[i]["description"] = description
        jobs[i]["skills"] = extract_skills(description, skills_list)

        print(f"\n[{i+1}] {jobs[i]['job_title']} | Skills: {jobs[i]['skills']}")
    return jobs
