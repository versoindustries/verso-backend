Prompt for Generating Modern CSS for Web Page Sections
Objective
Generate modern, responsive CSS for a specific section of a web page based on a provided description, optimized for use in a Flask-based backend with Jinja2 templates. The CSS should enhance the section with a futuristic aesthetic, ensure mobile-friendliness, and align with the design system defined in base.css.
Instructions
Input
A written description of a web page section, detailing its purpose, content, and desired design elements (e.g., a hero banner with a title and button, or a features grid with cards).
Output
CSS code that:

Styles the described section with a modern look (e.g., glassmorphism, subtle animations).
Uses custom class names for clarity and maintainability (e.g., .hero-section, .features-grid).
Implements a mobile-first approach with specific optimizations for 768px and 480px viewports.
Leverages variables from base.css (e.g., --primary-bg, --text-primary) for colors, fonts, and shadows.
Incorporates FontAwesome icons where applicable (e.g., fas fa-arrow-right).
Adds subtle animations (e.g., hover effects, pulse transitions) for interactivity.

Guidelines

Use semantic, descriptive class names reflecting the section’s purpose.
Structure CSS for readability, grouping related styles together.
Apply glassmorphism effects (e.g., backdrop-filter: blur(10px)) where suitable.
Use flexbox or grid for flexible, responsive layouts.
Ensure text legibility with sufficient contrast against backgrounds.
Include hover effects and transitions for buttons or interactive elements.

Responsiveness

Start with base styles optimized for mobile devices (default viewport).
Use media queries to enhance layouts for screens 768px and wider.
Add adjustments for very small screens (480px and below) to maintain usability.

Design Integration

Assume base.css defines:
Color variables (e.g., --glass-bg, --primary-bg).
Font settings using Neon fonts.
Shadow and spacing utilities.


Reference these variables to ensure consistency with the overall design system.

Example Structure
/* Section Name */
.section-class {
    padding: 20px;
    background: var(--glass-bg);
    backdrop-filter: blur(10px);
    display: flex;
    flex-direction: column;
    gap: 15px;
}

.section-class h2 {
    font-size: 1.5rem;
    color: var(--text-primary);
    font-family: 'Neon', sans-serif;
}

.section-class .icon {
    font-size: 1.2rem;
    transition: transform 0.3s ease;
}

.section-class .icon:hover {
    transform: scale(1.1);
}

/* Medium screens (768px and up) */
@media (min-width: 768px) {
    .section-class {
        padding: 40px;
        flex-direction: row;
    }

    .section-class h2 {
        font-size: 2rem;
    }
}

/* Small screens (480px and below) */
@media (max-width: 480px) {
    .section-class {
        padding: 15px;
    }

    .section-class h2 {
        font-size: 1.2rem;
    }
}

Additional Notes

Assume the section’s HTML structure is defined in the corresponding Jinja2 template.
Use FontAwesome classes (e.g., fas fa-users) for icons, as they’re included in base.html.
Avoid inline styles or security risks by relying on external CSS and predefined variables.
Focus on presentation without affecting accessibility (e.g., maintain readable font sizes).

Prompt Template
Generate modern, responsive CSS for the following web page section description. Include mobile optimizations for 768px and 480px viewports, and ensure the styles align with the futuristic aesthetic defined in base.css.

[Insert the written section description here]
