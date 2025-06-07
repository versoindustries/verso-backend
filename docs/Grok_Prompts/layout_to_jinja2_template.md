Prompt for Generating Jinja2 Template from Written Layout Description
Objective: Generate a Jinja2 template that extends base.html based on a provided written layout description, implementing a modern, responsive, and SEO-friendly web page layout for use in a web application.
Instructions:

Input: A written layout description detailing sections of a web page, including their purpose, content, design, and placement (e.g., generated from the "Prompt for Generating Modern Layouts from Written Copy").

Output: A Jinja2 template that:

Extends base.html using {% extends "base.html" %}.
Fills in the following blocks, assumed to be available in base.html:
title: Set to the heading of the first section in the layout description.
description: Set to the first paragraph of the first section in the layout description.
head: Include SEO meta tags (e.g., Open Graph, Twitter cards, canonical link) and a simple JSON-LD schema.
content: Implement the described sections with semantic HTML5 structure and custom CSS classes.
scripts: Include JavaScript for any interactive elements mentioned in the description.


Uses semantic HTML5 elements (e.g., <section>, <article>, <nav>) where appropriate.
Applies custom CSS classes reflecting the design elements (e.g., introduction-section, features-grid) for styling, assuming styles are defined externally.
Ensures responsiveness using flexible layouts (e.g., flexbox, grid) that adapt to different screen sizes.
Includes placeholders for images, icons, or visuals (e.g., {{ url_for('static', filename='images/placeholder.jpg') }}) as described, assuming they reside in the static/images folder.
Implements interactive elements (e.g., galleries, forms) with necessary HTML and JavaScript, using placeholders where applicable.
Use fontawesome icons, it's included in the base.html already


SEO Implementation:

In the head block, include:<meta name="description" content="{{ description }}">
<meta property="og:title" content="{{ title }}">
<meta property="og:description" content="{{ description }}">
<meta property="og:image" content="{{ url_for('static', filename='images/logo.png') }}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{{ title }}">
<meta name="twitter:description" content="{{ description }}">
<meta name="twitter:image" content="{{ url_for('static', filename='images/logo.png') }}">
<link rel="canonical" href="{{ request.url }}">
<meta name="robots" content="index, follow">


Add a simple JSON-LD schema:<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "WebPage",
  "name": "{{ title }}",
  "description": "{{ description }}"
}
</script>






Guidelines for base.html:

Assume base.html provides:
A <head> section with basic meta tags (e.g., charset, viewport), links to main CSS (e.g., styles.css), and common JavaScript files.
A <body> with blocks: title, description, additional_css, head, scripts, and content.
Placeholder structure that the generated template will override or extend.


The generated template only needs to fill these blocks, not redefine the full HTML structure.


Design and Responsiveness:

Map each section from the description to an HTML structure (e.g., a two-column layout becomes <div class="two-column-layout"> with flexbox children).
Use descriptive CSS classes (e.g., feature-list, gallery-container) that a developer can style to match the described design.
Structure content to stack or adjust on smaller screens (e.g., flexbox with flex-wrap or grid with media queries).


Interactive Elements:

For galleries, include HTML (e.g., <div class="gallery-grid">) and basic JavaScript (e.g., lightbox functionality) in the scripts block.
For forms, use Jinja2 syntax (e.g., {{ form.field_name }}) and assume CSRF protection is handled by base.html.


Security:

Sanitize any dynamic content with Jinja2 filters (e.g., |e) if user inputs are implied in the description.



Prompt Template:
Generate a Jinja2 template that extends 'base.html' based on the following written layout description. Implement the described sections with semantic HTML structure, custom CSS classes, and JavaScript for interactive elements. Include SEO meta tags in the head block and ensure the template is responsive.

[Insert the written layout description here]

