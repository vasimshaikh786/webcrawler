import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin, urlparse
from PIL import Image, UnidentifiedImageError
from io import BytesIO
import time  # Import the time module

def is_valid_url(url):
    """Checks if the given URL is valid."""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False

def fetch_page_content(url):
    """Fetches the content of a given URL with a custom User-Agent."""
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()  # Raise an exception for bad status codes
        return response.text, response.url
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching {url}: {e}")
        return None, None

def find_images(html_content, base_url, current_url):
    # ... (rest of your find_images function remains the same)

def find_forms(html_content, base_url, current_url):
    # ... (rest of your find_forms function remains the same)

def find_phone_numbers(html_content, current_url):
    # ... (rest of your find_phone_numbers function remains the same)

def crawl_website(start_url):
    if not is_valid_url(start_url):
        st.error("Invalid URL provided.")
        return

    visited = set()
    queue = [start_url]
    base_url = urlparse(start_url).netloc
    all_images = []
    all_forms = []
    all_phone_numbers = []

    with st.spinner(f"Crawling {start_url}..."):
        while queue:
            current_url = queue.pop(0)
            if current_url in visited:
                continue
            visited.add(current_url)
            st.info(f"Crawling: {current_url}")

            html_content, actual_url = fetch_page_content(current_url)
            if html_content:
                all_images.extend(find_images(html_content, start_url, actual_url))
                all_forms.extend(find_forms(html_content, start_url, actual_url))
                all_phone_numbers.extend(find_phone_numbers(html_content, actual_url))

                soup = BeautifulSoup(html_content, 'html.parser')
                for link in soup.find_all('a', href=True):
                    absolute_link = urljoin(current_url, link['href'])
                    if base_url in absolute_link and absolute_link not in visited:
                        queue.append(absolute_link)
            time.sleep(0.1) # Add a small delay between requests

    return all_images, all_forms, all_phone_numbers

def display_images(images_data):
    # ... (rest of your display_images function remains the same)

def display_forms(forms_data):
    # ... (rest of your display_forms function remains the same)

def display_phone_numbers(phone_numbers_data):
    # ... (rest of your display_phone_numbers function remains the same)

def main():
    # ... (rest of your main function remains the same)

if __name__ == "__main__":
    main()
