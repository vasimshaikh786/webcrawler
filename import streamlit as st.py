import re
import requests
import streamlit as st
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import pytesseract
from PIL import Image, UnidentifiedImageError
import io

# Initialize session state variables if they don't exist
if 'forms' not in st.session_state:
    st.session_state.forms = []
if 'phone_numbers' not in st.session_state:
    st.session_state.phone_numbers = []
if 'images_with_phones' not in st.session_state:
    st.session_state.images_with_phones = []
if 'crawling' not in st.session_state:
    st.session_state.crawling = False
if 'visited' not in st.session_state:
    st.session_state.visited = set()

class WebCrawler:
    def __init__(self, base_url, max_pages=10):
        self.base_url = base_url
        self.domain = urlparse(base_url).netloc
        self.max_pages = max_pages
        self.phone_pattern = re.compile(
            r'(\+\d{1,3}[-.\s]?)?(\d{1,4}[-.\s]?)?(\(\d{1,4}\)[-.\s]?)?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,9}'
        )
        self.image_extensions = ('.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.gif')
        self.skip_urls = ('google.com', 'gstatic.com', 'facebook.com', 'twitter.com')

    def is_valid_url(self, url):
        parsed = urlparse(url)
        if any(skip in parsed.netloc for skip in self.skip_urls):
            return False
        return bool(parsed.netloc) and parsed.netloc == self.domain

    def get_absolute_url(self, url):
        return urljoin(self.base_url, url)

    def extract_text_from_image(self, image_url):
        try:
            # Skip non-image URLs
            if not image_url.lower().endswith(self.image_extensions):
                return ""
                
            response = requests.get(image_url, stream=True, timeout=10)
            if response.status_code == 200:
                image = Image.open(io.BytesIO(response.content))
                text = pytesseract.image_to_string(image)
                return text
            return ""
        except UnidentifiedImageError:
            return ""
        except pytesseract.pytesseract.TesseractNotFoundError:
            st.warning("Tesseract OCR is not available. Image processing disabled.")
            return ""
        except Exception as e:
            st.error(f"Error processing image {image_url[:50]}...: {str(e)[:100]}...")
            return ""

    def crawl_page(self, url):
        if url in st.session_state.visited or len(st.session_state.visited) >= self.max_pages:
            return

        try:
            st.session_state.visited.add(url)
            with st.spinner(f"Crawling: {url}"):
                response = requests.get(url, timeout=10)
                soup = BeautifulSoup(response.text, 'html.parser')

                # 1. Find forms
                forms = soup.find_all('form')
                for form in forms:
                    form_name = form.get('id') or form.get('name') or form.get('aria-label') or "Unnamed Form"
                    form_action = form.get('action', url)
                    absolute_form_url = self.get_absolute_url(form_action)
                    st.session_state.forms.append({
                        'url': absolute_form_url,
                        'name': form_name
                    })

                # 2. Find phone numbers in text
                text = soup.get_text()
                found_phones = self.phone_pattern.findall(text)
                for match in found_phones:
                    phone = ''.join(match).strip()
                    if phone:
                        st.session_state.phone_numbers.append({
                            'phone': phone,
                            'url': url
                        })

                # 3. Find images that might contain phone numbers
                images = soup.find_all('img')
                for img in images:
                    img_src = img.get('src')
                    if img_src:
                        absolute_img_url = self.get_absolute_url(img_src)
                        self.process_image(absolute_img_url, url)

                # Find all links and add to queue
                links = soup.find_all('a', href=True)
                for link in links:
                    href = link['href']
                    absolute_url = self.get_absolute_url(href)
                    if self.is_valid_url(absolute_url) and absolute_url not in st.session_state.visited:
                        # For Streamlit, we'll process one page at a time
                        if len(st.session_state.visited) < self.max_pages:
                            self.crawl_page(absolute_url)

        except Exception as e:
            st.error(f"Error crawling {url}: {str(e)[:100]}...")

    def process_image(self, image_url, page_url):
        text = self.extract_text_from_image(image_url)
        if text:
            found_phones = self.phone_pattern.findall(text)
            for match in found_phones:
                phone = ''.join(match).strip()
                if phone:
                    st.session_state.images_with_phones.append({
                        'image_url': image_url,
                        'page_url': page_url,
                        'phone': phone
                    })

def display_results():
    st.subheader("Crawling Results")
    
    # 1. Forms
    st.write("### 1) Forms Found")
    if st.session_state.forms:
        for form in st.session_state.forms:
            st.write(f"**URL:** [{form['url']}]({form['url']}) - **Form Name:** {form['name']}")
    else:
        st.write("No forms found")
    
    # 2. Phone numbers
    st.write("### 2) Phone Numbers Found")
    if st.session_state.phone_numbers:
        for phone in st.session_state.phone_numbers:
            st.write(f"**Phone:** {phone['phone']} - **Page URL:** [{phone['url']}]({phone['url']})")
    else:
        st.write("No phone numbers found in page text")
    
    # 3. Images with phone numbers
    st.write("### 3) Images with Phone Numbers")
    if st.session_state.images_with_phones:
        for img in st.session_state.images_with_phones:
            st.write(f"**Page URL:** [{img['page_url']}]({img['page_url']})")
            st.write(f"**Image SRC:** {img['image_url']}")
            st.write(f"**Phone in Image:** {img['phone']}")
            st.image(img['image_url'], caption=img['phone'], width=200)
    else:
        st.write("No phone numbers found in images")

def main():
    st.title("Website Crawler")
    st.write("This tool crawls a website to find forms, phone numbers, and images containing phone numbers.")

    base_url = st.text_input("Enter website URL to crawl (e.g., https://example.com):")
    max_pages = st.number_input("Maximum pages to crawl:", min_value=1, max_value=50, value=10)

    if st.button("Start Crawling") and base_url:
        # Reset session state for new crawl
        st.session_state.forms = []
        st.session_state.phone_numbers = []
        st.session_state.images_with_phones = []
        st.session_state.visited = set()
        st.session_state.crawling = True

        try:
            crawler = WebCrawler(base_url, max_pages)
            crawler.crawl_page(base_url)
            st.success("Crawling completed!")
            st.session_state.crawling = False
        except Exception as e:
            st.error(f"Crawling failed: {str(e)}")
            st.session_state.crawling = False

    if st.session_state.forms or st.session_state.phone_numbers or st.session_state.images_with_phones:
        display_results()

if __name__ == "__main__":
    main()
