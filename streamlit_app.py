import streamlit as st
import streamlit.components.v1 as components
import os
import base64
import re

# Set Page Config MUST be the first Streamlit command
st.set_page_config(
    page_title="S-ELT Mobile App",
    page_icon="🎤",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Custom CSS to force mobile view and hide Streamlit UI
st.markdown("""
    <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        .block-container {
            padding: 0 !important;
            max-width: 450px !important;
            margin: 0 auto;
        }
        iframe {
            border: none;
            height: 100vh !important;
        }
    </style>
""", unsafe_allow_html=True)

def get_base64(file_path):
    if not os.path.exists(file_path):
        return ""
    with open(file_path, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()

def process_html(html_file):
    if not os.path.exists(html_file):
        # Default to splash if file missing
        if html_file != "splash.html":
            return process_html("splash.html")
        return "<h1>Initialization Error</h1>"
    
    with open(html_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 1. Inject Global CSS
    if os.path.exists('styles_final.css'):
        with open('styles_final.css', 'r', encoding='utf-8') as cf:
            css_data = cf.read()
        # Replace the link tag or inject if not present
        if '<link rel="stylesheet" href="styles_final.css">' in content:
            content = content.replace('<link rel="stylesheet" href="styles_final.css">', f'<style>{css_data}</style>')
        else:
            content = content.replace('</head>', f'<style>{css_data}</style></head>')

    # 2. Convert Images to Base64 (Crucial for Streamlit Cloud)
    # This ensures images load even if the iframe is on a different domain
    images = re.findall(r'src=["\'](.*?\.png|.*?\.jpg|.*?\.jpeg|.*?\.gif)["\']', content)
    bg_images = re.findall(r'url\(["\']?(.*?\.png|.*?\.jpg|.*?\.jpeg|.*?\.gif)["\']?\)', content)
    
    for img in list(set(images + bg_images)):
        if img.startswith('http') or img.startswith('data:'): continue
        clean_img = img.split('?')[0]
        if os.path.exists(clean_img):
            b64 = get_base64(clean_img)
            ext = clean_img.split('.')[-1]
            content = content.replace(img, f'data:image/{ext};base64,{b64}')

    # 3. INTERCEPT NAVIGATION
    # We transform all local links into parent-level query parameter updates.
    # This allows the Streamlit app to 'route' between files.
    
    # A) HTML Links: <a href="page.html"> -> <a href="?p=page.html" target="_parent">
    content = re.sub(r'href=["\']([^"\'\s]+\.html)(.*?)["\']', r'href="?p=\1\2" target="_parent"', content)

    # B) JS Redirections: window.location.href = 'page.html' -> window.parent.location.href = '?p=page.html'
    # Handles: window.location.href='page.html', window.location.href = "page.html", etc.
    content = re.sub(r'window\.location\.href\s*=\s*["\']([^"\'\s]+\.html)(.*?)["\']', r"window.parent.location.href='?p=\1\2'", content)
    
    # C) Special handling for dashboard completion parameters
    content = content.replace("dashboard.html?completed=", "?p=dashboard.html&completed=")

    return content

# --- MAIN ROUTING LOGIC ---

# 1. Capture query parameters
# In modern Streamlit, st.query_params behaves like a dict
query_p = st.query_params.get("p", "splash.html")

# 2. Prevent infinite loops or invalid files
valid_files = [f for f in os.listdir('.') if f.endswith('.html')]
if query_p not in valid_files:
    query_p = "splash.html"

# 3. Process and display the page
try:
    final_html = process_html(query_p)
    components.html(final_html, height=900, scrolling=False)
except Exception as e:
    st.error(f"Error loading page: {e}")
    if st.button("Back to Home"):
        st.query_params.clear()
        st.rerun()
