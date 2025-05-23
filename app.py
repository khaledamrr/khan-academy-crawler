import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import json
import os
import plotly.express as px
import plotly.graph_objects as go
import networkx as nx
from PIL import Image
import numpy as np
import seaborn as sns

# Configure page
st.set_page_config(
    page_title="Khan Academy Crawler Dashboard",
    layout="wide",
    page_icon="🧠"
)

# Title and description
st.title("🧠 Khan Academy Web Crawler Dashboard")
st.markdown("A dashboard to visualize Khan Academy's crawlability score, extracted educational content, and crawling recommendations.")

# Sidebar
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Overview", "Crawlability Analysis", "Content Extraction", "API Analysis", "Recommendations"])

# Load data
@st.cache_data
def load_data():
    data = {
        "courses": pd.DataFrame(),
        "robots_analysis": {},
        "api_status": {}
    }
    
    try:
        if os.path.exists('khan_academy_data.csv'):
            data["courses"] = pd.read_csv('khan_academy_data.csv')
        
        if os.path.exists('robots_analysis.json'):
            with open('robots_analysis.json', 'r') as f:
                data["robots_analysis"] = json.load(f)
        
        if os.path.exists('api_status.json'):
            with open('api_status.json', 'r') as f:
                data["api_status"] = json.load(f)
        
        return data
    except Exception as e:
        st.error("Error loading data. Make sure the data files exist.")
        st.exception(e)
        return data

data = load_data()

# Overview Page
if page == "Overview":
    st.header("📊 Project Overview")
    
    # Project metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Crawlability Score", f"{data['robots_analysis'].get('crawlability_score', 0)}/100")
    
    with col2:
        st.metric("Courses Extracted", len(data["courses"]))
    
    with col3:
        if not data["courses"].empty:
            total_lessons = data["courses"]["lesson_count"].sum()
            st.metric("Total Lessons", total_lessons)
        else:
            st.metric("Total Lessons", "0")
    
    with col4:
        api_available = data["api_status"].get("api_available", False)
        st.metric("API Available", "Yes" if api_available else "No")
    
    # Project description
    st.subheader("Project Description")
    st.markdown("""
    This dashboard presents the results of our Khan Academy web crawler project. The project analyzes Khan Academy's website structure, extracts educational content, and provides insights on the best approaches to access its data.
    
    The project is divided into several components:
    - **Crawlability Analysis**: Analyzes robots.txt and provides a crawlability score
    - **Content Extraction**: Extracts courses, units, and lessons from Khan Academy
    - **API Analysis**: Checks for available APIs and their endpoints
    - **Recommendations**: Provides recommendations for the best approach to access Khan Academy data
    """)
    
    # Team members
    st.subheader("👥 Team Members")
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        - **Khaled Amr**: Crawlability Specialist
        - **Omar Samh**: Content Extractor
        - **Mohamed Hossam**: JS & API Handler
        """)
    
    with col2:
        st.markdown("""
        - **Abdelrahman Shokry**: Visual & Report Designer
        - **Emad Wael**: Documentation & Deployment
        """)
    
    # Show a preview of the data
    if not data["courses"].empty:
        st.subheader("📚 Extracted Courses Preview")
        st.dataframe(data["courses"].head())

# Crawlability Analysis Page
elif page == "Crawlability Analysis":
    st.header("🛡️ Crawlability Analysis")
    
    # Crawlability score
    st.subheader("Crawlability Score")
    score = data["robots_analysis"].get("crawlability_score", 0)
    st.progress(score/100)
    st.write(f"Score: {score}/100")
    
    # Score explanation
    st.markdown("""
    The crawlability score is calculated based on:
    - Presence of robots.txt
    - Availability of sitemaps
    - Ratio of allowed vs. disallowed paths
    - Crawl delay settings
    """)
    
    # Robots.txt details
    st.subheader("Robots.txt Details")
    
    col1, col2 = st.columns(2)
    
    with col1:
        allowed_paths = data["robots_analysis"].get("allowed_paths", [])
        st.markdown(f"""
        <div style="text-align: center; margin-bottom: 20px;">
            <h3 style="color: #4CAF50;">Crawler Access Rules</h3>
            <p style="color: #666; font-size: 12px;">
                Note: These rules only apply to web crawlers/bots. Regular users can access all public content normally.
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; margin-bottom: 20px;">
            <h4 style="color: #4CAF50; margin-bottom: 10px;">Allowed for Crawlers</h4>
            <p style="color: #666; font-size: 13px;">
                No specific paths are explicitly allowed for crawlers. This means crawlers should only access paths that are not explicitly disallowed.
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        disallowed_paths = data["robots_analysis"].get("disallowed_paths", [])
        
        # Create categories for disallowed paths with icons
        categories = {
            "🔒 Core": [],
            "👤 Auth": [],
            "🧪 Labs": [],
            "🤖 Khanmigo": [],
            "🔧 Test": [],
            "📁 Other": []
        }
        
        # Categorize the paths
        for path in disallowed_paths:
            if path in ["/", "/_ah/", "/admin/", "/api/internal/_bb/", "/crash", "/devadmin/"]:
                categories["🔒 Core"].append(path)
            elif "login" in path or "postlogin" in path or "settings" in path:
                categories["👤 Auth"].append(path)
            elif "khan-labs" in path:
                categories["🧪 Labs"].append(path)
            elif "khanmigo" in path:
                categories["🤖 Khanmigo"].append(path)
            elif "test" in path or "qa" in path or "preview" in path:
                categories["🔧 Test"].append(path)
            else:
                categories["📁 Other"].append(path)
        
        # Unique striking design
        st.markdown("""
        <style>
        .striking-container {
            background: #1a1a1a;
            border-radius: 0;
            padding: 15px;
            color: #fff;
        }
        .striking-title {
            text-align: center;
            font-size: 16px;
            font-weight: bold;
            color: #ff4b4b;
            text-transform: uppercase;
            letter-spacing: 2px;
            margin-bottom: 20px;
            padding: 10px;
            border: 2px solid #ff4b4b;
            background: rgba(255, 75, 75, 0.1);
        }
        .striking-subtitle {
            text-align: center;
            font-size: 12px;
            color: #ccc;
            margin-bottom: 20px;
            font-style: italic;
        }
        .category-section {
            margin: 15px 0;
            border-left: 3px solid #ff4b4b;
            padding-left: 10px;
        }
        .category-label {
            display: inline-block;
            background: #ff4b4b;
            color: white;
            padding: 2px 8px;
            font-size: 12px;
            margin-bottom: 5px;
        }
        .path-list {
            margin-left: 10px;
        }
        .path-item {
            font-family: 'Courier New', monospace;
            font-size: 11px;
            color: #ccc;
            padding: 2px 0;
            position: relative;
            padding-left: 15px;
        }
        .path-item:before {
            content: ">";
            position: absolute;
            left: 0;
            color: #ff4b4b;
        }
        .path-item:hover {
            color: #ff4b4b;
            background: rgba(255, 75, 75, 0.1);
        }
        </style>
        """, unsafe_allow_html=True)
        
        st.markdown(f"""
        <div class="striking-container">
            <div class="striking-title">Restricted for Crawlers</div>
            <div class="striking-subtitle">These paths are restricted for automated crawlers only. Regular users can access all public content.</div>
        """, unsafe_allow_html=True)
        
        for category, paths in categories.items():
            if paths:
                st.markdown(f"""
                <div class="category-section">
                    <div class="category-label">{category}</div>
                    <div class="path-list">
                """, unsafe_allow_html=True)
                
                for path in paths:
                    st.markdown(f"""
                    <div class="path-item" title="{path}">{path}</div>
                    """, unsafe_allow_html=True)
                
                st.markdown("</div></div>", unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Crawl delay
    crawl_delay = data["robots_analysis"].get("crawl_delay", "Not specified")
    st.write(f"**Crawl Delay:** {crawl_delay} seconds" if crawl_delay else "**Crawl Delay:** Not specified")
    
    # Sitemaps
    sitemaps = data["robots_analysis"].get("sitemaps", [])
    st.write(f"**Sitemaps:** {len(sitemaps)}")
    if sitemaps:
        with st.expander("View Sitemaps"):
            for sitemap in sitemaps:
                st.write(f"- {sitemap}")

# Content Extraction Page
elif page == "Content Extraction":
    st.header("📚 Content Extraction")
    
    if data["courses"].empty:
        st.warning("No course data available. Please run the extractor first.")
    else:
        # Course statistics
        st.subheader("Course Statistics")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Courses", len(data["courses"]))
        
        with col2:
            total_units = data["courses"]["unit_count"].sum()
            st.metric("Total Units", total_units)
        
        with col3:
            total_lessons = data["courses"]["lesson_count"].sum()
            st.metric("Total Lessons", total_lessons)
        
        # Visualization: Courses by Subject
        st.subheader("Courses by Subject")
        
        subject_counts = data["courses"]["subject"].value_counts().reset_index()
        subject_counts.columns = ["Subject", "Count"]
        
        fig = px.bar(
            subject_counts,
            x="Subject",
            y="Count",
            color="Subject",
            title="Number of Courses by Subject"
        )
        st.plotly_chart(fig)
        
        # Visualization: Units and Lessons per Course
        st.subheader("Units and Lessons per Course")
        
        # Create a sample of courses (top 10 by lesson count) to avoid overcrowding
        top_courses = data["courses"].sort_values("lesson_count", ascending=False).head(10)
        
        fig = px.bar(
            top_courses,
            x="title",
            y=["unit_count", "lesson_count"],
            barmode="group",
            title="Units and Lessons in Top 10 Courses",
            labels={"value": "Count", "variable": "Type", "title": "Course"}
        )
        fig.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig)
        
        # Course details
        st.subheader("Course Details")
        
        selected_subject = st.selectbox("Select Subject", ["All"] + list(data["courses"]["subject"].unique()))
        
        filtered_courses = data["courses"]
        if selected_subject != "All":
            filtered_courses = data["courses"][data["courses"]["subject"] == selected_subject]
        
        st.dataframe(filtered_courses)

# API Analysis Page
elif page == "API Analysis":
    st.header("🔌 API Analysis")
    
    api_available = data["api_status"].get("api_available", False)
    
    if api_available:
        st.success("Khan Academy API is available!")
        
        # API endpoints
        st.subheader("API Endpoints")
        
        endpoints = data["api_status"].get("endpoints", {})
        
        for endpoint, status in endpoints.items():
            if status == "Available":
                st.write(f"✅ **{endpoint}**: {status}")
            else:
                st.write(f"❌ **{endpoint}**: {status}")
        
        # API usage example
        st.subheader("API Usage Example")
        
        st.code("""
import requests

# Example: Get topic tree
response = requests.get(
    "https://www.khanacademy.org/api/v1/topictree",
    headers={"User-Agent": "YourAppName/1.0"}
)

if response.status_code == 200:
    topic_tree = response.json()
    # Process the topic tree...
        """, language="python")
        
    else:
        st.warning("Khan Academy API is not available or could not be accessed.")
        
        st.markdown("""
        ### Alternative Approaches
        
        Since the API is not available, we recommend:
        
        1. **Web Scraping with Playwright**: For JavaScript-heavy pages
        2. **BeautifulSoup Parsing**: For static content
        3. **RSS Feeds**: Check if Khan Academy provides RSS feeds for content updates
        """)
    
    # JavaScript analysis
    st.subheader("JavaScript Analysis")
    
    st.markdown("""
    Khan Academy's website is JavaScript-heavy, using React for rendering most of the content. This means:
    
    - Many pages require JavaScript to load content
    - Simple requests with `requests` library may not work
    - Playwright or Selenium is needed for complete content extraction
    """)
    
    # Playwright example
    st.subheader("Playwright Implementation")
    
    st.code("""
from playwright.sync_api import sync_playwright

def extract_with_playwright(url):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="YourCrawler/1.0"
        )
        page = context.new_page()
        
        try:
            page.goto(url, wait_until="networkidle")
            
            # Wait for content to load
            page.wait_for_selector(".tutorial-list", timeout=10000)
            
            # Extract data
            course_title = page.query_selector("h1").inner_text()
            
            # Get all lessons
            lessons = []
            for lesson_elem in page.query_selector_all(".tutorial-list__item"):
                title = lesson_elem.query_selector(".tutorial-list__item-title").inner_text()
                lessons.append(title)
            
            browser.close()
            return {"title": course_title, "lessons": lessons}
        except Exception as e:
            print(f"Error: {e}")
            browser.close()
            return None
    """, language="python")

# Recommendations Page
elif page == "Recommendations":
    st.header("💡 Recommendations")
    
    # Crawlability recommendations
    st.subheader("Crawlability Recommendations")
    
    crawl_delay = data["robots_analysis"].get("crawl_delay", None)
    
    recommendations = [
        "Always check robots.txt before crawling Khan Academy",
        f"Respect the crawl delay of {crawl_delay} seconds" if crawl_delay else "Implement a reasonable crawl delay (1-2 seconds)",
        "Use the sitemap for more efficient crawling",
        "Avoid crawling disallowed paths"
    ]
    
    for rec in recommendations:
        st.markdown(f"- {rec}")
    
    # Content extraction recommendations
    st.subheader("Content Extraction Recommendations")
    
    api_available = data["api_status"].get("api_available", False)
    
    if api_available:
        st.markdown("""
        - **Use the API**: The Khan Academy API is available and provides structured data
        - **Combine API with web scraping**: For content not available through the API
        - **Cache API responses**: To reduce load on Khan Academy servers
        """)
    else:
        st.markdown("""
        - **Use Playwright/Selenium**: Khan Academy is JavaScript-heavy, requiring browser automation
        - **Implement robust error handling**: Pages may change structure or fail to load
        - **Use a modular approach**: Separate crawling logic from parsing logic
        """)
    
    # Best practices
    st.subheader("Best Practices")
    
    st.markdown("""
    - **Identify your crawler**: Use a descriptive User-Agent
    - **Implement rate limiting**: Avoid overloading Khan Academy servers
    - **Store data efficiently**: Use appropriate data structures for educational content
    - **Update selectors regularly**: Khan Academy may change its HTML structure
    - **Monitor for changes**: Set up alerts for when crawling fails
    """)
    
    # Technical architecture
    st.subheader("Recommended Technical Architecture")
    
    st.markdown("""
    ### Crawling Components
    
    1. **Robots.txt Parser**: Check crawling permissions
    2. **API Handler**: Try API first if available
    3. **Playwright Crawler**: For JavaScript-heavy pages
    4. **BeautifulSoup Parser**: For static content
    5. **Data Storage**: CSV/JSON for simple storage
    """)

# Footer
st.markdown("---")
st.markdown("Khan Academy Web Crawler Project | Created for educational purposes only")
