import requests
import json
import time
from urllib.parse import urljoin
import pandas as pd

class KhanAcademyAPIHandler:
    def __init__(self):
        self.base_url = "https://www.khanacademy.org/api/v1/"
        self.headers = {
            "User-Agent": "KhanAcademyResearchBot/1.0",
            "Accept": "application/json"
        }
        self.api_endpoints = {
            "topics": "topic",
            "topictree": "topictree",
            "exercises": "exercises",
            "videos": "videos",
            "articles": "articles"
        }
        self.api_available = False
        self.endpoints_status = {}
        
    def check_api_availability(self):
        """Check if Khan Academy API is available"""
        try:
            print("Checking if Khan Academy API is available...")
            response = requests.get(self.base_url + '/api/v1/topictree', timeout=5)
            
            if response.status_code == 200:
                print("Khan Academy API is available!")
                api_data = {
                    "api_available": True,
                    "endpoints": {
                        "topictree": "/api/v1/topictree",
                        "playlists": "/api/v1/playlists",
                        "badges": "/api/v1/badges"
                    },
                    "rate_limit": "60 requests per minute",
                    "authentication": "API Key required"
                }
                
                # Save API status
                with open('api_status.json', 'w') as f:
                    json.dump(api_data, f, indent=2)
                
                return True
            else:
                print(f"Khan Academy API returned status code {response.status_code}")
                self._save_mock_api_status(False)
                return False
            
        except Exception as e:
            print(f"Error checking API availability: {e}")
            self._save_mock_api_status(False)
            return False

    def _save_mock_api_status(self, available=False):
        """Save mock API status data for testing"""
        print("Saving mock API status data...")
        api_data = {
            "api_available": available,
            "endpoints": {
                "topictree": "/api/v1/topictree",
                "playlists": "/api/v1/playlists",
                "badges": "/api/v1/badges"
            },
            "rate_limit": "60 requests per minute",
            "authentication": "API Key required",
            "last_check": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Save API status
        with open('api_status.json', 'w') as f:
            json.dump(api_data, f, indent=2)
        print("Saved mock API status to api_status.json")
    
    def get_topic_tree(self):
        """Get the complete topic tree from Khan Academy"""
        try:
            url = urljoin(self.base_url, self.api_endpoints["topictree"])
            response = requests.get(url, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Failed to get topic tree: {response.status_code}")
                return None
        except Exception as e:
            print(f"Error getting topic tree: {e}")
            return None
    
    def get_topic_data(self, topic_slug):
        """Get data for a specific topic"""
        try:
            url = urljoin(self.base_url, f"{self.api_endpoints['topics']}/{topic_slug}")
            response = requests.get(url, headers=self.headers, timeout=5)
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Failed to get topic data: {response.status_code}")
                return None
        except Exception as e:
            print(f"Error getting topic data: {e}")
            return None
    
    def extract_courses(self, topic_tree=None):
        """Extract course information from the topic tree"""
        if not topic_tree:
            topic_tree = self.get_topic_tree()
            
        if not topic_tree:
            return []
            
        courses = []
        
        def process_node(node, parent_path=""):
            current_path = f"{parent_path}/{node.get('slug', '')}" if parent_path else node.get('slug', '')
            
            # Check if this is a course/subject node
            if node.get('kind') == 'Topic' and node.get('slug'):
                courses.append({
                    'title': node.get('title', ''),
                    'slug': node.get('slug', ''),
                    'path': current_path,
                    'description': node.get('description', ''),
                    'child_count': len(node.get('children', [])),
                    'url': f"https://www.khanacademy.org/{current_path}"
                })
            
            # Process children recursively
            for child in node.get('children', []):
                process_node(child, current_path)
        
        # Start processing from the root
        process_node(topic_tree)
        
        return courses
    
    def get_api_status(self):
        """Get the status of all API endpoints"""
        if not self.endpoints_status:
            self.check_api_availability()
        
        return {
            "api_available": self.api_available,
            "endpoints": self.endpoints_status
        }
    
    def extract_content_to_csv(self, output_file="khan_academy_api_data.csv"):
        """Extract content from Khan Academy API and save to CSV"""
        topic_tree = self.get_topic_tree()
        
        if not topic_tree:
            print("Failed to get topic tree. Cannot extract content.")
            return False
        
        courses = self.extract_courses(topic_tree)
        
        if courses:
            df = pd.DataFrame(courses)
            df.to_csv(output_file, index=False)
            print(f"Successfully saved {len(df)} courses to {output_file}")
            return True
        else:
            print("No courses were extracted.")
            return False

if __name__ == "__main__":
    api_handler = KhanAcademyAPIHandler()
    api_status = api_handler.check_api_availability()
    
    print(f"API Available: {api_status}")
    print("Endpoint Status:")
    for endpoint, status in api_handler.endpoints_status.items():
        print(f"  - {endpoint}: {status}")
    
    if api_status:
        api_handler.extract_content_to_csv()
