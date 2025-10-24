from flask import Flask
import requests
import os

app = Flask(__name__)

# This will be the internal DNS name of our backend service in Kubernetes
# For now, we'll use an environment variable with a default
BACKEND_URL = os.getenv('BACKEND_URL', 'http://localhost:4001')

@app.route('/', methods=['GET'])
def index():
    """
    Calls the greeting-service and displays the result
    """
    try:
        # Make HTTP request to the backend
        response = requests.get(f'{BACKEND_URL}/greet', timeout=5)
        response.raise_for_status()
        
        data = response.json()
        message = data.get('message', 'No message')
        pod = data.get('pod', 'unknown')
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Microservices Demo</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    max-width: 600px;
                    margin: 50px auto;
                    padding: 20px;
                    background-color: #f0f0f0;
                }}
                .container {{
                    background-color: white;
                    padding: 30px;
                    border-radius: 10px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }}
                h1 {{ color: #333; }}
                .message {{ 
                    font-size: 24px; 
                    color: #007bff;
                    margin: 20px 0;
                }}
                .pod-info {{
                    font-size: 14px;
                    color: #666;
                    margin-top: 20px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🚀 Kubernetes Microservices Demo</h1>
                <div class="message">{message}</div>
                <div class="pod-info">
                    <strong>Backend Pod:</strong> {pod}
                </div>
            </div>
        </body>
        </html>
        """
        return html
        
    except requests.exceptions.RequestException as e:
        error_html = f"""
        <!DOCTYPE html>
        <html>
        <head><title>Error</title></head>
        <body>
            <h1>❌ Error Connecting to Backend</h1>
            <p>Could not reach the greeting-service at {BACKEND_URL}</p>
            <p>Error: {str(e)}</p>
        </body>
        </html>
        """
        return error_html, 500

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return "OK", 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
