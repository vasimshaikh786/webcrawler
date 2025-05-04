import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from concurrent.futures import ThreadPoolExecutor
import pytesseract
from PIL import Image
import io

class WebCrawler:
    def __init__(self, base_url, max_pages=50):
        self.base_url = base_url
        self.domain = urlparse(base_url).netloc
        self.visited = set()
        self.max_pages = max_pages
        self.forms = []
        self.phone_numbers = []
        self.images_with_phones = []
        self.phone_pattern = re.compile(
            r'(\+\d{1,3}[-.\s]?)?(\d{1,4}[-.\s]?)?(\(\d{1,4}\)[-.\s]?)?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,9}'
        )

    def is_valid_url(self, url):
        parsed = urlparse(url)
        return bool(parsed.netloc) and parsed.netloc == self.domain

    def get_absolute_url(self, url):
        return urljoin(self.base_url, url)

    def extract_text_from_image(self, image_url):
        try:
            response = requests.get(image_url, stream=True)
            if response.status_code == 200:
                image = Image.open(io.BytesIO(response.content))
                text = pytesseract.image_to_string(image)
                return text
            return ""
        except Exception as e:
            print(f"Error processing image {image_url}: {e}")
            return ""

    def crawl(self, url=None):
        if url is None:
            url = self.base_url

        if url in self.visited or len(self.visited) >= self.max_pages:
            return

        try:
            print(f"Crawling: {url}")
            self.visited.add(url)
            response = requests.get(url, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')

            # 1. Find forms
            forms = soup.find_all('form')
            for form in forms:
                form_name = form.get('id') or form.get('name') or form.get('aria-label') or "Unnamed Form"
                form_action = form.get('action', url)
                absolute_form_url = self.get_absolute_url(form_action)
                self.forms.append({
                    'url': absolute_form_url,
                    'name': form_name
                })

            # 2. Find phone numbers in text
            text = soup.get_text()
            found_phones = self.phone_pattern.findall(text)
            for match in found_phones:
                phone = ''.join(match).strip()
                if phone:
                    self.phone_numbers.append({
                        'phone': phone,
                        'url': url
                    })

            # 3. Find images that might contain phone numbers
            images = soup.find_all('img')
            with ThreadPoolExecutor(max_workers=5) as executor:
                for img in images:
                    img_src = img.get('src')
                    if img_src:
                        absolute_img_url = self.get_absolute_url(img_src)
                        # Check if image URL looks like it might contain text (simple heuristic)
                        if any(ext in absolute_img_url.lower() for ext in ['.png', '.jpg', '.jpeg']):
                            # Submit image for processing
                            executor.submit(self.process_image, absolute_img_url, url)

            # Find all links and crawl them
            links = soup.find_all('a', href=True)
            for link in links:
                href = link['href']
                absolute_url = self.get_absolute_url(href)
                if self.is_valid_url(absolute_url) and absolute_url not in self.visited:
                    self.crawl(absolute_url)

        except Exception as e:
            print(f"Error crawling {url}: {e}")

    def process_image(self, image_url, page_url):
        text = self.extract_text_from_image(image_url)
        if text:
            found_phones = self.phone_pattern.findall(text)
            for match in found_phones:
                phone = ''.join(match).strip()
                if phone:
                    self.images_with_phones.append({
                        'image_url': image_url,
                        'page_url': page_url,
                        'phone': phone
                    })

    def get_results(self):
        return {
            'forms': self.forms,
            'phone_numbers': self.phone_numbers,
            'images_with_phones': self.images_with_phones
        }

    def print_results(self):
        print("\nResults:")
        
        # 1. Forms
        print("\n1) Forms:")
        for form in self.forms:
            print(f"URL: {form['url']} - Form Name: {form['name']}")
        
        # 2. Phone numbers
        print("\n2) Phone Numbers:")
        for phone in self.phone_numbers:
            print(f"Phone: {phone['phone']} - Page URL: {phone['url']}")
        
        # 3. Images with phone numbers
        print("\n3) Images with Phone Numbers:")
        for img in self.images_with_phones:
            print(f"Page URL: {img['page_url']}")
            print(f"Image SRC: {img['image_url']}")
            print(f"Phone in Image: {img['phone']}\n")

# Usage example:
if __name__ == "__main__":
    # Note: You'll need to install pytesseract and Tesseract OCR for image processing
    # pip install pytesseract pillow
    # Also install Tesseract OCR from https://github.com/tesseract-ocr/tesseract
    
    target_url = "https://example.com"  # Replace with your target URL
    crawler = WebCrawler(target_url, max_pages=20)
    crawler.crawl()
    crawler.print_results()
