# Verso Backend

**Verso Backend** is a Flask-based backend template designed for easy deployment on Heroku. It provides a robust foundation for building web applications with features like user authentication, database models, forms, and email support. This template is highly extensible and can integrate with various frontend frameworks or templating engines, such as Jinja2, Tailwind CSS, or Figma-to-Webflow pages.

## Features

- **User Authentication**: Registration, login, password reset, and role-based access control.
- **Database Models**: Predefined models for users, roles, appointments, and more using SQLAlchemy.
- **Forms**: WTForms for handling user input and validation.
- **Email Support**: Configured with Flask-Mail for sending emails (e.g., password resets).
- **Admin Interface**: Basic admin dashboard for managing users and appointments.
- **User Dashboard**: User dashboard that replaces the homepage once logged in. Once someone has registered, the homepage (index.html) serves no purpose to the end user. As long as the user is logged in, the 
- **Heroku Ready**: Pre-configured for deployment on Heroku.
- **Modular Design**: Easily extendable with additional routes, models, and features.
- **AppointQix**: A Verso Industries native appointments integrated directly in.

## Prerequisites

- **Python 3.10.11** (ensure this version is installed)
- **pip** (Python package installer)
- **Virtualenv** (recommended for isolating dependencies)

## Setup Instructions

Follow these steps to set up the project locally:

1. **Clone the Repository**
   ```bash
   git clone https://github.com/yourusername/verso-backend.git
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

7. **Run Database Migrations**
   ```bash
   flask db init
   flask db migrate
   flask db upgrade
   ```

8. **Create Default Roles**
   ```bash
   flask create-roles
   ```

9. **Run the Application**
   ```bash
   flask run --host=0.0.0.0 --debug
   ```
   - **Note**: The `--host=0.0.0.0` flag allows LAN connections for local development only. Use with caution and never in production.

10. **Set Admin User**
    - After registering an account via the web application, set the user as admin:
      ```bash
      flask set-admin dude@setadmin.com
      ```
    - Replace `dude@setadmin.com` with the email you used during registration.

## Deployment to Heroku

To deploy the application on Heroku:

1. **Create a Heroku App**
   ```bash
   heroku create your-app-name
   ```

2. **Set Environment Variables on Heroku**
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
   - Replace placeholders (`your_secret_key`, `your_database_url`, etc.) with appropriate values.

3. **Push to Heroku**
   ```bash
   git push heroku main
   ```

4. **Run Migrations on Heroku**
   ```bash
   heroku run flask db upgrade
   ```

5. **Create Default Roles on Heroku**
   ```bash
   heroku run flask create-roles
   ```

Or link your heroku account to your github repo and push it live directly from GitHub.

## Usage

- Access the application at `http://localhost:5000` (or your Heroku app URL).
- Register a new user account via the registration page.
- Use the admin command to set a user as an admin (as shown in the setup instructions).
- Explore the dashboard and features based on user roles (e.g., admin, commercial, user).

## Notes on Database Migrations

When updating `models.py` or `forms.py`, update the database schema as follows:

1. **Shut down the server** (press `Ctrl + C`).
2. **Generate a migration**:
   ```bash
   flask db migrate -m "Description of changes"
   ```
3. **Apply the migration**:
   ```bash
   flask db upgrade
   ```

## Integrating with Frontend

This backend template is designed to work with any frontend framework or templating engine:

- **Jinja2**: Default templating engine for Flask.
- **Tailwind CSS**: For modern, utility-first styling.
- **Figma to Webflow**: Design in Figma, export to Webflow, and integrate with this backend.

To integrate with a custom frontend:
- Update routes and templates as needed.
- Expose API endpoints for a headless setup if preferred.

## Notes

Docs.md is a breakdown and explanation of the backend. 

In the docs folder, we will have documentation on how to effectively build this out using Grok3. 
   - **WARNING**: LLM docs and system instructions are specifically tailored to work with XAi Grok3 only. It is untested with any other LLM provider, thus we cannot guarentee results. We strongly reccomend utilizing Grok3 from XAi to build this out. Refer to the docs for the rest.

## Still In The Works

- **Flask Mail**: Not a great solution and was removed sometime in use last year. Integrations would be better served under specific provider APIs.

## Future Plans

The goal with the Verso Backend is to open community support to actively build with our founder, Michael B. Zimmerman, and create a new Python based cms for businesses. We are still working out the architecture and structure, we will be sharing a more solid vision here in the next few days. Documentation needs to be parsed through, still a few decisions to make. This already breaks down quite a few barriers and offers a faster website option, on heroku it's only $7/month. 

## Contributing

Contributions are welcome! To contribute:

1. Fork the repository.
2. Create a new branch for your feature or bugfix.
3. Commit your changes.
4. Push to your branch.
5. Create a pull request.

Please ensure your code follows the project’s coding standards and includes appropriate tests.

## Support the Project

- **Contribute**: Submit pull requests or report issues on GitHub Issues.
- **Sponsor**: Support development via GitHub Sponsors or Patreon.
- **Share**: Promote Verso Backend on social media, forums, or X to increase visibility.

## Contributors

- **Michael Zimmerman**: Founder and CEO of Verso Industries, creator of HighNoon LLM and the HSMN architecture, and Lead Developer for the project.
- **Jacob Godina**: President and Co-Founder of Verso Industries, contributor to code, design, and marketing.

## Contact

- **Email**: `zimmermanmb99@gmail.com`
- **Website**: `www.versoindustries.com` (currently not live)
- **Commercial Licensing**: See `COMMERCIAL-LICENSE.md`

## Discord Server

https://discord.gg/pBrSPbaMnM

## License

This project is licensed under the [Apache License 2.0](LICENSE).