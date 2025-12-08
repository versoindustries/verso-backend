# How to Extend Verso Backend

This guide provides instructions for developers looking to add new features, routes, or models to the Verso Backend application.

## Project Structure

- **`app/`**: Core application logic.
  - **`__init__.py`**: Flask app factory and extension initialization.
  - **`models.py`**: SQLAlchemy database models.
  - **`forms.py`**: Flask-WTF forms.
  - **`routes/`**: Blueprints for different implementation areas (e.g., `admin`, `auth`, `main`).
  - **`modules/`**: Helper modules and business logic (e.g., `file_manager.py`).
  - **`templates/`**: Jinja2 HTML templates.
  - **`static/`**: CSS, JavaScript, and images.

## Adding a New Route

1. **Create a Blueprint**:
   If adding a major feature, create a new file in `app/routes/` (e.g., `app/routes/feature.py`).
   ```python
   from flask import Blueprint, render_template

   feature_bp = Blueprint('feature', __name__, url_prefix='/feature')

   @feature_bp.route('/')
   def index():
       return render_template('feature/index.html')
   ```

2. **Register the Blueprint**:
   In `app/__init__.py`, import and register your new blueprint.
   ```python
   from app.routes.feature import feature_bp
   app.register_blueprint(feature_bp)
   ```

3. **Add Templates**:
   Create a corresponding directory in `app/templates/` (e.g., `app/templates/feature/`) and add your HTML files. Extend `base.html` for consistency.

## Adding a New Model

1. **Define the Model**:
   Add your class to `app/models.py`. Inherit from `db.Model`.
   ```python
   class NewModel(db.Model):
       id = db.Column(db.Integer, primary_key=True)
       name = db.Column(db.String(100), nullable=False)
       created_at = db.Column(db.DateTime, default=datetime.utcnow)
   ```

2. **Create Migration**:
   Run the following commands to generate and apply the migration.
   ```bash
   flask db migrate -m "Add NewModel"
   flask db upgrade
   ```

## Adding a Form

1. **Define the Form**:
   Add your form class to `app/forms.py`. Inherit from `FlaskForm`.
   ```python
   from flask_wtf import FlaskForm
   from wtforms import StringField, SubmitField
   from wtforms.validators import DataRequired

   class NewFeatureForm(FlaskForm):
       name = StringField('Name', validators=[DataRequired()])
       submit = SubmitField('Save')
   ```

2. **Use in Route**:
   Import and instantiate the form in your route handler.
   ```python
   from app.forms import NewFeatureForm

   @feature_bp.route('/new', methods=['GET', 'POST'])
   def new():
       form = NewFeatureForm()
       if form.validate_on_submit():
           # Save logic here
           pass
       return render_template('feature/new.html', form=form)
   ```

## Adding a Background Task

1. **Define Task Logic**:
   Add your logic to `app/worker.py` or a dedicated module.

2. **Enqueue Task**:
   Use the `Task` model to schedule work.
   ```python
   from app.models import Task
   
   task = Task(
       name='send_email',
       payload={'to': 'user@example.com', 'subject': 'Hello'},
       status='pending'
   )
   db.session.add(task)
   db.session.commit()
   ```

## Testing

- **Run Tests**: Use `pytest` (or `make test` if available) to run the test suite.
- **Manual Testing**: verify all flows in a local environment before pushing.
