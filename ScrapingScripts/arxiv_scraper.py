import requests
import feedparser
import pandas as pd
import time

def scrape_arxiv(query="machine learning", max_results=100):
    print(f"🔍 Searching arXiv for: {query}")
    base_url = "http://export.arxiv.org/api/query?"
    search_query = f"search_query=all:{query.replace(' ', '+')}&start=0&max_results={max_results}"
    response = requests.get(base_url + search_query)
    
    feed = feedparser.parse(response.text)
    papers = []
    
    for entry in feed.entries:
        papers.append({
            "Title": entry.title,
            "Authors": ", ".join(author.name for author in entry.authors),
            "Published": entry.published,
            "Summary": entry.summary.strip().replace('\n', ' '),
            "Link": entry.link,
            "PDF Link": next((l.href for l in entry.links if l.type == "application/pdf"), "N/A")
        })
    
    return papers

# Batch scrape multiple queries
queries = [
    "machine learning", "artificial intelligence", "deep learning",
    "data science", "natural language processing", "computer vision",
    "cybersecurity", "cloud computing", "blockchain", "edge computing",
    "big data", "internet of things", "robotics", "neural networks",
    "data engineering", "quantum computing", "disaster detection",
    "remote sensing", "geospatial analysis"
]

all_papers = []
for query in queries:
    papers = scrape_arxiv(query, max_results=50)
    all_papers.extend(papers)
    time.sleep(2)  

# Save to CSV
df = pd.DataFrame(all_papers)
df.to_csv("raw/arxiv_it_research.csv", index=False)
print("\n✅ Done. Saved to arxiv_it_research.csv")
