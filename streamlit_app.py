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

# Hide Streamlit elements to make it look like a pure mobile app
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
    if not os.path.exists(file_path): return ""
    with open(file_path, "rb") as f:
        return base64.b64encode(f.read()).decode()

def bundle_app():
    # 1. Load CSS
    css_data = ""
    if os.path.exists('styles_final.css'):
        with open('styles_final.css', 'r', encoding='utf-8') as f:
            css_data = f.read()

    # 2. Load all HTML pages and extract their content
    pages_html = ""
    html_files = [f for f in os.listdir('.') if f.endswith('.html') and f != 'index.html']
    
    # Ensure splash is first
    if 'splash.html' in html_files:
        html_files.remove('splash.html')
        html_files.insert(0, 'splash.html')

    for file in html_files:
        with open(file, 'r', encoding='utf-8') as f:
            content = f.read()
            
            # Extract content between <body> tags or just the app-container
            match = re.search(r'<div class="app-container">(.*?)</div>\s*<nav class="bottom-nav">', content, re.DOTALL)
            if not match:
                match = re.search(r'<div class="app-container">(.*?)</div>', content, re.DOTALL)
            
            body_content = match.group(1) if match else "Content not found"
            
            # Add bottom nav if it exists
            nav_match = re.search(r'<nav class="bottom-nav">(.*?)</nav>', content, re.DOTALL)
            nav_html = f'<nav class="bottom-nav">{nav_match.group(1)}</nav>' if nav_match else ""

            pages_html += f"""
            <div id="page-{file}" class="selt-page" style="display: none; height: 100vh; position: relative;">
                <div class="app-container">
                    {body_content}
                </div>
                {nav_html}
            </div>
            """

    # 3. Create the Master SPA Template (Use double braces to escape f-string)
    master_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <title>S-ELT SPA</title>
        <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800;900&family=Playfair+Display:wght@700;800&family=Satisfy&family=Luckiest+Guy&display=swap" rel="stylesheet">
        <style>
            {css_data}
            body, html {{ margin: 0; padding: 0; overflow: hidden; background: #f8f6ec; }}
            .selt-page {{ width: 100%; overflow-x: hidden; }}
        </style>
    </head>
    <body>
        {pages_html}

        <script>
            // NAVIGATION ENGINE
            function navigate(page) {{
                document.querySelectorAll('.selt-page').forEach(p => p.style.display = 'none');
                const target = document.getElementById('page-' + page);
                if (target) {{
                    target.style.display = 'block';
                    window.scrollTo(0, 0);
                    if (page === 'dashboard.html') updateDashboard();
                }}
            }}

            function goTo(url) {{
                const page = url.split('?')[0];
                const params = url.split('?')[1];
                if (params && params.includes('completed=')) {{
                    const compId = params.split('completed=')[1];
                    localStorage.setItem('temp_comp', compId);
                }}
                navigate(page);
            }}

            document.addEventListener('click', function(e) {{
                const a = e.target.closest('[onclick*="window.location.href"]');
                if (a) {{
                    e.preventDefault();
                    const attr = a.getAttribute('onclick');
                    const match = attr.match(/window\.location\.href\s*=\s*['"](.*?)['"]/);
                    if (match) goTo(match[1]);
                }}
                
                const link = e.target.closest('a');
                if (link && link.getAttribute('href') && link.getAttribute('href').endsWith('.html')) {{
                    e.preventDefault();
                    goTo(link.getAttribute('href'));
                }}
            }});

            function updateDashboard() {{
                const compId = localStorage.getItem('temp_comp');
                if (compId) {{
                    const overlay = document.querySelector('#page-dashboard.html #feedback-overlay');
                    if (overlay) {{
                        overlay.style.display = 'flex';
                        localStorage.removeItem('temp_comp');
                    }}
                }}
            }}

            // Start with Splash
            navigate('splash.html');
        </script>
    </body>
    </html>
    """

    # 4. Final Base64 Image Replacement
    images = re.findall(r'src=["\'](.*?\.png|.*?\.jpg|.*?\.jpeg|.*?\.gif)["\']', master_html)
    bg_images = re.findall(r'url\(["\']?(.*?\.png|.*?\.jpg|.*?\.jpeg|.*?\.gif)["\']?\)', master_html)
    for img in list(set(images + bg_images)):
        if img.startswith('http') or img.startswith('data:'): continue
        clean_img = img.split('?')[0]
        if os.path.exists(clean_img):
            b64 = get_base64(clean_img)
            ext = clean_img.split('.')[-1]
            master_html = master_html.replace(img, f'data:image/{ext};base64,{b64}')

    return master_html

# --- EXECUTE BUNDLER ---
try:
    spa_content = bundle_app()
    components.html(spa_content, height=1000, scrolling=False)
except Exception as e:
    st.error(f"Bundling Error: {e}")
