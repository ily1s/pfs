# scraper/__init__.py

# Expose key modules at package level:
from .utils import (
    safe_click,
    login_to_linkedin,
    load_skills_list,
    navigate_to_linkedin_jobs,
    extract_skills,
    scroll_job_list,
    go_to_next_page,
)
from .job_scraper import extract_jobs_with_bs4
from .skills_extractor import enrich_with_descriptions_and_skills
from .recruiter_extractor import extract_recruiters

__all__ = [
    "safe_click",
    "login_to_linkedin",
    "load_skills_list",
    "navigate_to_linkedin_jobs",
    "extract_jobs_with_bs4",
    "enrich_with_descriptions_and_skills",
    "open_company_people_tab",
    "extract_recruiters",
    "extract_skills",
    "scroll_job_list",
    "go_to_next_page",
]


"""In Python, an __init__.py file inside a folder tells the interpreter “this directory is a package.” Here’s what it does for you:

Turns a folder into a package
Without __init__.py, you can’t do import scraper.job_scraper. The file (even if empty) signals “scraper” is a Python package.

Controls what’s exported
You can define an __all__ list in __init__.py to specify which modules get imported when someone does from scraper import *.

Package‑level setup
If you need package‑wide initialization (e.g. setting up logging, loading shared config), you can put that code here."""
