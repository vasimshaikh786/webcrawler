import streamlit as st
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

# Initialize session state
if 'form_urls' not in st.session_state:
    st.session_state.form_urls = []

def find_forms(base_url, max_pages=10):
    visited = set()
    queue = [base_url]
    session = requests.Session()
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        while queue and len(visited) < max_pages:
            url = queue.pop(0)
            
            if url in visited:
                continue

            try:
                progress = len(visited) / max_pages
                progress_bar.progress(progress)
                status_text.text(f"Crawling: {url[:50]}... ({len(visited)}/{max_pages} pages)")

                response = session.get(url, timeout=10)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')

                    # Check for forms
                    if soup.find_all('form'):
                        if url not in st.session_state.form_urls:
                            st.session_state.form_urls.append(url)
                            st.success(f"✅ Form found at: {url}")

                    visited.add(url)

                    # Find links to continue crawling
                    for link in soup.find_all('a', href=True):
                        href = link['href']
                        absolute_url = urljoin(url, href)
                        if urlparse(absolute_url).netloc == urlparse(base_url).netloc:
                            if absolute_url not in visited and absolute_url not in queue:
                                queue.append(absolute_url)

            except Exception as e:
                st.error(f"⚠️ Error crawling {url[:50]}: {str(e)[:100]}")
                continue

    finally:
        progress_bar.empty()
        status_text.empty()

def display_form_urls():
    st.subheader("📋 Pages with Forms", divider="rainbow")
    
    if st.session_state.form_urls:
        for i, url in enumerate(st.session_state.form_urls, 1):
            with st.expander(f"🔹 Form {i}: {url[:60]}..."):
                st.markdown(f"""
                **Full URL:**  
                [{url}]({url})  
                
                **Quick Actions:**  
                🔗 [Open in new tab]({url})  
                📋 Copy to clipboard: `{url}`
                """)
        st.toast(f"Found {len(st.session_state.form_urls)} form pages!", icon="🎉")
    else:
        st.warning("No forms found on the scanned pages.")

def main():
    st.set_page_config(page_title="Form & Phone Finder", page_icon="🔍")
    st.title("🔍 Form & Phone Number Finder")
    st.markdown("This tool crawls a website to find HTML-rendered forms.")

    col1, col2 = st.columns(2)
    with col1:
        base_url = st.text_input("Website URL:", placeholder="https://example.com")
    with col2:
        max_pages = st.number_input("Max pages to scan:", min_value=1, max_value=50, value=10)

    if st.button("🚀 Start Scanning", type="primary"):
        if not base_url.startswith("http"):
            st.error("Please enter a valid URL (starting with http or https).")
        else:
            st.session_state.form_urls = []
            find_forms(base_url, max_pages)

    if st.session_state.form_urls:
        display_form_urls()

if __name__ == "__main__":
    main()
