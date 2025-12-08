# System Instructions for Verso-Backend Repository Contributors

**Repository**: Verso-Backend (https://github.com/versoindustries/verso-backend)\
**Python Version**: 3.10.11

These instructions provide a comprehensive guide for contributors to ensure consistency, security, performance, and maintainability across the Flask backend application. Please follow these guidelines carefully when working on the project.

---

## 1. Coding Standards & Compliance

- Adhere to PEP 8 plus enterprise secure coding norms: threat-model changes, avoid risky constructs, and keep functions small and auditable.
- Align with OWASP ASVS/Top 10 for the backend: validate inputs, enforce authz on every route, output-encode, and protect against injection/XSS/CSRF/SSRF.
- Use meaningful names and docstrings for all functions/classes; keep public interfaces documented and side effects explicit.
- Avoid hardcoded values and secrets; source from configuration (`config.py`) or environment variables, and never commit keys or tokens.
- Keep logging privacy-aware (no credentials/PII), add structured context for audits, and ensure errors do not leak stack traces in production.

---

## 2. Flask Application Structure

- Use Flask blueprints to organize the application into modular components.
- Store configuration settings in a separate `config.py` file or use environment variables.
- Implement custom error pages for common HTTP errors (e.g., 404, 500) to improve user experience.

---

## 3. Jinja2 Templates

- All templates must extend from `base.html` using Jinja2's template inheritance.
- Use template blocks to override specific sections in child templates.
- Ensure that no user input is directly executed in templates to prevent cross-site scripting (XSS) attacks.

---

## 4. CSS and HTML

- Write custom CSS and avoid inline styles for better maintainability. Provide only one section at a time to ensure completeness. 
- Ensure the design is responsive, with specific optimizations for 768px and 480px viewports.
- Follow a mobile-first design approach to ensure compatibility with smaller screens.

---

## 5. JavaScript

- Use vanilla JavaScript; avoid unnecessary libraries to keep the codebase lightweight.
- Place all JavaScript files in the `static/js` folder.
- Minimize and bundle JavaScript files to reduce load times and improve performance.

---

## 6. SEO Considerations

- Include appropriate meta tags (e.g., title, description, keywords) in the HTML `<head>` for each page.
- Use semantic HTML5 elements to improve search engine crawlability and accessibility.
- Ensure that all pages are accessible and indexable by search engines.

---

## 7. Security

- Follow the OWASP Top 10 guidelines to prevent common security vulnerabilities.
- Sanitize all user inputs to prevent SQL injection and XSS attacks.
- Use HTTPS to encrypt data in transit and protect sensitive information.

---

## 8. Performance Optimization

- Optimize images and other assets to reduce file sizes and improve load times.
- Implement caching strategies for static files and database queries to reduce server load.
- Minimize the number of HTTP requests by bundling CSS and JavaScript files.

---

## 9. Testing

- Write unit tests for Python code using a testing framework like pytest.
- Test the application's responsiveness and functionality across different browsers and devices.
- Ensure that all tests pass before merging changes into the main branch.

---

## 10. Documentation

- Keep the `README.md` file up to date with setup instructions, contribution guidelines, and a project overview.
- Document any API endpoints, including request and response formats, if applicable.

---

## 11. Debugging and Error Handling

- Add logging statements to trace application behavior and identify issues.
- Use Python's pdb for debugging Python code and browser developer tools for frontend issues.
- Handle exceptions gracefully and provide user-friendly error messages in production.

---

## 12. Version Control

- Use Git for version control, with the `main` branch as the production-ready branch.
- Create feature branches for new developments and bug fixes.
- Write descriptive commit messages and create pull requests for code reviews.

---
