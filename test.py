import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import trafilatura
from typing import Dict, Optional
import os
from datetime import datetime

class URLScraper:
    """Handles URL scraping and content extraction"""
    
    def _init_(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.scrape_dir = "scraped_content"
        os.makedirs(self.scrape_dir, exist_ok=True)
    
    def _save_scraped_content(self, content: Dict[str, str]) -> str:
        """Save scraped content to file and return the filepath"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{content['filename']}"
        filepath = os.path.join(self.scrape_dir, filename)
        
        # Save the content with metadata
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"URL: {content.get('url', 'Direct Input')}\n")
            f.write(f"Scrape Time: {datetime.now().isoformat()}\n")
            f.write("=" * 50 + "\n\n")
            f.write(content['content'])
        
        print(f"📥 Saved scraped content to: {filepath}")
        return filepath

    def extract_content(self, url: str) -> Optional[Dict[str, str]]:
        """Extract content from a URL"""
        try:
            # Validate URL
            parsed_url = urlparse(url)
            if not all([parsed_url.scheme, parsed_url.netloc]):
                raise ValueError("Invalid URL format")
            
            print(f"🌐 Fetching content from: {url}")
            
            # Use trafilatura for main content extraction
            downloaded = trafilatura.fetch_url(url)
            if downloaded:
                content = trafilatura.extract(downloaded, include_links=True, include_tables=True)
                if content:
                    result = {
                        "filename": f"scraped_{parsed_url.netloc.replace('.', '_')}.md",
                        "content": content,
                        "url": url
                    }
                    # Save the content
                    filepath = self._save_scraped_content(result)
                    result['filepath'] = filepath
                    return result
            
            # Fallback to BeautifulSoup if trafilatura fails
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Remove unwanted elements
            for element in soup(['script', 'style', 'nav', 'footer', 'iframe']):
                element.decompose()
            
            # Extract title and main content
            title = soup.title.string if soup.title else ""
            content = " ".join([p.get_text().strip() for p in soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'])])
            
            result = {
                "filename": f"scraped_{parsed_url.netloc.replace('.', '_')}.md",
                "content": f"Title: {title}\n\n{content}",
                "url": url
            }
            # Save the content
            filepath = self._save_scraped_content(result)
            result['filepath'] = filepath
            return result
            
        except Exception as e:
            print(f"❌ Error scraping URL: {str(e)}")
            return None
    
    def is_url(self, text: str) -> bool:
        """Check if the given text is a URL"""
        try:
            result = urlparse(text)
            return all([result.scheme, result.netloc])
        except:
            return False
    
    def process_resource(self, resource: str) -> Dict[str, str]:
        """Process a resource (URL or direct content)"""
        if self.is_url(resource):
            print("📥 Processing URL...")
            result = self.extract_content(resource)
            if result:
                print("✅ URL content extracted successfully")
                return result
            else:
                print("⚠ Failed to extract URL content, treating as direct input")
        
        # If not a URL or URL extraction failed, treat as direct content
        result = {
            "filename": "direct_input.md",
            "content": resource,
            "url": None
        }
        # Save direct input as well
        filepath = self._save_scraped_content(result)
        result['filepath'] = filepath
        return result

if _name_ == "_main_":
    # Test the scraper
    scraper = URLScraper()
    test_url = "https://substack.com/home/post/p-154948998?utm_campaign=post&utm_medium=web"  # Replace with a test URL
    result = scraper.process_resource(test_url)
    print("\nExtracted Content:")
    print(f"Filename: {result['filename']}")
    print(f"Content Length: {len(result['content'])} characters")
    print(f"First 200 characters: {result['content'][:200]}...")