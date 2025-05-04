import streamlit as st
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import re
import pytesseract
from PIL import Image
from io import BytesIO

# Selenium imports
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

# Initialize session state
if 'form_urls' not in st.session_state:
    st.session_state.form_urls = []

# OCR check for phone numbers in images
def image_has_phone_number(img_url, session):
    try:
        response = session.get(img_url, timeout=10)
        if response.status_code == 200:
            image = Image.open(BytesIO(response.content)).convert("RGB")
            text = pytesseract.image_to_string(image)
            phone_pattern = r'(\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4})'
            if re.search(phone_pattern, text):
                return True
    except:
        pass
    return False

# Crawl pages and find forms (static + JS) and images with phone numbers
def find_forms_with_selenium(base_url, max_pages=10):
    visited = set()
    queue = [base_url]
    session = requests.Session()

    # Setup headless Chrome
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")

    driver = webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options)

    progress_bar = st.progress(0)
    status_text = st.empty()

    try:
        while queue and len(visited) < max_pages:
            url = queue.pop(0)
            if url in visited:
                continue

            try:
                driver.get(url)
                progress = len(visited) / max_pages
                progress_bar.progress(progress)
                status_text.text(f"Crawling: {url[:50]}... ({len(visited)}/{max_pages} pages)")

                # Check for forms (JS-rendered or static)
                forms = driver.find_elements(By.TAG_NAME, 'form')
                if forms:
                    st.session_state.form_urls.append(url)
                    st.success(f"✅ Form found at: {url}")

                # Static HTML parsing for image URLs
                response = session.get(url, timeout=10)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')

                    images = soup.find_all('img', src=True)
                    for img in images:
                        img_url = urljoin(url, img['src'])
                        if image_has_phone_number(img_url, session):
                            st.session_state.form_urls.append(img_url)
                            st.success(f"📷 Image with phone number found at: {img_url}")

                    # Find internal links to continue crawling
                    links = soup.find_all('a', href=True)
                    for link in links:
                        href = link['href']
                        absolute_url = urljoin(url, href)
                        if urlparse(absolute_url).netloc == urlparse(base_url).netloc:
                            if absolute_url not in visited and absolute_url not in queue:
                                queue.append(absolute_url)

                visited.add(url)

            except Exception as e:
                st.error(f"⚠️ Error crawling {url[:50]}...: {str(e)[:100]}")
                continue

    finally:
        driver.quit()
        progress_bar.empty()
        status_text.empty()

# Display results in UI
def display_form_urls():
    st.subheader("📋 Pages or Images with Forms / Phone Numbers", divider="rainbow")

    if st.session_state.form_urls:
        for i, url in enumerate(st.session_state.form_urls, 1):
            with st.expander(f"🔹 Item {i}: {url[:60]}..."):
                st.markdown(f"""
                **Full URL:**  
                [{url}]({url})  

                **Quick Actions:**  
                🔗 [Open in new tab]({url})  
                📋 Copy to clipboard: `{url}`
                """)
        st.success(f"🎉 Found {len(st.session_state.form_urls)} relevant items!")
    else:
        st.warning("No forms or phone numbers in images found on the scanned pages.")

# Main UI
def main():
    st.title("🔍 Form & Phone Number Finder")
    st.markdown("This tool crawls a website to find **HTML or JavaScript-rendered forms** and **images containing phone numbers**.")

    col1, col2 = st.columns(2)
    with col1:
        base_url = st.text_input("Website URL:", placeholder="https://example.com")
    with col2:
        max_pages = st.number_input("Max pages to scan:", min_value=1, max_value=50, value=10)

    if st.button("🚀 Start Scanning", type="primary"):
        if not base_url.strip():
            st.warning("Please enter a valid website URL.")
        else:
            st.session_state.form_urls = []
            find_forms_with_selenium(base_url, max_pages)

    if st.session_state.form_urls:
        display_form_urls()

if __name__ == "__main__":
    main()
