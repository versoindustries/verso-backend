from flask import Flask, render_template, url_for, request, redirect, Response
import xml.etree.ElementTree as ET
import os
import requests
from app import create_app

# Sitemap generation function (to be modified as per your requirements)
def generate_sitemap(app):
    app = create_app()  # Create an instance of the Flask app
    with app.app_context():
        # Extract routes from the application
        links = []
        for rule in app.url_map.iter_rules():
            # Filter out rules you can't navigate to in a browser
            # and rules that require parameters
            if "GET" in rule.methods and len(rule.arguments) == 0:
                url = url_for(rule.endpoint, _external=True)
                links.append(url)

        # Generate sitemap
        urlset = ET.Element("urlset", xmlns="http://www.sitemaps.org/schemas/sitemap/0.9")
        for link in links:
            u = ET.SubElement(urlset, "url")
            loc = ET.SubElement(u, "loc")
            loc.text = link

        tree = ET.ElementTree(urlset)
        sitemap_path = os.path.join(app.static_folder, 'sitemap.xml')
        tree.write(sitemap_path, encoding='utf-8', xml_declaration=True)

    # Submit to Bing
    submit_sitemap_to_bing('http://www.znhhomebuilders.com/static/sitemap.xml')

def submit_sitemap_to_bing(sitemap_url):
    api_key = 'f00ed402512c4d4b929fec116ad623d3'  # Store this in a secure place
    submit_url = f'https://www.bing.com/indexnow?url={sitemap_url}&key={api_key}'
    response = requests.get(submit_url)
    if response.status_code == 200:
        print("Sitemap successfully submitted to Bing")
    else:
        print("Error submitting sitemap to Bing:", response.text)

def check_and_submit_new_page(page):
    if page.is_public:  # Check if the page is not login restricted
        submit_sitemap_to_bing(page.url)