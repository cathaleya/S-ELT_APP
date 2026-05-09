import streamlit as st
import streamlit.components.v1 as components
import os
import base64
import re

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
            border-radius: 0;
            height: 100vh !important;
        }
        /* Container for mobile frame */
        .mobile-wrapper {
            width: 100%;
            max-width: 450px;
            height: 100vh;
            margin: 0 auto;
            border-left: 1px solid #ddd;
            border-right: 1px solid #ddd;
            background: #fff;
            position: relative;
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
        return "<h1>File not found</h1>"
    
    with open(html_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 1. Inject CSS
    if 'styles_final.css' in content or '<link rel="stylesheet" href="styles_final.css">' in content:
        if os.path.exists('styles_final.css'):
            with open('styles_final.css', 'r', encoding='utf-8') as cf:
                css_data = cf.read()
            content = content.replace('<link rel="stylesheet" href="styles_final.css">', f'<style>{css_data}</style>')

    # 2. Convert Images to Base64
    images = re.findall(r'src=["\'](.*?\.png|.*?\.jpg|.*?\.jpeg|.*?\.gif)["\']', content)
    # Also find background-images in style tags
    bg_images = re.findall(r'url\(["\']?(.*?\.png|.*?\.jpg|.*?\.jpeg|.*?\.gif)["\']?\)', content)
    
    all_images = list(set(images + bg_images))
    for img in all_images:
        if img.startswith('http'): continue
        # Clean query params like ?v=2026
        clean_img = img.split('?')[0]
        if os.path.exists(clean_img):
            b64 = get_base64(clean_img)
            ext = clean_img.split('.')[-1]
            content = content.replace(img, f'data:image/{ext};base64,{b64}')

    # 3. Intercept Links for Navigation
    # Replace window.location.href = 'xxx.html' with Streamlit query param update
    # Note: Streamlit Components are in an iframe, so window.parent is the way.
    nav_script = """
    <script>
    document.addEventListener('click', function(e) {
        let target = e.target.closest('a');
        if (target && target.href && target.href.includes('.html')) {
            e.preventDefault();
            let page = target.getAttribute('href').split('/').pop();
            window.parent.postMessage({type: 'navigation', page: page}, '*');
        }
    });
    
    // Override window.location.href
    const originalHref = Object.getOwnPropertyDescriptor(window.location, 'href');
    // We can't easily override location.href, so we use a helper
    function navigate(page) {
        window.parent.postMessage({type: 'navigation', page: page}, '*');
    }
    // Replace window.location.href assignment in the existing code
    </script>
    """
    # Simple replacement of location.href assignments
    content = content.replace("window.location.href='", "navigate('")
    content = content.replace('window.location.href = "', 'navigate("')
    content = content.replace('window.location.href = \'', 'navigate(\'')
    
    if '</body>' in content:
        content = content.replace('</body>', nav_script + '</body>')
    else:
        content += nav_script

    return content

# Navigation handling
if 'page' not in st.session_state:
    st.session_state.page = 'splash.html'

# Communication from iframe to Streamlit
from streamlit_js_eval import streamlit_js_eval

# Use query params for state management if possible, or session state
# For now, let's use a simpler trick: catch messages from iframe
import streamlit.components.v1 as components

# Handle messages from the HTML component
# This requires a more complex component, so we'll use query params for now.
# THE TRICK: Use a dummy query param to trigger rerun
params = st.query_params
if 'p' in params:
    st.session_state.page = params['p']

html_to_show = process_html(st.session_state.page)

# Render
components.html(html_to_show, height=900, scrolling=True)

# Navigation via Query Params helper
st.markdown("""
<script>
window.addEventListener("message", (event) => {
    if (event.data.type === "navigation") {
        const url = new URL(window.location.href);
        url.searchParams.set("p", event.data.page);
        window.parent.location.href = url.href;
    }
}, false);
</script>
""", unsafe_allow_html=True)
