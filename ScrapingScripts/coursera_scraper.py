import requests
from bs4 import BeautifulSoup
import pandas as pd
import time

BASE_URL = 'https://www.coursera.org/courses'
HEADERS = {'User-Agent': 'Mozilla/5.0'}

def extract_course_info(card):
    try:
        title = card.select_one('h3[class*="cds-CommonCard-title"]')
        provider = card.select_one('div.cds-ProductCard-content p.css-vac8rf')  
        skills = card.select_one('div.cds-ProductCard-body p.css-vac8rf')
        rating_tag = card.select_one('div.cds-ProductCard-footer span.css-6ecy9b')
        reviews_tag = card.select_one('div.cds-ProductCard-footer div.css-vac8rf')
        meta = card.select_one('div.cds-CommonCard-metadata p.css-vac8rf')
        link_tag = card.select_one('a[href*="/"]')
        image = card.select_one('div.cds-ProductCard-gridPreviewContainer img')

        return {
            'Title': title.get_text(strip=True) if title else "N/A",
            'Provider': provider.get_text(strip=True) if provider else "N/A",
            'Skills': skills.get_text(strip=True).replace("Skills you'll gain:", "").strip() if skills else "N/A",
            'Rating': rating_tag.get_text(strip=True) if rating_tag else "N/A",
            'Reviews': reviews_tag.get_text(strip=True) if reviews_tag else "N/A",
            'Details': meta.get_text(strip=True) if meta else "N/A",
            'Course Link': f"https://www.coursera.org{link_tag['href']}" if link_tag else "N/A",
            'Image URL': image['src'] if image else "N/A",
        }
    except Exception as e:
        print("⚠️  Error extracting course info:", e)
        return None

def scrape_courses(max_pages=3):
    all_courses = []
    for page in range(1, max_pages + 1):
        print(f"\n🔍 Scraping page {page}...")
        url = f"{BASE_URL}?page={page}"
        response = requests.get(url, headers=HEADERS)
        if response.status_code != 200:
            print(f"❌ Failed to load page {page}, status code: {response.status_code}")
            continue

        soup = BeautifulSoup(response.text, 'html.parser')
        course_cards = soup.select('li[class*="cds-"]')
        print(f"📦 Found {len(course_cards)} course cards")

        if not course_cards:
            break

        for card in course_cards:
            info = extract_course_info(card)
            if info and info['Title'] != "N/A":
                all_courses.append(info)

        time.sleep(1)

    return all_courses

# Run & save
courses = scrape_courses(max_pages=84)
df = pd.DataFrame(courses)
df.to_csv("raw/coursera_courses_detailed.csv", index=False)
print("\n✅ Done. Saved to coursera_courses_detailed.csv")
