import click
from flask.cli import with_appcontext
from app.worker import run_worker

@click.command('run-worker')
@with_appcontext
def run_worker_command():
    """Run the background worker."""
    run_worker()
