# Verso Backend Template Repository Documentation

Welcome to the Flask Template Repository! This document is designed for first-time users to help you understand, set up, and customize this Flask-based web application template. Whether you're building a simple site or a complex application with user authentication and appointment booking, this guide will get you started.

## Overview

This Flask template provides a robust starting point for web applications. Key features include:

- **User Authentication**: Login, registration, and password reset functionality.
- **Role-Based Access Control**: Different permissions for `admin`, `user`, `commercial`, and `blogger` roles.
- **Appointment Booking**: Schedule appointments with timezone support using FullCalendar.
- **Blog System**: Create and manage blog posts with image support.
- **Modular Design**: Organized with blueprints for easy extension.
- **Heroku Deployment**: Ready-to-deploy configuration.

The template uses Flask, SQLAlchemy, Flask-Login, Flask-WTF, and other libraries to provide a secure and scalable foundation.

## Directory Structure

Here's how the repository is organized:

- **`app/`**: Core application directory
  - **`static/`**: Static assets
    - `js/`: JavaScript files (e.g., `calendar.js` for appointments, `slider.js` for carousels)
    - `css/`: Stylesheets
    - `images/`: Image assets (e.g., gallery images)
  - **`templates/`**: Jinja2 HTML templates (e.g., `index.html`, `admin/dashboard.html`)
  - **`models.py`**: Database models (e.g., `User`, `Appointment`, `Post`)
  - **`forms.py`**: Form definitions (e.g., `RegistrationForm`, `EstimateRequestForm`)
  - **`routes/`**: Blueprint-based routing
    - `main_routes.py`: Homepage, contact, and estimate requests
    - `admin.py`: Admin dashboard and management
    - `auth.py`: Authentication endpoints
    - `user.py`: User dashboards
    - `blog.py`: Blog functionality
  - **`modules/`**: Utility scripts
    - `role_setup.py`: Sets up default roles
    - `file_manager.py`: File handling utilities
    - `locations.py`: Geographic data
    - `indexing.py`: Sitemap generation
    - `auth_manager.py`: Role-based decorators
  - **`config.py`**: Configuration settings
  - **`database.py`**: SQLAlchemy initialization
  - **`extensions.py`**: Flask extension setup
  - **`__init__.py`**: Application factory

- **`directory_ai.py`**: Script to generate directory documentation
- **`.gitattributes`, `.gitignore`, `.slugignore`**: Git and deployment configs
- **`LICENSE`**: Apache License 2.0
- **`Procfile`**: Heroku process definition
- **`run.py`**: Local run script
- **`.env`**: Environment variables (not in Git)

## Setup

Follow these steps to get the application running locally:

1. **Clone the Repository**
   ```bash
   git clone https://github.com/yourusername/flask-template-repo.git
   cd flask-template-repo
   ```

2. **Install Python and Dependencies**
   - Ensure Python 3.8+ is installed.
   - Install required packages:
     ```bash
     pip install -r requirements.txt
     ```
   *Note*: If `requirements.txt` is missing, install core dependencies like `flask`, `flask-sqlalchemy`, `flask-login`, `flask-wtf`, `flask-bcrypt`, `flask-migrate`, `python-dotenv`, and `gunicorn`.

3. **Configure Environment Variables**
   - Create a `.env` file in the root directory:
     ```
     FLASK_APP=app
     SECRET_KEY=your_random_secure_key_here
     DATABASE_URL=sqlite:///mydatabase.sqlite
     MAIL_SERVER=smtp.yourmailserver.com
     MAIL_PORT=587
     MAIL_USE_TLS=True
     MAIL_USERNAME=your_email@example.com
     MAIL_PASSWORD=your_email_password
     MAIL_DEFAULT_SENDER=your_email@example.com
     ```
   - Replace values with your own (e.g., generate a secure `SECRET_KEY` using `os.urandom(24).hex()` in Python).

4. **Initialize the Database**
   - Run these commands to set up the database:
     ```bash
     flask db init
     flask db migrate
     flask db upgrade
     ```

5. **Set Up Default Roles**
   - Create default roles (`admin`, `user`, `commercial`, `blogger`):
     ```bash
     flask create-roles
     ```

6. **Seed Business Configuration (Optional)**
   - Add default business settings (e.g., timezone, hours):
     ```bash
     flask seed-business-config
     ```

7. **Run the Application**
   - Start the development server:
     ```bash
     python run.py
     ```
   - Open `http://localhost:5000` in your browser.

## Key Components

### Database Models (`app/models.py`)

- **`User`**: Stores user info (`username`, `email`, `password_hash`) and links to roles.
- **`Role`**: Defines roles for access control.
- **`Appointment`**: Manages bookings with UTC timestamps.
- **`Service`**: Lists available services.
- **`Estimator`**: Tracks staff handling appointments.
- **`Post`**: Blog post data with images.
- **`ContactFormSubmission`**: Stores contact form entries.

### Forms (`app/forms.py`)

- **`RegistrationForm`**: Sign-up with role selection.
- **`LoginForm`**: User login.
- **`EstimateRequestForm`**: Book appointments.
- **`CreatePostForm`**: Add blog posts with CKEditor.

### Routes (`app/routes/`)

- **Main (`main_routes.py`)**: Homepage, contact, and estimate requests.
- **Auth (`auth.py`)**: Login, registration, logout.
- **User (`user.py`)**: User and commercial dashboards.
- **Admin (`admin.py`)**: Management interface for users, roles, and settings.
- **Blog (`blog.py`)**: Blog post creation and display.

### Templates (`app/templates/`)

- Organized by blueprint (e.g., `auth/login.html`, `blog/post.html`).
- Use Jinja2 for dynamic content: `{{ variable }}`.

### Static Files (`app/static/`)

- **`js/calendar.js`**: Powers the appointment calendar with FullCalendar.
- **`js/slider.js`**: Runs the homepage image carousel.
- **`css/`**: Custom styles.
- **`images/`**: Static assets.

## Making Changes

### Adding a New Route

1. Open `app/routes/main_routes.py` (or another blueprint).
2. Add a route:
   ```python
   @main.route('/hello')
   def hello():
       return render_template('hello.html', message='Hello, World!')
   ```
3. Create `app/templates/hello.html`:
   ```html
   <h1>{{ message }}</h1>
   ```

### Adding a New Model

1. Edit `app/models.py`:
   ```python
   class Note(db.Model):
       id = db.Column(db.Integer, primary_key=True)
       content = db.Column(db.String(255), nullable=False)
   ```
2. Update the database:
   ```bash
   flask db migrate -m "Added Note model"
   flask db upgrade
   ```

### Adding a New Form

1. Edit `app/forms.py`:
   ```python
   class NoteForm(FlaskForm):
       content = StringField('Note', validators=[DataRequired()])
       submit = SubmitField('Save')
   ```
2. Use it in a route (`app/routes/main_routes.py`):
   ```python
   @main.route('/add-note', methods=['GET', 'POST'])
   def add_note():
       form = NoteForm()
       if form.validate_on_submit():
           note = Note(content=form.content.data)
           db.session.add(note)
           db.session.commit()
           return redirect(url_for('main_routes.index'))
       return render_template('add_note.html', form=form)
   ```

### Modifying Templates

- Edit `app/templates/index.html`:
  ```html
  <p>Welcome, {{ current_user.username if current_user.is_authenticated else 'Guest' }}!</p>
  ```

### Updating Static Files

- Add a style in `app/static/css/style.css`:
  ```css
  .welcome { color: blue; }
  ```
- Update `slider.js` for faster slides:
  ```javascript
  var slideInterval = setInterval(function() { moveSlide(1); }, 2000); // 2 seconds
  ```

### Adding a Blog Post Feature

1. Use the existing `blog.py` routes or enhance them:
   ```python
   @blog_blueprint.route('/blog/quick-post', methods=['POST'])
   @login_required
   @blogger_required
   def quick_post():
       title = request.form['title']
       content = request.form['content']
       post = Post(title=title, content=content, author_id=current_user.id, slug=title.lower().replace(' ', '-'), is_published=True)
       db.session.add(post)
       db.session.commit()
       return redirect(url_for('blog.show_blog'))
   ```
2. Add a form in `app/templates/blog/quick_post.html`.

## Deployment

To deploy on Heroku:

1. **Install Heroku CLI**
   ```bash
   heroku login
   ```

2. **Create a Heroku App**
   ```bash
   heroku create my-flask-app
   ```

3. **Set Environment Variables**
   ```bash
   heroku config:set SECRET_KEY=your_key DATABASE_URL=postgresql://your_db_info
   heroku config:set MAIL_SERVER=smtp.example.com MAIL_PORT=587 MAIL_USE_TLS=True
   heroku config:set MAIL_USERNAME=your_email MAIL_PASSWORD=your_pass MAIL_DEFAULT_SENDER=your_email
   ```

4. **Push to Heroku**
   ```bash
   git push heroku main
   ```

5. **Run Migrations**
   ```bash
   heroku run "flask db upgrade"
   ```

6. **Open the App**
   ```bash
   heroku open
   ```

The `Procfile` ensures Gunicorn runs the app:
```
web: gunicorn "app:create_app()"
```

## Additional Notes

- **Timezone Handling**: Appointments use UTC storage with `pytz` for conversions (see `models.py` and `main_routes.py`).
- **Security**: CSRF protection (Flask-WTF) and password hashing (Bcrypt) are built-in.
- **JavaScript Features**:
  - `calendar.js`: Integrates FullCalendar with touch support.
  - `slider.js`: Supports touch swipes and auto-sliding.

For more details, check code comments or file an issue on GitHub. Happy coding!