import os

from app import create_app  # You'll create a create_app function in __init__.py

app = create_app()

if __name__ == '__main__':
    # Bind to all interfaces so the server is reachable from other devices.
    host = '0.0.0.0'
    port = int(os.environ.get('PORT', 5000))
    app.run(host=host, port=port, debug=False)
