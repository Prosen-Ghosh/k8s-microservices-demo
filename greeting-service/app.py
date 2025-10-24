from flask import Flask, jsonify
import os
import socket

app = Flask(__name__)

# Read greeting message from environment variable with a default fallback
GREETING_MSG = os.getenv('GREETING_MSG', 'Hello from the Backend!')

@app.route('/greet', methods=['GET'])
def greet():
    """
    Returns a greeting message with the pod hostname
    """
    hostname = socket.gethostname()
    greeting = {
        "message": GREETING_MSG,  # Now uses the environment variable
        "pod": hostname,
        "version": "v3"  # Bumped version
    }
    return jsonify(greeting)

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=4001)