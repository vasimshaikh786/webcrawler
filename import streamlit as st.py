import streamlit as st
import requests
import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

# Initialize session state
if 'form_urls' not in st.session_state:
    st.session_state.form_urls = []
if 'phone_numbers' not in st.session_state:
    st.session_state.phone_numbers = []

def find_elements(base_url, max_pages=10):
    visited = set()
    queue = [base_url]
    session = requests.Session()
    
    # Enhanced phone number regex
    phone_pattern = re.compile(
        r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b|'
        r'\b\d{3}[-.\s]?\d{4}\b|'
        r'\b(Toll[- ]?Free|Call|Phone|Tel|Telephone|Contact)[: ]?[- ]?(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b',
        re.IGNORECASE
    )
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        while queue and len(visited) < max_pages:
            url = queue.pop(0)
            
            if url in visited:
                continue
                
            try:
                # Update progress
                progress = len(visited)/max_pages
                progress_bar.progress(progress)
                status_text.text(f"🔍 Scanning: {url[:50]}... ({len(visited)}/{max_pages} pages)")
                
                response = session.get(url, timeout=10)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Enhanced form detection
                    form_elements = soup.find_all(['form', 'div', 'section'], class_=re.compile(r'form|contact|request', re.I))
                    if form_elements:
                        is_form = False
                        for element in form_elements:
                            # Check for actual form tags or divs with form-like content
                            if element.name == 'form' or (element.find(['input', 'textarea', 'button']) and 
                                                         any(term in element.get('class', [''])[0].lower() 
                                                         for term in ['form', 'contact', 'request'] if element.get('class')):
                                is_form = True
                                break
                        
                        if is_form and url not in st.session_state.form_urls:
                            st.session_state.form_urls.append(url)
                            st.success(f"✅ Form found at: {url}")
                    
                    # Phone number detection
                    text = soup.get_text()
                    for match in phone_pattern.finditer(text):
                        phone = match.group()
                        context = text[max(0, match.start()-20):match.end()+20].strip()
                        # Check if this number was already found on this page
                        if not any(p['phone'] == phone and p['url'] == url for p in st.session_state.phone_numbers):
                            st.session_state.phone_numbers.append({
                                'phone': phone,
                                'url': url,
                                'context': context
                            })
                            st.success(f"📞 Phone number found: {phone}")
                    
                    visited.add(url)
                    
                    # Find all links on the page
                    for link in soup.find_all('a', href=True):
                        href = link['href']
                        absolute_url = urljoin(url, href)
                        if (urlparse(absolute_url).netloc == urlparse(base_url).netloc and 
                            absolute_url not in visited and 
                            absolute_url not in queue):
                            queue.append(absolute_url)
                                
            except Exception as e:
                st.error(f"⚠️ Error scanning {url[:50]}...: {str(e)[:100]}")
                continue
                
    finally:
        progress_bar.empty()
        status_text.empty()

def display_results():
    st.subheader("📋 Scan Results", divider="rainbow")
    
    # Forms section
    with st.expander(f"📝 Forms Found ({len(st.session_state.form_urls)})", expanded=True):
        if st.session_state.form_urls:
            for i, url in enumerate(st.session_state.form_urls, 1):
                st.markdown(f"""
                **Form {i}:**  
                🔗 [{url}]({url})  
                📋 `{url}`
                """)
        else:
            st.warning("No forms found")
    
    # Phone numbers section
    with st.expander(f"📞 Phone Numbers Found ({len(st.session_state.phone_numbers)})", expanded=True):
        if st.session_state.phone_numbers:
            cols = st.columns([1, 3, 6])
            cols[0].markdown("**#**")
            cols[1].markdown("**Phone Number**")
            cols[2].markdown("**Found On Page**")
            
            for i, item in enumerate(st.session_state.phone_numbers, 1):
                cols = st.columns([1, 3, 6])
                cols[0].markdown(f"{i}.")
                cols[1].markdown(f"`{item['phone']}`")
                cols[2].markdown(f"[{item['url'][:50]}...]({item['url']})  \n*(...{item['context']}...)*")
        else:
            st.warning("No phone numbers found")

def main():
    st.title("🔍 Website Scanner Pro")
    st.markdown("Find forms and phone numbers on any website")
    
    col1, col2 = st.columns(2)
    with col1:
        base_url = st.text_input("Website URL:", placeholder="https://example.com", value="https://kreativedgeinteriors.com")
    with col2:
        max_pages = st.number_input("Max pages to scan:", min_value=1, max_value=50, value=10)
    
    if st.button("🚀 Start Scan", type="primary"):
        st.session_state.form_urls = []
        st.session_state.phone_numbers = []
        find_elements(base_url, max_pages)
        st.toast("Scan completed!", icon="🎉")
    
    if st.session_state.form_urls or st.session_state.phone_numbers:
        display_results()

if __name__ == "__main__":
    main()
