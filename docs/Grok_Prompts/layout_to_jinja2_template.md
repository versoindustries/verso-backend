
**Prompt for Generating Jinja2 Template from Written Layout Description**

**Objective**: Generate a Jinja2 template that extends `base.html` based on a provided written layout description, implementing a modern, responsive, and SEO-friendly web page layout for use in a web application.

**Instructions**:

**Input**: A written layout description detailing sections of a web page, including their purpose, content, design, and placement (e.g., generated from the "Prompt for Generating Modern Layouts from Written Copy").

**Output**: A Jinja2 template that:

- Extends `base.html` using `{% extends "base.html" %}`.
- Fills in the following blocks, assumed to be available in `base.html`:
  - `title`: Set to the heading of the first section in the layout description.
  - `description`: Set to the first paragraph of the first section in the layout description.
  - `additional_css`: Include a link to a custom CSS file specific to the page, using `{{ url_for('static', filename='css/[page-name].css') }}`, where `[page-name]` is derived from the page's purpose or title (e.g., `edit-user.css` for an edit user page).
  - `head`: Include SEO meta tags (e.g., Open Graph, Twitter cards, canonical link) and a simple JSON-LD schema.
  - `content`: Implement the described sections with semantic HTML5 structure and custom CSS classes.
  - `scripts`: Include vanilla JavaScript for any interactive elements mentioned in the description.
- Uses semantic HTML5 elements (e.g., `<section>`, `<article>`, `<nav>`) where appropriate.
- Applies custom CSS classes reflecting the design elements (e.g., `introduction-section`, `features-grid`) for styling, assuming styles are defined in the external CSS file linked in `additional_css`.
- Ensures responsiveness using flexible layouts (e.g., flexbox, grid) that adapt to different screen sizes, optimized for 768px and 480px viewports with a mobile-first approach.
- Includes placeholders for images, icons, or visuals (e.g., `{{ url_for('static', filename='images/placeholder.jpg') }}`) as described, assuming they reside in the `static/images` folder.
- Implements interactive elements (e.g., galleries, forms) with necessary HTML and JavaScript, using placeholders where applicable.
- Uses Font Awesome icons (free version) for icon usage, assuming inclusion in `base.html`.

**SEO Implementation**:

In the `head` block, include:
```html
<meta name="description" content="{{ description | e }}">
<meta property="og:title" content="{{ title | e }}">
<meta property="og:description" content="{{ description | e }}">
<meta property="og:image" content="{{ url_for('static', filename='images/logo.png') }}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{{ title | e }}">
<meta name="twitter:description" content="{{ description | e }}">
<meta name="twitter:image" content="{{ url_for('static', filename='images/logo.png') }}">
<link rel="canonical" href="{{ request.url }}">
<meta name="robots" content="index, follow">
```

Add a simple JSON-LD schema:
```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "WebPage",
  "name": "{{ title | e }}",
  "description": "{{ description | e }}"
}
</script>
```

**Guidelines for `base.html`**:

Assume `base.html` provides:
- A `<head>` section with basic meta tags (e.g., charset, viewport), links to main CSS (e.g., `styles.css`), and common JavaScript files.
- A `<body>` with blocks: `title`, `description`, `additional_css`, `head`, `content`, and `scripts`.
- Placeholder structure that the generated template will override or extend.

The generated template only needs to fill these blocks, not redefine the full HTML structure.

**Design and Responsiveness**:

- Map each section from the description to an HTML structure (e.g., a two-column layout becomes `<div class="two-column-layout">` with flexbox children).
- Use descriptive CSS classes (e.g., `feature-list`, `gallery-container`) that a developer can style in the linked CSS file to match the described design.
- Structure content to stack or adjust on smaller screens (e.g., flexbox with `flex-wrap` or grid with media queries) using a mobile-first approach.
- Optimize for 768px and 480px viewports, ensuring compatibility with smaller screens.

**Interactive Elements**:

- For galleries, include HTML (e.g., `<div class="gallery-grid">`) and basic JavaScript (e.g., lightbox functionality) in the `scripts` block.
- For forms, use Jinja2 syntax (e.g., `{{ form.field_name }}`) and assume CSRF protection is handled by `base.html` or the form object.
- Place JavaScript in the `scripts` block, ensuring it is lightweight and stored in `static/js` if external files are needed.

**Security**:

- Sanitize any dynamic content with Jinja2 filters (e.g., `|e`) if user inputs are implied in the description.
- Avoid inline styles or scripts; use the `additional_css` block for CSS and `scripts` block for JavaScript.

**Prompt Template**:
```
Generate a Jinja2 template that extends 'base.html' based on the following written layout description. Implement the described sections with semantic HTML structure, custom CSS classes, and vanilla JavaScript for interactive elements. Always include an 'additional_css' block linking to a page-specific CSS file (e.g., {{ url_for('static', filename='css/[page-name].css') }}). Include SEO meta tags in the 'head' block and ensure the template is responsive with a mobile-first approach, optimized for 768px and 480px viewports. Use Font Awesome icons where appropriate.

[Insert the written layout description here]
