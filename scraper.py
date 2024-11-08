import requests
from bs4 import BeautifulSoup
import time
from fake_useragent import UserAgent
import logging
from datetime import datetime
import os
import random

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class ProductHuntScraper:
    def __init__(self):
        self.ua = UserAgent()
        self.request_delay = 3
        # Add max retries and backoff delay
        self.max_retries = 3
        self.backoff_factor = 2
        
    def _get_headers(self):
        # Add more headers to look more like a real browser
        return {
            'User-Agent': self.ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0'
        }
    
    def scrape_products(self):
        url = 'https://www.producthunt.com'
        retry_count = 0
        
        while retry_count < self.max_retries:
            try:
                # Add randomized delay between 2-5 seconds
                delay = self.request_delay + random.uniform(-1, 2)
                time.sleep(delay)
                
                response = requests.get(url, headers=self._get_headers(), timeout=10)
                logging.info(f"Response status code: {response.status_code}")  # Debug log
                
                # Check for rate limiting response codes
                if response.status_code in [429, 403]:
                    retry_delay = self.backoff_factor ** retry_count
                    logging.warning(f"Rate limited. Waiting {retry_delay} seconds before retry.")
                    time.sleep(retry_delay)
                    retry_count += 1
                    continue
                    
                response.raise_for_status()
                
                # Force UTF-8 encoding
                response.encoding = 'utf-8'
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Debug log for HTML content
                logging.debug(f"HTML content length: {len(response.text)}")
                
                # Try multiple selector patterns for product items
                product_items = []
                selectors = [
                    'div[class*="styles_item"]',  # New Product Hunt class pattern
                    'div[class*="item_"]',        # Alternative class pattern
                    'div[data-test="product-item"]',
                    'article[class*="item"]',
                    'div[class*="product-item"]'
                ]
                
                for selector in selectors:
                    product_items = soup.select(selector)
                    if product_items:
                        logging.info(f"Found {len(product_items)} products using selector: {selector}")
                        break
                
                if not product_items:
                    logging.warning("No product items found with any selector")
                    # Save HTML for debugging
                    with open('debug_output.html', 'w', encoding='utf-8') as f:
                        f.write(soup.prettify())
                    logging.info("Saved HTML to debug_output.html for inspection")
                    raise Exception("Could not find product items with any selector")
                
                products = []
                for item in product_items[:5]:
                    try:
                        # Updated selectors for product details
                        name = (
                            item.select_one('h2, h3, [class*="title"], [class*="name"]') or
                            item.select_one('a[class*="title"], a[class*="name"]')
                        )
                        description = (
                            item.select_one('div[class*="tagline"], div[class*="description"], p') or
                            item.select_one('[class*="tagline"], [class*="description"]')
                        )
                        votes = (
                            item.select_one('[class*="vote"], [class*="upvote"]') or
                            item.select_one('button[class*="vote"]')
                        )
                        link_element = (
                            item.select_one('a[href*="/posts/"]') or
                            item.select_one('a[class*="link"]')
                        )
                        
                        if not all([name, description, votes, link_element]):
                            missing = []
                            if not name: missing.append('name')
                            if not description: missing.append('description')
                            if not votes: missing.append('votes')
                            if not link_element: missing.append('link')
                            logging.warning(f"Missing elements: {', '.join(missing)}")
                            continue
                        
                        product = {
                            'name': name.text.strip(),
                            'description': description.text.strip(),
                            'votes': votes.text.strip(),
                            'url': f"https://www.producthunt.com{link_element['href']}" if link_element['href'].startswith('/') else link_element['href'],
                            'scraped_at': datetime.now().isoformat()
                        }
                        products.append(product)
                        logging.info(f"Successfully scraped product: {product['name']}")
                    
                    except Exception as e:
                        logging.error(f"Error processing product item: {str(e)}")
                        continue
                
                if products:
                    logging.info(f"Successfully scraped {len(products)} products from Product Hunt")
                    return {"status": "success", "data": products}
                else:
                    raise Exception("No products could be scraped")
                
            except Exception as e:
                logging.error(f"Error scraping Product Hunt: {str(e)}")
                retry_count += 1
                if retry_count >= self.max_retries:
                    return {"status": "error", "message": str(e)}
                logging.info(f"Retrying... Attempt {retry_count + 1} of {self.max_retries}")

def main():
    scraper = ProductHuntScraper()
    result = scraper.scrape_products()
    if result["status"] == "success":
        # Print the scraped products in a readable format
        print("\nTop 5 Products from Product Hunt:")
        for idx, product in enumerate(result["data"], 1):
            print(f"\n{idx}. {product['name']}")
            print(f"   Votes: {product['votes']}")
            print(f"   Description: {product['description']}")
            print(f"   URL: {product['url']}")
    else:
        print(f"Error: {result['message']}")

if __name__ == "__main__":
    main()
