import os
import glob
import re

cur_dir = r"c:\Users\Harsha\Documents\10-Templates\realestate\1"

# Rename projects to properties
projects_path = os.path.join(cur_dir, "projects.html")
properties_path = os.path.join(cur_dir, "properties.html")
if os.path.exists(projects_path):
    os.rename(projects_path, properties_path)

html_files = glob.glob(os.path.join(cur_dir, "*.html"))

new_footer_css = """
        /* --- Robust Footer --- */
        .main-footer {
            background-color: #1C1A18;
            color: #FFFFFF;
            padding: 80px 0 30px;
            margin-top: 80px;
        }
        .footer-grid {
            display: grid;
            grid-template-columns: 2fr 1fr 1fr;
            gap: 60px;
            margin-bottom: 60px;
        }
        .footer-logo {
            font-family: var(--font-serif);
            font-size: 1.8rem;
            font-weight: 500;
            margin-bottom: 20px;
            color: #FFFFFF !important;
            text-transform: uppercase;
        }
        .footer-desc {
            color: #A09E9C;
            font-size: 0.95rem;
            max-width: 350px;
            line-height: 1.6;
            margin-bottom: 30px;
        }
        .social-links {
            display: flex;
            gap: 20px;
        }
        .social-links a {
            color: #FFFFFF;
            font-size: 0.85rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            border-bottom: 1px solid transparent;
            text-decoration: none;
        }
        .social-links a:hover {
            color: var(--accent-green);
            border-color: var(--accent-green);
        }
        .footer-col h4 {
            font-family: var(--font-serif);
            font-size: 1.3rem;
            margin-bottom: 25px;
            font-weight: 400;
            color: #FFFFFF;
        }
        .footer-col ul {
            list-style: none;
            padding: 0;
            margin: 0;
        }
        .footer-col ul li {
            margin-bottom: 15px;
            color: #A09E9C;
            font-size: 0.95rem;
        }
        .footer-col ul li a {
            color: #A09E9C;
            text-decoration: none;
            transition: color 0.3s;
        }
        .footer-col ul li a:hover {
            color: #FFFFFF;
        }
        .footer-bottom {
            border-top: 1px solid rgba(255,255,255,0.1);
            padding-top: 30px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            color: #A09E9C;
            font-size: 0.85rem;
        }
        @media (max-width: 900px) {
            .footer-grid {
                grid-template-columns: 1fr;
                gap: 40px;
            }
            .footer-bottom {
                flex-direction: column;
                gap: 15px;
                text-align: center;
            }
        }
"""

new_footer_html = """
    <footer class="main-footer">
        <div class="container">
            <div class="footer-grid">
                <div class="footer-col">
                    <div class="footer-logo">ARCHETYPE</div>
                    <p class="footer-desc">Sculpting light and defining space through visionary architecture and sustainable design.</p>
                    <div class="social-links">
                        <a href="#" aria-label="Instagram">Instagram</a>
                        <a href="#" aria-label="LinkedIn">LinkedIn</a>
                        <a href="#" aria-label="Twitter">Twitter</a>
                    </div>
                </div>
                <div class="footer-col">
                    <h4>Quick Links</h4>
                    <ul>
                        <li><a href="index.html">Home</a></li>
                        <li><a href="about.html">About Us</a></li>
                        <li><a href="properties.html">Properties</a></li>
                    </ul>
                </div>
                <div class="footer-col">
                    <h4>Contact Us</h4>
                    <ul>
                        <li>Guntur, Andhra Pradesh</li>
                        <li><a href="mailto:contact@archetype.com">contact@archetype.com</a></li>
                        <li><a href="tel:+919876543210">+91 98765 43210</a></li>
                    </ul>
                </div>
            </div>
            <div class="footer-bottom">
                <p>&copy; 2026 Archetype. All rights reserved.</p>
                <p>Sculpting Light, Defining Space.</p>
            </div>
        </div>
    </footer>
"""

for filepath in html_files:
    if not filepath.endswith(".html"):
        continue

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Rename projects.html to properties.html everywhere
    content = content.replace('href="projects.html"', 'href="properties.html"')
    content = content.replace('projects.html', 'properties.html')

    # 1. Update Footer CSS
    content = re.sub(r'/\*\s*--- Footer ---\s*\*/.*?}(?=\s*(?:/\*|<\/style>))', '', content, flags=re.DOTALL | re.IGNORECASE)
    if ".main-footer {" not in content:
        content = content.replace("</style>", new_footer_css + "\n    </style>")

    # 2. Update Footer HTML
    content = re.sub(r'<footer>.*?</footer>', new_footer_html, content, flags=re.DOTALL | re.IGNORECASE)

    # 3. Update Nav Colors Make text white, turn black on scroll
    if "header.scrolled nav {" not in content:
        content = content.replace("header.scrolled {", "header.scrolled nav { color: var(--text-primary); }\n        header.scrolled {")
    
    # We want header to be background: transparent by default.
    def repl_header(m):
        header_body = m.group(1)
        header_body = re.sub(r'background:\s*rgba\([^)]+\)', 'background: transparent', header_body)
        return "header {" + header_body + "}"
    content = re.sub(r'header\s*{([^}]+)}', repl_header, content)

    # We want nav to be color: #FFFFFF by default
    def repl_nav(m):
        nav_body = m.group(1)
        # remove existing colors in nav base
        nav_body = re.sub(r'color:\s*[^;]+;', '', nav_body)
        return "nav {" + nav_body + " color: #FFFFFF;}"
    
    # Be careful not to replace header.scrolled nav! Use a stricter regex or just `.replace` for the basic `nav {`
    # Let's cleanly apply it:
    # `nav { display: flex; ... font-weight: 500; }`
    nav_match = re.search(r'(\n\s*nav\s*\{[^}]*?\})', content)
    if nav_match:
        nav_block = nav_match.group(1)
        # remove color
        nav_block_new = re.sub(r'color:\s*[^;]+;', '', nav_block)
        nav_block_new = nav_block_new.replace('}', ' color: #FFFFFF; }')
        content = content.replace(nav_block, nav_block_new)

    # 4. Check for properties.html - insert Hero element
    if filepath.endswith("properties.html") or filepath.endswith("projects.html"):
        hero_replacement = """
        <section class="properties-hero" style="position: relative; padding: 180px 0 120px; background-color: #1C1A18; color: white;">
            <img src="https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?q=80&w=2000&auto=format&fit=crop" style="position: absolute; top:0; left:0; width:100%; height:100%; object-fit: cover; opacity: 0.3;" alt="Properties Hero">
            <div class="container" style="position: relative; z-index: 1;">
                <h1 style="font-family: var(--font-serif); font-size: clamp(3rem, 5vw, 4.5rem); font-weight: 400; margin-bottom: 20px;">Selected Properties</h1>
                <p style="font-size: 1.15rem; max-width: 600px; opacity: 0.9;">Explore our curated collection of visionary architectural designs, spanning coastal retreats to modern commercial spaces.</p>
            </div>
        </section>
        """
        content = re.sub(r'<div class="container">\s*<section class="page-header">.*?</section>', hero_replacement, content, flags=re.DOTALL)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

print("Done updates")
