# Production Deployment Guide

This guide covers how to deploy the Verso-Backend application and manage its background worker process in a production environment.

## Background Worker

The application requires a separate background process to handle tasks such as email sending. This process runs via the command:

```bash
flask run-worker
```

This command **must be running continuously** for background tasks to be processed. Below are two common methods to manage this process in production: **Supervisor** and **Systemd**.

### Option 1: Supervisor (Recommended)

Supervisor is a popular process control system for UNIX-like operating systems. It is robust and easy to configure for Python web applications.

1.  **Install Supervisor:**
    ```bash
    sudo apt-get update
    sudo apt-get install supervisor
    ```

2.  **Create a Configuration File:**
    Create a file named `/etc/supervisor/conf.d/verso-worker.conf`:

    ```ini
    [program:verso-worker]
    command=/path/to/your/venv/bin/flask run-worker
    directory=/path/to/your/app
    user=www-data
    autostart=true
    autorestart=true
    stopasgroup=true
    killasgroup=true
    stderr_logfile=/var/log/verso-worker.err.log
    stdout_logfile=/var/log/verso-worker.out.log
    environment=FLASK_APP="app",DATABASE_URL="postgresql://user:pass@localhost/dbname",SECRET_KEY="your_secret_key"
    ```

    *Replace `/path/to/your/venv`, `/path/to/your/app`, and environment variables with your actual values.*

3.  **Update Supervisor:**
    ```bash
    sudo supervisorctl reread
    sudo supervisorctl update
    ```

4.  **Check Status:**
    ```bash
    sudo supervisorctl status
    ```

### Option 2: Systemd

Systemd is the standard init system for most modern Linux distributions (Ubuntu 16.04+, CentOS 7+, Debian 8+).

1.  **Create a Service File:**
    Create a file named `/etc/systemd/system/verso-worker.service`:

    ```ini
    [Unit]
    Description=Verso Background Worker
    After=network.target

    [Service]
    User=www-data
    Group=www-data
    WorkingDirectory=/path/to/your/app
    Environment="PATH=/path/to/your/app/venv/bin"
    Environment="FLASK_APP=app"
    Environment="DATABASE_URL=postgresql://user:pass@localhost/dbname"
    # Load other env vars or use EnvironmentFile
    # EnvironmentFile=/path/to/your/app/.env
    ExecStart=/path/to/your/app/venv/bin/flask run-worker
    Restart=always

    [Install]
    WantedBy=multi-user.target
    ```

2.  **Enable and Start the Service:**
    ```bash
    sudo systemctl daemon-reload
    sudo systemctl start verso-worker
    sudo systemctl enable verso-worker
    ```

3.  **Check Status:**
    ```bash
    sudo systemctl status verso-worker
    ```

### Option 3: Heroku

Heroku uses a `Procfile` to manage processes.

1.  **Update Procfile:**
    Ensure your `Procfile` includes both the web server and the worker process:

    ```text
    web: gunicorn "app:create_app()"
    worker: flask run-worker
    ```

2.  **Deploy:**
    Push your changes to Heroku as usual.

3.  **Scale Worker Dyno:**
    By default, only the web dyno might be active. You need to verify and scale the worker dyno:

    ```bash
    heroku ps:scale worker=1
    ```

4.  **Monitor:**
    View logs to ensure the worker is processing tasks:

    ```bash
    heroku logs --tail -p worker
    ```

## Web Server

For the web application itself, use a production WSGI server like Gunicorn behind Nginx.

**Gunicorn Command:**
```bash
gunicorn -w 4 -b 0.0.0.0:8000 "app:create_app()"
```

**Nginx Configuration Example:**
```nginx
server {
    listen 80;
    server_name example.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```
