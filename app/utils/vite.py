import os
from flask import current_app, url_for
from markupsafe import Markup
import json

def vite_tags():
    """
    Generates the script tags for Vite.
    
    Priority:
    1. If USE_VITE_DEV=1, use Vite dev server (for HMR during active development)
    2. If production manifest exists, use built assets (works in debug mode too)
    3. Fallback to dev server if no production build available
    """
    use_vite_dev = os.environ.get('USE_VITE_DEV', '0') == '1'
    
    # Check for production manifest
    manifest_path = os.path.join(current_app.static_folder, 'dist', '.vite', 'manifest.json')
    if not os.path.exists(manifest_path):
        manifest_path = os.path.join(current_app.static_folder, 'dist', 'manifest.json')
    has_prod_build = os.path.exists(manifest_path)
    
    # Use dev server only if explicitly requested OR no production build available
    if use_vite_dev or not has_prod_build:
        return Markup(f"""
            <script type="module" src="http://localhost:5173/@vite/client"></script>
            <script type="module" src="http://localhost:5173/app/static/src/main.tsx"></script>
        """)
    
    # Production: read manifest.json
    try:
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
        
        entry = manifest.get('main.tsx')
        if not entry:
            return Markup("<!-- Vite entry not found in manifest -->")
        
        check_file = entry['file']
        css_files = entry.get('css', [])
        
        tags = [f'<script type="module" src="{url_for("static", filename=f"dist/{check_file}")}"></script>']
        
        for css in css_files:
            tags.append(f'<link rel="stylesheet" href="{url_for("static", filename=f"dist/{css}")}">')
            
        return Markup('\n'.join(tags))
    except Exception as e:
        current_app.logger.error(f"Vite manifest error: {e}")
        return Markup(f"<!-- Vite manifest error: {e} -->")
