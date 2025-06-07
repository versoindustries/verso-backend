### Prompt for Implementing a Feature in a Flask-Based Application

**Objective**: Provide step-by-step instructions for implementing a specified feature, system, or enhancement in a Flask-based application, ensuring seamless integration with the existing codebase. The solution should prioritize security (OWASP guidelines), performance, maintainability, and suitability for an open-source project on GitHub, without including any code.

**Instructions**:
1. **Input**: Accept the user-provided task description, codebase details, requirements, constraints, and preferences for the feature to be implemented in their Flask-based application. This may include:
   - A detailed feature description (e.g., "Build a product inventory system with CRUD operations").
   - Codebase details (e.g., key files like `app/models.py`, `app/routes/main_routes.py`, or a GitHub repository link).
   - Requirements and constraints (e.g., environment, dependencies, security, performance, user expertise).
   - Preferences (e.g., output format, front-end needs, documentation).
2. **Output**: Provide a detailed, step-by-step guide for implementing the feature, structured as a written description without any code snippets. For each step:
   - **Purpose**: Explain the goal of the step (e.g., defining the database model, setting up routes).
   - **Actions**: Describe the specific tasks to complete (e.g., create a model class, configure a route, update a template).
   - **Integration**: Explain how the step integrates with the existing codebase (e.g., referencing existing models, routes, or templates).
   - **Considerations**: Highlight best practices for:
     - **Security**: Address OWASP guidelines (e.g., input validation, CSRF protection, secure file uploads).
     - **Performance**: Suggest optimizations (e.g., database indexing, caching, query efficiency).
     - **Maintainability**: Recommend modular design, clear naming, and documentation.
     - **Open-Source Suitability**: Ensure the approach is clear, well-documented, and follows GitHub contribution standards.
   - **Order**: Specify the sequence of the step relative to others (e.g., "After defining the model, configure the routes").
3. **Design Principles**:
   - **Security**: Align with OWASP Top Ten (e.g., prevent SQL injection, secure session management, sanitize inputs).
   - **Performance**: Optimize for scalability (e.g., minimize database queries, use lazy loading, implement caching).
   - **Maintainability**: Promote modular code, clear documentation, and adherence to PEP 8 for Python.
   - **Open-Source Readiness**: Ensure the feature is well-documented, includes contribution guidelines, and is easy for external contributors to understand.
   - **User Expertise**: Tailor instructions to the user’s experience level (e.g., detailed explanations for beginners, concise steps for advanced users).
4. **Feature Implementation**:
   - Break the feature into logical components (e.g., database models, routes, templates, front-end interactivity).
   - Describe how to structure each component (e.g., model fields, route logic, template layout).
   - Suggest file organization (e.g., placing new routes in `app/routes/main_routes.py`).
   - Address integration with existing features (e.g., tying into an existing User model or authentication system).
5. **Constraints**:
   - Do not generate any code (e.g., Python, HTML, JavaScript, SQL). Provide only written instructions.
   - Do not assume specific tools, libraries, or frameworks beyond Flask and user-specified dependencies.
   - Respect user-specified constraints (e.g., environment, database, dependencies, testing needs).
   - If the feature involves front-end elements (e.g., forms, dynamic content), describe their integration visually and functionally without technical implementation details.
6. **Additional Notes**:
   - If the user specifies preferences (e.g., deployment environment, front-end styling, documentation needs), incorporate them into the instructions.
   - Suggest testing strategies (e.g., unit tests for CRUD operations, integration tests for routes) and describe their purpose.
   - Provide deployment instructions tailored to the specified environment (e.g., Heroku, AWS).
   - Include documentation recommendations (e.g., updating README, creating user-facing docs, adding contribution guidelines for GitHub).
   - If the feature interacts with existing functionality (e.g., authentication, existing models), describe how to ensure compatibility.
7. **Format**:
   - Start with a brief introduction summarizing the feature and its purpose within the Flask application.
   - List each implementation step as a numbered item, including subheadings for **Purpose**, **Actions**, **Integration**, and **Considerations**.
   - Conclude with a summary of the overall approach, including:
     - Testing recommendations to verify the feature.
     - Deployment steps for the specified environment.
     - Documentation and GitHub contribution guidelines (e.g., pull request structure, README updates).
     - Any final notes (e.g., scalability, future enhancements).

||

{Replace with your task description, codebase details, requirements, constraints, and preferences for the Flask-based feature implementation.}