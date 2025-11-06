from bs4 import BeautifulSoup


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
