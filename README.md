# Verso Backend

![ZNH Mockup](app/static/images/gallery/ZNH-Mockup.jpg)

**Verso Backend** is a Flask-based backend template designed for easy deployment on Heroku for as low as $7/month(https://www.heroku.com/). It provides a robust foundation for building scalable and secure web applications with features like user authentication, database models, forms, and email support. This template is highly extensible and can integrate with various frontend frameworks or templating engines, such as Jinja2, Tailwind CSS, or Figma-to-Webflow pages.

## Features

- **User Authentication**: Secure registration, login, password reset, and role-based access control.
- **Database Models**: Predefined SQLAlchemy models for users, roles, appointments, services, and more.
- **Forms**: WTForms for seamless user input handling and validation.
- **Email Support**: Configured with Flask-Mail for sending emails (e.g., password resets), though specific provider APIs are recommended for future enhancements.
- **Admin Interface**: Basic admin dashboard for managing users, appointments, and site content.
- **User Dashboard**: Replaces the homepage post-login, redirecting registered users to a personalized dashboard.
- **Heroku Ready**: Pre-configured for straightforward deployment on Heroku.
- **Modular Design**: Easily extendable with additional routes, models, and features.
- **AppointQix**: Verso Industries’ native appointment system integrated directly into the backend.

## Prerequisites

- **Python 3.10.11**: Ensure this version is installed.
- **pip**: Python package installer.
- **Virtualenv**: Recommended for isolating dependencies.

## Setup Instructions

Follow these steps to set up the project locally:

1. **Clone the Repository**
   ```bash
   git clone https://github.com/versoindustries/verso-backend.git
   cd verso-backend
   ```

2. **Create a Virtual Environment**
   ```bash
   python -m venv env
   ```

3. **Activate the Virtual Environment**
   - On Windows:
     ```bash
     env\Scripts\activate
     ```
   - On macOS/Linux:
     ```bash
     source env/bin/activate
     ```

4. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

5. **Set Environment Variables**
   - Create a `.env` file in the root directory with:
     ```
     FLASK_APP=app
     SECRET_KEY=your_secure_random_key
     DATABASE_URL=sqlite:///mydatabase.sqlite  # Or your preferred database URL
     MAIL_SERVER=smtp.example.com
     MAIL_PORT=587
     MAIL_USE_TLS=True
     MAIL_USERNAME=your_email
     MAIL_PASSWORD=your_password
     MAIL_DEFAULT_SENDER=your_email
     ```
   - Load variables:
     - On Windows:
       ```bash
       set FLASK_APP=app
       ```
     - On macOS/Linux:
       ```bash
       export FLASK_APP=app
       ```

6. **Initialize the Database**
   ```bash
   python dbl.py
   ```
   - Note: `dbl.py` is a custom script for database initialization.

7. **Run Database Migrations**
   ```bash
   python -m flask db init
   python -m flask db migrate
   python -m flask db upgrade
   ```

8. **Create Default Roles**
   ```bash
   python -m flask create-roles
   ```

9. **Run the Application**
   ```bash
   python -m flask run --host=0.0.0.0 --debug
   ```
   - **Note**: The `--host=0.0.0.0` flag allows LAN connections for local development only. Avoid using it in production.

10. **Set Admin User**
    - After registering an account via the web app, set the user as admin:
      ```bash
      flask set-admin your_email@example.com
      ```
    - Replace `your_email@example.com` with the registered email.

## Deployment to Heroku

To deploy the application on Heroku:

1. **Install Heroku CLI and Log In**
   ```bash
   heroku login
   ```

2. **Create a Heroku App**
   ```bash
   heroku create your-app-name
   ```

3. **Set Environment Variables on Heroku**
   ```bash
   heroku config:set FLASK_APP=app
   heroku config:set SECRET_KEY=your_secret_key
   heroku config:set DATABASE_URL=your_database_url
   heroku config:set MAIL_SERVER=your_mail_server
   heroku config:set MAIL_PORT=your_mail_port
   heroku config:set MAIL_USE_TLS=True  # or False
   heroku config:set MAIL_USERNAME=your_mail_username
   heroku config:set MAIL_PASSWORD=your_mail_password
   heroku config:set MAIL_DEFAULT_SENDER=your_default_sender
   ```
   - Replace placeholders with appropriate values.

4. **Push to Heroku**
   ```bash
   git push heroku main
   ```

5. **Run Migrations on Heroku**
   ```bash
   heroku run flask db upgrade
   ```

6. **Create Default Roles on Heroku**
   ```bash
   heroku run flask create-roles
   ```

Alternatively, link your Heroku account to your GitHub repository and deploy directly from GitHub.

## Usage

- Access the app at `http://localhost:5000` locally or your Heroku app URL.
- Register a new user via the registration page.
- Set a user as admin using the admin command (see Setup Instructions).
- Explore dashboards and features based on roles (e.g., admin, commercial, user).

## Notes on Database Migrations

When updating `models.py` or `forms.py`, update the database schema:

1. **Shut Down the Server**
   - Press `Ctrl + C`.
2. **Generate a Migration**
   ```bash
   flask db migrate -m "Description of changes"
   ```
3. **Apply the Migration**
   ```bash
   flask db upgrade
   ```

## Integrating with Frontend

This backend supports integration with various frontend solutions:

- **Jinja2**: Default templating engine for server-side rendering.
- **Tailwind CSS**: Modern, utility-first styling.
- **Figma to Webflow**: Design in Figma, export to Webflow, and connect to this backend.
- **Headless Setup**: Expose API endpoints for frameworks like React or Vue.

To integrate a custom frontend:
- Modify routes and templates as needed.
- Create API endpoints for a headless architecture.

## Notes

- **`docs.md`**: Provides a detailed breakdown of the backend structure and components.
- **Grok3 Documentation**: Located in the `docs` folder, it explains how to extend the backend using XAi’s Grok3(https://grok.com/).
  - **WARNING**: These docs and system instructions are tailored for XAi Grok3 only. Compatibility with other LLMs is untested, and results cannot be guaranteed. We recommend using Grok3 from XAi for optimal development.

## Still In The Works

- **Flask-Mail**: Previously removed due to limitations. Future integrations will favor specific provider APIs (e.g., SendGrid, Mailgun) for robust email handling.

## Future Plans

Our vision is to evolve Verso Backend into a community-supported, Python-based CMS for businesses, led by founder Michael B. Zimmerman. We’re refining the architecture and will share a detailed roadmap soon. This template already offers a cost-effective, fast website solution—deployable on Heroku for just $7/month.

## Contributing

We welcome contributions! To get started:

1. Fork the repository.
2. Create a branch for your feature or bugfix.
3. Commit your changes.
4. Push to your branch.
5. Submit a pull request.

Ensure your code adheres to the project’s coding standards and includes tests where applicable.

## Support the Project

- **Contribute**: Submit pull requests or report issues on GitHub Issues.
- **Sponsor**: Support development via GitHub Sponsors or Patreon.
- **Share**: Spread the word on social media, forums, or X to boost visibility.

## Contributors

- **Michael Zimmerman**: Founder and CEO of Verso Industries, creator of HighNoon LLM and HSMN architecture, and Lead Developer.
- **Jacob Godina**: President and Co-Founder of Verso Industries, contributor to code, design, and marketing.

## Contact

- **Email**: `zimmermanmb99@gmail.com`
- **Website**: `www.versoindustries.com` (currently not live)

## Discord Server

Join our community: [https://discord.gg/pBrSPbaMnM](https://discord.gg/pBrSPbaMnM)

## License

This project is licensed under the [Apache License 2.0](LICENSE).