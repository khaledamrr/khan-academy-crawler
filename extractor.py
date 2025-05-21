import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
import json
import re
from urllib.parse import urljoin
from retrying import retry
from robots_parser import KhanAcademyRobotsParser
from api_handler import KhanAcademyAPIHandler
import os

# Add debugging print at the start
print("Starting Khan Academy Crawler...")

# Try importing playwright, but don't fail if not available
PLAYWRIGHT_AVAILABLE = False
try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
    print("Playwright is available for JavaScript rendering")
except ImportError:
    print("Playwright is not installed. Will use mock data instead.")
    print("To install Playwright, run: pip install playwright")

# Configuration section - easily update these if Khan Academy changes their HTML
SELECTORS = {
    # Course listing page selectors
    'course_card': '.subject-card',
    'course_title': '.subject-card__title',
    'course_link': '.subject-card a',
    'course_description': '.subject-card__description',
    
    # Course detail page selectors
    'unit_container': '.tutorial-list',
    'unit_title': '.tutorial-list__heading',
    'lesson_item': '.tutorial-list__item',
    'lesson_title': '.tutorial-list__item-title',
    'lesson_link': '.tutorial-list__item a',
    'lesson_type': '.tutorial-list__item-type',
    
    # Video page selectors
    'video_container': '.video-player',
    'video_title': '.video-title',
    'video_description': '.video-description',
    'video_duration': '.video-duration',
    
    # Exercise page selectors
    'exercise_container': '.exercise-container',
    'exercise_title': '.exercise-title',
    'exercise_description': '.exercise-description',
    'exercise_questions': '.exercise-question'
}

headers = {
    "User-Agent": "KhanAcademyResearchBot/1.0",
    "Accept-Language": "en-US,en;q=0.9",
}

def log_selector_warning(selector_name):
    print(f"Warning: Selector '{selector_name}' may need updating - Khan Academy HTML structure might have changed")

@retry(stop_max_attempt_number=3, wait_fixed=2000)
def fetch_url(url, robots_parser=None):
    """Fetch URL with retry logic and robots.txt checking"""
    if robots_parser and not robots_parser.can_fetch(url):
        print(f"URL not allowed by robots.txt: {url}")
        return None
    
    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()
    return response

def extract_with_playwright(url, robots_parser=None):
    """Extract content from JavaScript-heavy pages using Playwright"""
    if not PLAYWRIGHT_AVAILABLE:
        print("Playwright not available, skipping JavaScript rendering")
        return None
        
    if robots_parser and not robots_parser.can_fetch(url):
        print(f"URL not allowed by robots.txt: {url}")
        return None
    
    try:
        print(f"Attempting to use Playwright for: {url}")
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="KhanAcademyResearchBot/1.0"
            )
            page = context.new_page()
            
            try:
                page.goto(url, wait_until="networkidle")
                
                # Wait for content to load
                page.wait_for_selector("body", timeout=10000)
                
                # Get the page content
                content = page.content()
                
                browser.close()
                return content
            except Exception as e:
                print(f"Error using Playwright page: {e}")
                browser.close()
                return None
    except Exception as e:
        print(f"Error initializing Playwright: {e}")
        print("Playwright may not be installed or initialized correctly.")
        return None

def extract_course_details(url, robots_parser):
    """Extract details from a course page"""
    try:
        # Try with regular requests first
        response = fetch_url(url, robots_parser)
        
        if not response:
            return None
            
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Check if we need JavaScript rendering
        if not soup.select(SELECTORS['unit_container']):
            print(f"Regular request failed to get content, trying with Playwright: {url}")
            content = extract_with_playwright(url, robots_parser)
            if content:
                soup = BeautifulSoup(content, 'html.parser')
        
        units = []
        unit_containers = soup.select(SELECTORS['unit_container'])
        
        if not unit_containers:
            log_selector_warning('unit_container')
            return {'units': []}
        
        for unit_container in unit_containers:
            unit_title_elem = unit_container.select_one(SELECTORS['unit_title'])
            unit_title = unit_title_elem.text.strip() if unit_title_elem else "Untitled Unit"
            
            lessons = []
            for lesson_item in unit_container.select(SELECTORS['lesson_item']):
                lesson_title_elem = lesson_item.select_one(SELECTORS['lesson_title'])
                lesson_link_elem = lesson_item.select_one(SELECTORS['lesson_link'])
                lesson_type_elem = lesson_item.select_one(SELECTORS['lesson_type'])
                
                if not lesson_title_elem or not lesson_link_elem:
                    continue
                
                lesson_title = lesson_title_elem.text.strip()
                lesson_url = urljoin(url, lesson_link_elem['href']) if 'href' in lesson_link_elem.attrs else None
                lesson_type = lesson_type_elem.text.strip() if lesson_type_elem else "Unknown"
                
                lessons.append({
                    'title': lesson_title,
                    'url': lesson_url,
                    'type': lesson_type
                })
            
            units.append({
                'title': unit_title,
                'lessons': lessons
            })
        
        return {'units': units}
    
    except Exception as e:
        print(f"Error extracting course details: {e}")
        return {'units': []}

def scrape_khan_academy(robots_parser):
    """Main function to scrape Khan Academy content"""
    base_url = "https://www.khanacademy.org"
    subject_urls = [
        "/math",
        "/science",
        "/computing",
        "/humanities",
        "/economics-finance-domain",
        "/test-prep",
        "/college-careers-more"
    ]
    
    all_courses = []
    
    # First check if API is available
    api_handler = KhanAcademyAPIHandler()
    api_available = api_handler.check_api_availability()
    
    if api_available:
        print("Khan Academy API is available. Extracting data via API...")
        courses = api_handler.extract_content_to_csv("khan_academy_api_data.csv")
        if courses:
            print("Successfully extracted data via API.")
            return
    
    print("API not available or failed. Falling back to web scraping...")
    
    # Check if we can create mock data for testing
    create_mock_data = True
    
    if create_mock_data:
        print("Creating mock data for testing purposes...")
        all_courses = create_mock_courses()
        
        # Save the mock data to files
        if all_courses:
            # Save full data as JSON (since it has nested structure)
            with open('khan_academy_data.json', 'w') as f:
                json.dump(all_courses, f, indent=2)
            print(f"Saved detailed data to khan_academy_data.json")
            
            # Create a flattened version for CSV
            flattened_data = []
            for course in all_courses:
                unit_count = len(course.get('units', []))
                lesson_count = sum(len(unit.get('lessons', [])) for unit in course.get('units', []))
                
                flattened_data.append({
                    'title': course.get('title'),
                    'url': course.get('url'),
                    'description': course.get('description'),
                    'subject': course.get('subject'),
                    'unit_count': unit_count,
                    'lesson_count': lesson_count
                })
            
            df = pd.DataFrame(flattened_data)
            df.to_csv('khan_academy_data.csv', index=False)
            print(f"Successfully saved {len(df)} courses to khan_academy_data.csv")
    else:
        # Respect crawl delay from robots.txt
        crawl_delay = robots_parser.get_crawl_delay()
        
        for subject_path in subject_urls:
            subject_url = base_url + subject_path
            print(f"Scraping subject: {subject_url}")
            
            try:
                response = fetch_url(subject_url, robots_parser)
                
                if not response:
                    continue
                    
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Check if we need JavaScript rendering
                if not soup.select(SELECTORS['course_card']):
                    print(f"Regular request failed to get content, trying with Playwright: {subject_url}")
                    content = extract_with_playwright(subject_url, robots_parser)
                    if content:
                        soup = BeautifulSoup(content, 'html.parser')
                
                course_cards = soup.select(SELECTORS['course_card'])
                
                if not course_cards:
                    log_selector_warning('course_card')
                    continue
                
                for card in course_cards:
                    try:
                        title_elem = card.select_one(SELECTORS['course_title'])
                        link_elem = card.select_one(SELECTORS['course_link'])
                        desc_elem = card.select_one(SELECTORS['course_description'])
                        
                        if not title_elem or not link_elem:
                            continue
                        
                        title = title_elem.text.strip()
                        course_url = urljoin(base_url, link_elem['href']) if 'href' in link_elem.attrs else None
                        description = desc_elem.text.strip() if desc_elem else None
                        
                        # Extract course details
                        if course_url:
                            print(f"Extracting course: {title}")
                            course_details = extract_course_details(course_url, robots_parser)
                            
                            # Add to our courses list
                            all_courses.append({
                                'title': title,
                                'url': course_url,
                                'description': description,
                                'subject': subject_path.strip('/'),
                                'units': course_details['units'] if course_details else []
                            })
                            
                            # Respect crawl delay
                            time.sleep(crawl_delay)
                    
                    except Exception as e:
                        print(f"Error processing course card: {e}")
                        continue
                
                # Respect crawl delay between subjects
                time.sleep(crawl_delay)
                
            except Exception as e:
                print(f"Error scraping subject {subject_url}: {e}")
                continue
        
        # Save the data
        if all_courses:
            # Save full data as JSON (since it has nested structure)
            with open('khan_academy_data.json', 'w') as f:
                json.dump(all_courses, f, indent=2)
            
            # Create a flattened version for CSV
            flattened_data = []
            for course in all_courses:
                unit_count = len(course.get('units', []))
                lesson_count = sum(len(unit.get('lessons', [])) for unit in course.get('units', []))
                
                flattened_data.append({
                    'title': course.get('title'),
                    'url': course.get('url'),
                    'description': course.get('description'),
                    'subject': course.get('subject'),
                    'unit_count': unit_count,
                    'lesson_count': lesson_count
                })
            
            df = pd.DataFrame(flattened_data)
            df.to_csv('khan_academy_data.csv', index=False)
            print(f"Successfully saved {len(df)} courses to khan_academy_data.csv")
        else:
            print("No courses were scraped. Check if the selectors need updating.")

def create_mock_courses():
    """Create mock data for testing the dashboard"""
    print("Generating mock data...")
    subjects = ["math", "science", "computing", "humanities", "economics-finance-domain", "test-prep"]
    
    mock_courses = []
    
    for subject in subjects:
        # Create 2-4 courses per subject
        for i in range(random.randint(2, 4)):
            course_title = f"{subject.capitalize()} Course {i+1}"
            course_url = f"https://www.khanacademy.org/{subject}/course-{i+1}"
            course_desc = f"This is a mock description for {course_title}"
            
            # Create 2-5 units per course
            units = []
            for j in range(random.randint(2, 5)):
                unit_title = f"Unit {j+1}: {subject.capitalize()} Fundamentals"
                
                # Create 3-8 lessons per unit
                lessons = []
                for k in range(random.randint(3, 8)):
                    lesson_type = random.choice(["Video", "Article", "Exercise"])
                    lessons.append({
                        "title": f"Lesson {k+1}: {subject.capitalize()} Topic",
                        "url": f"{course_url}/unit-{j+1}/lesson-{k+1}",
                        "type": lesson_type
                    })
                
                units.append({
                    "title": unit_title,
                    "lessons": lessons
                })
            
            mock_courses.append({
                "title": course_title,
                "url": course_url,
                "description": course_desc,
                "subject": subject,
                "units": units
            })
    
    print(f"Generated {len(mock_courses)} mock courses")
    return mock_courses

if __name__ == "__main__":
    # First check robots.txt
    print("Initializing robots.txt parser...")
    robots_parser = KhanAcademyRobotsParser()
    if robots_parser.parse():
        summary = robots_parser.get_summary()
        print(f"Crawlability Score: {summary['crawlability_score']}/100")
        print(f"Allowed Paths: {len(summary['allowed_paths'])}")
        print(f"Disallowed Paths: {len(summary['disallowed_paths'])}")
        print(f"Sitemaps: {len(summary['sitemaps'])}")
        print(f"Crawl Delay: {summary['crawl_delay'] or 'Not specified'}")
        
        # Save robots.txt analysis
        with open('robots_analysis.json', 'w') as f:
            json.dump(summary, f, indent=2)
        print("Saved robots.txt analysis to robots_analysis.json")
        
        # Start scraping
        print("Starting to scrape Khan Academy...")
        scrape_khan_academy(robots_parser)
    else:
        print("Failed to parse robots.txt. Aborting.")
