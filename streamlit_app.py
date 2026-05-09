import streamlit as st
import streamlit.components.v1 as components
import os
import base64
import re

# 1. Page Config
st.set_page_config(
    page_title="S-ELT Mobile App",
    page_icon="🎤",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# 2. Global CSS for Mobile Look
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
            height: 95vh !important;
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
        return f"<h1>File not found: {html_file}</h1>"
    
    with open(html_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # A. Inject CSS
    if os.path.exists('styles_final.css'):
        with open('styles_final.css', 'r', encoding='utf-8') as cf:
            css_data = cf.read()
        content = content.replace('<link rel="stylesheet" href="styles_final.css">', f'<style>{css_data}</style>')

    # B. Base64 Images
    images = re.findall(r'src=["\'](.*?\.png|.*?\.jpg|.*?\.jpeg|.*?\.gif)["\']', content)
    bg_images = re.findall(r'url\(["\']?(.*?\.png|.*?\.jpg|.*?\.jpeg|.*?\.gif)["\']?\)', content)
    for img in list(set(images + bg_images)):
        if img.startswith('http') or img.startswith('data:'): continue
        clean_img = img.split('?')[0]
        if os.path.exists(clean_img):
            b64 = get_base64(clean_img)
            ext = clean_img.split('.')[-1]
            content = content.replace(img, f'data:image/{ext};base64,{b64}')

    # C. ROBUST NAVIGATION (postMessage Strategy)
    nav_script = """
    <script>
    function seltNavigate(page) {
        window.parent.postMessage({
            type: 'selt_nav',
            page: page
        }, '*');
    }
    document.addEventListener('click', function(e) {
        let a = e.target.closest('a');
        if (a && a.getAttribute('href') && a.getAttribute('href').endsWith('.html')) {
            e.preventDefault();
            seltNavigate(a.getAttribute('href'));
        }
    });
    </script>
    """
    if '<body>' in content:
        content = content.replace('<body>', '<body>' + nav_script)
    else:
        content = nav_script + content

    # Transform programmatic redirects: window.location.href = 'xxx' -> seltNavigate('xxx')
    content = re.sub(r'window\.location\.href\s*=\s*["\']([^"\'\s]+)["\']', r"seltNavigate('\1')", content)
    
    # Handle the specific dashboard completed logic
    content = content.replace("dashboard.html?completed=", "dashboard.html&completed=")

    return content

# --- NAVIGATION ROUTER ---

# Use Query Params for persistent routing
# Modern Streamlit (1.30+) uses st.query_params
current_page = st.query_params.get("p", "splash.html")

# Render the page
try:
    processed_content = process_html(current_page)
    components.html(processed_content, height=900, scrolling=False)
except Exception as e:
    st.error(f"Error: {e}")

# LISTEN FOR NAVIGATION MESSAGES FROM THE IFRAME
# This script runs in the PARENT window (Streamlit)
st.markdown("""
<script>
const streamlitDoc = window.parent.document;
window.addEventListener("message", (event) => {
    if (event.data.type === "selt_nav") {
        const page = event.data.page;
        // Update URL query param to trigger Streamlit rerun
        const url = new URL(window.location.href);
        url.searchParams.set("p", page);
        window.location.href = url.href;
    }
}, false);
</script>
""", unsafe_allow_html=True)

# Add a tiny "Rescue" link in case navigation fails
if st.button("Reset App (Back to Splash)"):
    st.query_params.clear()
    st.rerun()
