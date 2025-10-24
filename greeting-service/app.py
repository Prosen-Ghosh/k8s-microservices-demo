from flask import Flask, jsonify
import os
import socket

app = Flask(__name__)

@app.route('/greet', methods=['GET'])
def greet():
    """
    Returns a greeting message with the pod hostname
    (useful later to see load balancing in action)
    """
    hostname = socket.gethostname()
    greeting = {
        "message": "Hello from the UPDATED Backend! 🚀",  # Changed this line
        "pod": hostname,
        "version": "v2" 
    }
    return jsonify(greeting)

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy"}), 200

if __name__ == '__main__':
    # Listen on all interfaces (0.0.0.0) so Docker can access it
    app.run(host='0.0.0.0', port=4001)
