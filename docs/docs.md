# Documentation for Flask Template Repository

This document provides an overview of the Flask web application template, explains the directory structure, and guides you on how to set up the environment, understand key components, and make changes to the codebase.

## Overview

This repository contains a Flask web application template designed as a foundation for building web applications. It includes features such as user authentication, role-based access control, appointment booking, and basic content management (e.g., blog). The template is modular, extensible, and configured for deployment on platforms like Heroku.

## Directory Structure

The repository is organized as follows:

- **`app/`**: Core application directory
  - **`static/`**: Static assets
    - `js/`: JavaScript files (e.g., `slider.js` for carousel, `calendar.js` for appointment scheduling)
    - `css/`: Stylesheets
    - `images/`: Image assets (e.g., gallery images)
  - **`templates/`**: HTML templates for rendering pages (e.g., `index.html`, `admin/dashboard.html`)
  - **`models.py`**: Defines database models (e.g., `User`, `Role`, `Appointment`)
  - **`forms.py`**: Form definitions for user input (e.g., `RegistrationForm`, `EstimateRequestForm`)
  - **`routes/`**: Routing logic organized into blueprints
    - `main_routes.py`: Handles main pages (e.g., homepage, contact)
    - `admin.py`: Admin dashboard and management routes
    - `auth.py`: Authentication routes (e.g., login, register)
    - `user.py`: User dashboard routes
    - `blog.py`: Blog-related routes
  - **`modules/`**: Utility modules
    - `role_setup.py`: Creates default roles
    - `file_manager.py`: File handling utilities
    - `locations.py`: Location data for maps
    - `indexing.py`: Sitemap generation and submission
    - `auth_manager.py`: Role-based access control decorators
  - **`config.py`**: Configuration settings (e.g., database URI)
  - **`database.py`**: Initializes SQLAlchemy database
  - **`extensions.py`**: Initializes Flask extensions (e.g., Flask-Login, CSRF)
  - **`__init__.py`**: Application factory for Flask app creation

- **`directory_ai.py`, `directory_html.py`, `directory_markdown.py`**: Scripts for generating directory documentation
- **`.gitattributes`, `.gitignore`, `.slugignore`**: Git and deployment configuration files
- **`LICENSE`**: Apache License 2.0
- **`Procfile`**: Heroku deployment configuration
- **`run.py`**: Entry point to run the Flask application locally
- **`.env`**: Environment variables (not committed to Git)

## Setup

To set up the development environment:

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/yourusername/verso-backend.git
   cd verso-backend
   ```

2. **Install Dependencies**:
   Ensure Python 3.8+ is installed, then run:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set Up Environment Variables**:
   Create a `.env` file in the root directory with:
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

4. **Initialize the Database**:
   ```bash
   flask db init
   flask db migrate
   flask db upgrade
   ```

5. **Create Default Roles**:
   ```bash
   flask create-roles
   ```

6. **Run the Application**:
   ```bash
   python run.py
   ```
   Access the app at `http://localhost:5000`.

## Key Components

### Models (`app/models.py`)

Defines database tables using SQLAlchemy:
- **`User`**: User accounts with fields like `username`, `email`, `password_hash`, and role relationships.
- **`Role`**: User roles (e.g., `admin`, `user`, `commercial`).
- **`Service`**: Services offered by the application.
- **`Appointment`**: Booking details with timezone-aware `preferred_date_time`.
- **`Estimator`**: Individuals handling appointments.
- **`ContactFormSubmission`**: Stores contact form submissions.

### Forms (`app/forms.py`)

Handles user input validation with Flask-WTF:
- **`RegistrationForm`**: User sign-up with role selection.
- **`LoginForm`**: User login.
- **`EstimateRequestForm`**: Appointment booking with date and time selection.
- **`ContactForm`**: Contact form submissions.

### Routes (`app/routes/`)

Organized into blueprints:
- **`main_routes.py`**:
  - `/`: Homepage with gallery.
  - `/request_estimate`: Appointment booking endpoint.
  - `/contact`: Contact form handling.
- **`admin.py`**:
  - `/admin/dashboard`: Admin dashboard with appointment and user stats.
  - `/admin/user-management`: Manage users and roles.
- **`auth.py`**:
  - `/register`, `/login`, `/logout`: Authentication routes.
- **`user.py`**:
  - `/dashboard`: User dashboard.
  - `/dashboard/commercial`: Commercial user dashboard.
- **`blog.py`**:
  - `/blog`: Blog page and individual posts.

### Templates (`app/templates/`)

Jinja2 HTML templates rendered by routes, organized by blueprint (e.g., `auth/register.html`).

### Static Files (`app/static/`)

- **`js/`**: Client-side scripts (e.g., `slider.js` for carousel, `calendar.js` for FullCalendar integration).
- **`css/`**: Stylesheets.
- **`images/`**: Static images.

### Modules (`app/modules/`)

Utility functions:
- **`role_setup.py`**: Initializes roles.
- **`file_manager.py`**: File operations (e.g., checking allowed extensions).
- **`locations.py`**: Provides geographic data.
- **`indexing.py`**: Generates and submits sitemaps.
- **`auth_manager.py`**: Decorators like `admin_required`.

## Making Changes

### Adding a New Route

1. Open the relevant blueprint file (e.g., `app/routes/main_routes.py`).
2. Add a new route:
   ```python
   @main.route('/new-page')
   def new_page():
       return render_template('new_page.html')
   ```
3. Create a corresponding template in `app/templates/new_page.html`.

### Adding a New Model

1. Edit `app/models.py`:
   ```python
   class NewModel(db.Model):
       id = db.Column(db.Integer, primary_key=True)
       name = db.Column(db.String(100), nullable=False)
   ```
2. Generate and apply migrations:
   ```bash
   flask db migrate -m "Added NewModel"
   flask db upgrade
   ```

### Adding a New Form

1. Edit `app/forms.py`:
   ```python
   class NewForm(FlaskForm):
       field = StringField('Field', validators=[DataRequired()])
       submit = SubmitField('Submit')
   ```
2. Use it in a route:
   ```python
   @main.route('/new-form', methods=['GET', 'POST'])
   def new_form():
       form = NewForm()
       if form.validate_on_submit():
           # Process form data
           return redirect(url_for('main_routes.index'))
       return render_template('new_form.html', form=form)
   ```

### Modifying Templates

Edit HTML files in `app/templates/` to adjust layout or content. Use Jinja2 syntax for dynamic data:
```html
<h1>Welcome, {{ current_user.username }}!</h1>
```

### Updating Static Files

Modify files in `app/static/`:
- Add CSS in `static/css/`.
- Update JavaScript in `static/js/` (e.g., enhance `slider.js`).
- Replace images in `static/images/`.

### Adding a New Feature (e.g., Blog Post)

1. Add a route in `app/routes/blog.py`:
   ```python
   @blog_blueprint.route('/blog/new-post')
   def new_post():
       return render_template('new_post.html')
   ```
2. Create `app/templates/new_post.html`.
3. Update sitemap in `app/modules/indexing.py` if public.

## Deployment

The app is configured for Heroku:
1. Install Heroku CLI and log in:
   ```bash
   heroku login
   ```
2. Create a Heroku app:
   ```bash
   heroku create your-app-name
   ```
3. Set environment variables in Heroku:
   ```bash
   heroku config:set SECRET_KEY=your_key DATABASE_URL=your_db_url
   ```
4. Deploy:
   ```bash
   git push heroku main
   ```
5. Run migrations:
   ```bash
   heroku run "flask db upgrade"
   ```

The `Procfile` specifies:
```
web: gunicorn "app:create_app()"
```

## Additional Notes

- **Timezone Handling**: Uses `pytz` for UTC storage and local conversions (see `Appointment` model and `main_routes.py`).
- **JavaScript Features**: `slider.js` includes touch support and auto-sliding; `calendar.js` integrates FullCalendar for appointments.
- **Security**: CSRF protection via Flask-WTF and password hashing with Bcrypt.

This documentation should help you navigate and extend your Flask template repository effectively. For further questions, refer to the code comments or open an issue on GitHub.