import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin, urlparse
from PIL import Image, UnidentifiedImageError
from io import BytesIO

def is_valid_url(url):
    """Checks if the given URL is valid."""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False

def fetch_page_content(url):
    """Fetches the content of a given URL."""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()  # Raise an exception for bad status codes
        return response.text, response.url
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching {url}: {e}")
        return None, None

def find_images(html_content, base_url, current_url):
    """Finds images in the HTML content."""
    soup = BeautifulSoup(html_content, 'html.parser')
    images_data = []
    for img_tag in soup.find_all('img'):
        img_src = img_tag.get('src')
        if img_src:
            absolute_url = urljoin(base_url, img_src)
            try:
                img_response = requests.get(absolute_url, stream=True, timeout=5)
                img_response.raise_for_status()
                content_type = img_response.headers.get('Content-Type')
                if content_type and content_type.startswith('image/'):
                    try:
                        image = Image.open(BytesIO(img_response.content))
                        images_data.append({"original_url": absolute_url, "location": current_url, "image": image})
                    except UnidentifiedImageError as e:
                        st.warning(f"Could not open image from {absolute_url}: {e}")
                else:
                    st.warning(f"Skipping non-image file: {absolute_url} (Content-Type: {content_type})")
            except requests.exceptions.RequestException as e:
                st.warning(f"Could not retrieve resource from {absolute_url}: {e}")
            except UnidentifiedImageError as e:
                st.warning(f"Could not identify image format from {absolute_url}: {e}")
    return images_data

def find_forms(html_content, base_url, current_url):
    """Finds forms in the HTML content and extracts relevant information."""
    soup = BeautifulSoup(html_content, 'html.parser')
    form_actions = set()
    for form_tag in soup.find_all('form'):
        action = form_tag.get('action')
        if action:
            absolute_url = urljoin(base_url, action)
            form_actions.add(absolute_url)
        # You might want to add more logic here to identify form types based on keywords
        # or input fields. For simplicity, we are just extracting form URLs.
    return [{"url": url} for url in form_actions]

def find_phone_numbers(html_content, current_url):
    """Finds phone numbers in the HTML content."""
    phone_number_pattern = re.compile(r'(\+\d{1,3}\s?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}|\d{3}-\d{3}-\d{4}|\d{10,11}')
    phone_numbers = set(re.findall(phone_number_pattern, html_content))
    return [{"number": number, "location": current_url} for number in phone_numbers]

def crawl_website(start_url):
    """Crawls the website and extracts information."""
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

    return all_images, all_forms, all_phone_numbers

def display_images(images_data):
    """Displays the extracted images in a grid format."""
    st.subheader("Images Found:")
    if images_data:
        cols = st.columns(3)  # Adjust the number of columns as needed
        for i, img_info in enumerate(images_data):
            with cols[i % 3]:
                st.image(img_info["image"], caption=f"Location: {img_info['location']}", use_column_width=True)
                st.markdown(f"**Original URL:** {img_info['original_url']}")
    else:
        st.info("No images found on the crawled pages.")

def display_forms(forms_data):
    """Displays the extracted form URLs."""
    st.subheader("Forms Found:")
    if forms_data:
        for form in forms_data:
            st.markdown(f"**Forms URL:** {form['url']}")
    else:
        st.info("No forms found on the crawled pages.")

def display_phone_numbers(phone_numbers_data):
    """Displays the extracted phone numbers and their locations."""
    st.subheader("Phone Numbers Found:")
    if phone_numbers_data:
        for phone_info in phone_numbers_data:
            st.markdown(f"**Phone Number:** {phone_info['number']}")
            st.markdown(f"**Page URL:** {phone_info['location']}")
            st.divider()
    else:
        st.info("No phone numbers found on the crawled pages.")

def main():
    st.title("Web Crawler and Information Extractor")

    start_url = st.text_input("Enter the URL of the website to crawl:")

    if st.button("Start Crawling"):
        if start_url:
            images, forms, phone_numbers = crawl_website(start_url)
            display_images(images)
            display_forms(forms)
            display_phone_numbers(phone_numbers)
        else:
            st.warning("Please enter a URL to start crawling.")

if __name__ == "__main__":
    main()
