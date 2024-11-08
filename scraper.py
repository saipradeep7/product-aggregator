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
                
                # Check for rate limiting response codes
                if response.status_code in [429, 403]:
                    retry_delay = self.backoff_factor ** retry_count
                    logging.warning(f"Rate limited. Waiting {retry_delay} seconds before retry.")
                    time.sleep(retry_delay)
                    retry_count += 1
                    continue
                    
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, 'html.parser')
                products = []
                
                # Find product cards on the homepage
                product_items = soup.find_all('div', {'data-test': 'product-item'})[:5]  # Limit to top 5
                
                for item in product_items:
                    name = item.find('h3').text.strip()
                    description = item.find('div', {'data-test': 'product-description'}).text.strip()
                    votes = item.find('span', {'data-test': 'vote-button'}).text.strip()
                    
                    # Get the product URL
                    link_element = item.find('a', {'data-test': 'product-name-link'})
                    product_url = f"https://www.producthunt.com{link_element['href']}" if link_element else None
                    
                    product = {
                        'name': name,
                        'description': description,
                        'votes': votes,
                        'url': product_url,
                        'scraped_at': datetime.now().isoformat()
                    }
                    products.append(product)
                    logging.info(f"Scraped product: {name}")
                
                logging.info(f"Successfully scraped {len(products)} products from Product Hunt")
                return {"status": "success", "data": products}
                
            except Exception as e:
                logging.error(f"Error scraping Product Hunt: {str(e)}")
                return {"status": "error", "message": str(e)}

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
