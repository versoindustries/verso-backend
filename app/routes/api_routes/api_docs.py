"""
Phase 9: API Documentation Routes

Serves OpenAPI spec and Swagger UI for interactive API documentation.
"""
from flask import Blueprint, render_template_string, send_from_directory, current_app
import os

api_docs = Blueprint('api_docs', __name__, url_prefix='/api')

# Swagger UI HTML template (uses CDN for simplicity, keeping sovereignty for actual API)
SWAGGER_UI_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Verso API Documentation</title>
    <link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist@5.9.0/swagger-ui.css">
    <style>
        body { margin: 0; padding: 0; }
        .topbar { display: none !important; }
        .swagger-ui .info { margin: 30px 0; }
        .swagger-ui .info .title { font-size: 2.5em; }
    </style>
</head>
<body>
    <div id="swagger-ui"></div>
    <script src="https://unpkg.com/swagger-ui-dist@5.9.0/swagger-ui-bundle.js"></script>
    <script>
        window.onload = function() {
            window.ui = SwaggerUIBundle({
                url: "{{ spec_url }}",
                dom_id: '#swagger-ui',
                presets: [
                    SwaggerUIBundle.presets.apis,
                    SwaggerUIBundle.SwaggerUIStandalonePreset
                ],
                layout: "BaseLayout",
                deepLinking: true,
                showExtensions: true,
                showCommonExtensions: true
            });
        };
    </script>
</body>
</html>
'''

# Code examples template
CODE_EXAMPLES_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Verso API - Code Examples</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 900px; margin: 0 auto; padding: 20px; line-height: 1.6; }
        h1 { color: #333; border-bottom: 2px solid #007bff; padding-bottom: 10px; }
        h2 { color: #555; margin-top: 40px; }
        h3 { color: #666; }
        pre { background: #1e1e1e; color: #dcdcdc; padding: 15px; border-radius: 5px; overflow-x: auto; }
        code { font-family: 'Fira Code', 'Source Code Pro', monospace; }
        .language-label { color: #007bff; font-size: 0.9em; margin-bottom: 5px; }
        .note { background: #e7f3ff; border-left: 4px solid #007bff; padding: 10px 15px; margin: 20px 0; }
        a { color: #007bff; }
    </style>
</head>
<body>
    <h1>Verso API Code Examples</h1>
    
    <div class="note">
        <strong>Base URL:</strong> <code>{{ base_url }}/api/v1</code><br>
        <strong>Authentication:</strong> Bearer token in Authorization header
    </div>
    
    <h2>Getting Started</h2>
    <p>Create an API key in Admin → API Keys with the appropriate scopes.</p>
    
    <h2>List Leads</h2>
    
    <h3>cURL</h3>
    <p class="language-label">bash</p>
    <pre><code>curl -X GET "{{ base_url }}/api/v1/leads?page=1&per_page=10" \\
  -H "Authorization: Bearer YOUR_API_KEY"</code></pre>
    
    <h3>Python</h3>
    <p class="language-label">python</p>
    <pre><code>import requests

API_KEY = "YOUR_API_KEY"
BASE_URL = "{{ base_url }}/api/v1"

response = requests.get(
    f"{BASE_URL}/leads",
    headers={"Authorization": f"Bearer {API_KEY}"},
    params={"page": 1, "per_page": 10}
)

data = response.json()
for lead in data["data"]:
    print(f"{lead['first_name']} {lead['last_name']} - {lead['email']}")</code></pre>
    
    <h3>JavaScript (fetch)</h3>
    <p class="language-label">javascript</p>
    <pre><code>const API_KEY = "YOUR_API_KEY";
const BASE_URL = "{{ base_url }}/api/v1";

async function getLeads() {
    const response = await fetch(`${BASE_URL}/leads?page=1&per_page=10`, {
        headers: {
            "Authorization": `Bearer ${API_KEY}`
        }
    });
    
    const data = await response.json();
    data.data.forEach(lead => {
        console.log(`${lead.first_name} ${lead.last_name} - ${lead.email}`);
    });
}

getLeads();</code></pre>

    <h2>Create a Lead</h2>
    
    <h3>cURL</h3>
    <p class="language-label">bash</p>
    <pre><code>curl -X POST "{{ base_url }}/api/v1/leads" \\
  -H "Authorization: Bearer YOUR_API_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{
    "first_name": "John",
    "last_name": "Doe",
    "email": "john@example.com",
    "phone": "+1-555-123-4567",
    "message": "Interested in your services"
  }'</code></pre>

    <h3>Python</h3>
    <p class="language-label">python</p>
    <pre><code>import requests

response = requests.post(
    f"{BASE_URL}/leads",
    headers={
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    },
    json={
        "first_name": "John",
        "last_name": "Doe",
        "email": "john@example.com",
        "phone": "+1-555-123-4567",
        "message": "Interested in your services"
    }
)

if response.status_code == 201:
    print(f"Lead created with ID: {response.json()['id']}")
else:
    print(f"Error: {response.json()['error']}")</code></pre>

    <h3>JavaScript</h3>
    <p class="language-label">javascript</p>
    <pre><code>async function createLead(leadData) {
    const response = await fetch(`${BASE_URL}/leads`, {
        method: "POST",
        headers: {
            "Authorization": `Bearer ${API_KEY}`,
            "Content-Type": "application/json"
        },
        body: JSON.stringify(leadData)
    });
    
    const result = await response.json();
    if (response.status === 201) {
        console.log(`Lead created with ID: ${result.id}`);
    } else {
        console.error(`Error: ${result.error}`);
    }
}

createLead({
    first_name: "John",
    last_name: "Doe", 
    email: "john@example.com",
    phone: "+1-555-123-4567",
    message: "Interested in your services"
});</code></pre>

    <h2>Update Order Status</h2>
    
    <h3>cURL</h3>
    <p class="language-label">bash</p>
    <pre><code>curl -X PATCH "{{ base_url }}/api/v1/orders/123" \\
  -H "Authorization: Bearer YOUR_API_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{
    "fulfillment_status": "shipped",
    "tracking_number": "1Z999AA10123456784"
  }'</code></pre>

    <h2>Webhook Verification</h2>
    <p>Webhooks include an HMAC signature in the <code>X-Webhook-Signature</code> header.</p>
    
    <h3>Python</h3>
    <p class="language-label">python</p>
    <pre><code>import hmac
import hashlib

def verify_webhook(payload_bytes, signature, secret):
    """Verify webhook signature."""
    expected = hmac.new(
        secret.encode('utf-8'),
        payload_bytes,
        hashlib.sha256
    ).hexdigest()
    
    # Signature format: sha256=hexdigest
    if signature.startswith('sha256='):
        signature = signature[7:]
    
    return hmac.compare_digest(expected, signature)

# In your webhook handler:
# signature = request.headers.get('X-Webhook-Signature')
# is_valid = verify_webhook(request.data, signature, YOUR_WEBHOOK_SECRET)</code></pre>

    <p style="margin-top: 40px;">
        <a href="/api/docs">← Back to Interactive Documentation</a>
    </p>
</body>
</html>
'''


@api_docs.route('/docs')
def swagger_ui():
    """Serve Swagger UI for interactive API documentation."""
    spec_url = '/api/openapi.yaml'
    return render_template_string(SWAGGER_UI_TEMPLATE, spec_url=spec_url)


@api_docs.route('/openapi.yaml')
def openapi_spec():
    """Serve the OpenAPI specification file."""
    static_folder = os.path.join(current_app.root_path, 'static')
    return send_from_directory(static_folder, 'openapi.yaml', mimetype='text/yaml')


@api_docs.route('/examples')
def code_examples():
    """Serve code examples page."""
    base_url = current_app.config.get('BASE_URL', 'http://localhost:5000')
    return render_template_string(CODE_EXAMPLES_TEMPLATE, base_url=base_url)
