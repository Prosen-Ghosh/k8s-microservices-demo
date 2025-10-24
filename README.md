# k8s-microservices-demo

This project is a comprehensive demonstration of a microservices application running on Kubernetes, covering containerization, deployment, scaling, and updates.

## Table of Contents

*   [Phase 1: Containerize the Microservices](#phase-1-containerize-the-microservices)
    *   [Step 1: Create the Application Code](#step-1-create-the-application-code)
    *   [Step 2: Create Dockerfiles](#step-2-create-dockerfiles)
    *   [Step 3: Build and Run Locally with Docker](#step-3-build-and-run-locally-with-docker)
*   [Phase 2: Deploy to Kubernetes](#phase-2-deploy-to-kubernetes)
    *   [Step 4: Introduction to Core Kubernetes Objects](#step-4-introduction-to-core-kubernetes-objects)
    *   [Step 5: Create Kubernetes Deployments](#step-5-create-kubernetes-deployments)
    *   [Step 6: Create Kubernetes Services](#step-6-create-kubernetes-services)
    *   [Step 7: Deploy to the Cluster](#step-7-deploy-to-the-cluster)
*   [Phase 3: Advanced Concepts & Day-2 Operations](#phase-3-advanced-concepts--day-2-operations)
    *   [Step 8: Scaling and Updates](#step-8-scaling-and-updates)

---

## Phase 1: Containerize the Microservices

### Step 1: Create the Application Code

**Why This Step?**
We're creating two simple microservices that work together. This teaches you the fundamental pattern of microservices architecture: small, independent services that communicate over HTTP. The `greeting-service` (backend) does one job—generating greetings. The `web-service` (frontend) calls the backend and presents the result to users.
I'll use Python with Flask since it's beginner-friendly and requires minimal boilerplate.

**How the Services Communicate**
*   The `web-service` will make an HTTP GET request to `greeting-service`
*   The `greeting-service` will respond with a JSON message
*   The `web-service` will display this to the user in their browser

**Create the Project Structure**
First, let's create directories for our project:
```bash
mkdir -p k8s-microservices/greeting-service
mkdir -p k8s-microservices/web-service
cd k8s-microservices
```

**greeting-service (Backend)**
Create the file `greeting-service/app.py`:
```python
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
        "message": "Hello from the Backend!",
        "pod": hostname
    }
    return jsonify(greeting)

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy"}), 200

if __name__ == '__main__':
    # Listen on all interfaces (0.0.0.0) so Docker can access it
    app.run(host='0.0.0.0', port=5000)
```

Create the file `greeting-service/requirements.txt`:
```
flask==3.0.0
```

**web-service (Frontend)**
Create the file `web-service/app.py`:
```python
from flask import Flask
import requests
import os

app = Flask(__name__)

# This will be the internal DNS name of our backend service in Kubernetes
# For now, we'll use an environment variable with a default
BACKEND_URL = os.getenv('BACKEND_URL', 'http://localhost:5000')

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
```

Create the file `web-service/requirements.txt`:
```
flask==3.0.0
requests==2.31.0
```

**Verify the Files Are Created**
Run this command to see your project structure:
```bash
tree k8s-microservices
```
You should see:
```
k8s-microservices/
├── greeting-service/
│   ├── app.py
│   └── requirements.txt
└── web-service/
    ├── app.py
    └── requirements.txt
```
If you don't have `tree` installed, you can use:
```bash
ls -R k8s-microservices
```

**Understanding the Code**
*   **`greeting-service`**:
    *   Listens on port 5000
    *   Has a `/greet` endpoint that returns JSON with a message and the pod hostname
    *   The hostname will help us see load balancing later
*   **`web-service`**:
    *   Listens on port 8080
    *   Calls the backend using the `BACKEND_URL` environment variable
    *   Displays the result as a nice HTML page
    *   Has error handling if the backend is unreachable

**✅ Verification Step**
Let's verify the files are created correctly:
```bash
# Check greeting-service files
cat greeting-service/app.py | head -n 10
cat greeting-service/requirements.txt

# Check web-service files
cat web-service/app.py | head -n 10
cat web-service/requirements.txt
```
You should see the Python code and requirements for both services.

**🎓 Key Takeaway**: You now have two independent microservices. Each one is a small, focused application. In the next step, we'll containerize them with Docker so they can run anywhere!

---

### Step 2: Create Dockerfiles

**Why This Step?**
A Dockerfile is a recipe that tells Docker how to build a container image for your application. It includes:
*   The base operating system and runtime (Python, in our case)
*   Your application code
*   Dependencies (from `requirements.txt`)
*   Instructions on how to run your app

Containers ensure your app runs the same way everywhere—on your laptop, in the cloud, or in Kubernetes.

**Create Dockerfile for greeting-service**
Create the file `greeting-service/Dockerfile`:
```dockerfile
# FROM: Start from a base image with Python 3.11 pre-installed
FROM python:3.11-slim

# WORKDIR: Set the working directory inside the container
WORKDIR /app

# COPY: Copy the requirements file first (this helps with Docker layer caching)
COPY requirements.txt .

# RUN: Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# COPY: Copy the application code into the container
COPY app.py .

# EXPOSE: Document which port the app will listen on (this is informational)
EXPOSE 5000

# CMD: The command to run when the container starts
CMD ["python", "app.py"]
```

**Create Dockerfile for web-service**
Create the file `web-service/Dockerfile`:
```dockerfile
# FROM: Start from a base image with Python 3.11 pre-installed
FROM python:3.11-slim

# WORKDIR: Set the working directory inside the container
WORKDIR /app

# COPY: Copy the requirements file first
COPY requirements.txt .

# RUN: Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# COPY: Copy the application code into the container
COPY app.py .

# EXPOSE: Document which port the app will listen on
EXPOSE 8080

# CMD: The command to run when the container starts
CMD ["python", "app.py"]
```

---

#### Understanding the Dockerfile Instructions

Let me explain each instruction:

| Instruction | Purpose | Example |
|-------------|---------|---------|
| **FROM** | Specifies the base image to build upon | `python:3.11-slim` gives us Python installed on a minimal Linux |
| **WORKDIR** | Sets the working directory for subsequent commands | `/app` - all files will go here |
| **COPY** | Copies files from your computer into the container | `COPY app.py .` copies your code |
| **RUN** | Executes commands during the build process | `RUN pip install` installs dependencies |
| **EXPOSE** | Documents which port the app uses (doesn't actually open it) | `EXPOSE 5000` |
| **CMD** | The default command to run when container starts | `CMD ["python", "app.py"]` |

**💡 Pro Tip:** We copy `requirements.txt` first and install dependencies before copying the application code. This is a Docker best practice—if you change your code but not dependencies, Docker can reuse the cached layer with installed packages, making builds faster!

---

#### Create a `.dockerignore` File (Optional but Recommended)

To avoid copying unnecessary files into your Docker images, create these files:

`greeting-service/.dockerignore`:
```
__pycache__
*.pyc
*.pyo
*.pyd
.Python
*.so
.env
```

`web-service/.dockerignore`:
```
__pycache__
*.pyc
*.pyo
*.pyd
.Python
*.so
.env
```

**✅ Verification Step**
Verify that the Dockerfiles are created correctly:
```bash
# Check greeting-service Dockerfile
cat greeting-service/Dockerfile

# Check web-service Dockerfile
cat web-service/Dockerfile

# Verify your complete project structure
ls -la greeting-service/
ls -la web-service/
```
You should see these files in each directory:
- `app.py`
- `requirements.txt`
- `Dockerfile`
- `.dockerignore` (if you created it)

---

#### Your Project Structure Now
```
k8s-microservices/
├── greeting-service/
│   ├── .dockerignore
│   ├── Dockerfile
│   ├── app.py
│   └── requirements.txt
└── web-service/
    ├── .dockerignore
    ├── Dockerfile
    ├── app.py
    └── requirements.txt
```

**🎓 Key Takeaway**: Dockerfiles are the blueprints for your containers. They define everything needed to run your application in an isolated, reproducible environment. Each service has its own Dockerfile because each is independently deployable.

---

### Step 3: Build and Run Locally with Docker

**Why This Step?**
Before deploying to Kubernetes, we need to verify our containers work correctly. We'll:
*   Build Docker images from our Dockerfiles
*   Run the containers locally
*   Connect them so the frontend can talk to the backend
*   Test the full application

This ensures everything works before we add the complexity of Kubernetes.

**Part A: Build the Docker Images**
Navigate to your project root and build both images:
```bash
# Make sure you're in the project root
cd k8s-microservices

# Build the greeting-service image
docker build -t greeting-service:v1 ./greeting-service

# Build the web-service image
docker build -t web-service:v1 ./web-service
```
Understanding the command:
*   `docker build` - tells Docker to build an image
*   `-t greeting-service:v1` - tags (names) the image as "greeting-service" with version "v1"
*   `./greeting-service` - the directory containing the Dockerfile

You should see output showing Docker executing each instruction from the Dockerfile.

**✅ Verification: Check Your Images**
```bash
docker images | grep -E "greeting-service|web-service"
```
You should see output like:
```
greeting-service   v1      abc123def456   2 minutes ago   150MB
web-service        v1      def456ghi789   1 minute ago    152MB
```

**Part B: Create a Docker Network**
Docker containers are isolated by default. To let them communicate, we'll create a custom network:
```bash
docker network create microservices-net
```
Why? On this network, containers can find each other by their container name (like DNS). The `web-service` will be able to reach `greeting-service` by name.

**Part C: Run the Containers**
Now let's start both services:
1.  Start the `greeting-service` (backend):
    ```bash
docker run -d \
  --name greeting-service \
  --network microservices-net \
  -p 5000:5000 \
  greeting-service:v1
```
    Understanding the flags:
    *   `-d` - run in detached mode (background)
    *   `--name greeting-service` - name the container "greeting-service"
    *   `--network microservices-net` - connect to our custom network
    *   `-p 5000:5000` - map port 5000 on your machine to port 5000 in the container
    *   `greeting-service:v1` - the image to run

2.  Start the `web-service` (frontend):
    ```bash
docker run -d \
  --name web-service \
  --network microservices-net \
  -p 8080:8080 \
  -e BACKEND_URL=http://greeting-service:5000 \
  web-service:v1
```
    New flag:
    *   `-e BACKEND_URL=http://greeting-service:5000` - set an environment variable telling the frontend where to find the backend. Notice we use the container name "greeting-service" as the hostname!

**✅ Verification: Check Running Containers**
```bash
docker ps
```
You should see both containers running:
```
CONTAINER ID   IMAGE                 STATUS         PORTS                    NAMES
abc123def456   web-service:v1        Up 10 seconds  0.0.0.0:8080->8080/tcp   web-service
def456ghi789   greeting-service:v1   Up 20 seconds  0.0.0.0:5000->5000/tcp   greeting-service
```

**Part D: Test the Application**
1.  Test the backend directly:
    ```bash
curl http://localhost:5000/greet
```
    Expected output:
    ```json
{"message":"Hello from the Backend!","pod":"abc123def456"}
```

2.  **Test the full application in your browser:**
    Open your web browser and navigate to:
    ```
    http://localhost:8080
    ```
    You should see a beautiful webpage displaying:
    *   "🚀 Kubernetes Microservices Demo"
    *   "Hello from the Backend!"
    *   Backend Pod: (some container ID)

3.  Test using `curl` (alternative):
    ```bash
curl http://localhost:8080
```
    You should see the HTML response.

**Part E: Check the Logs (Debugging)**
If something isn't working, check the logs:
```bash
# View greeting-service logs
docker logs greeting-service

# View web-service logs
docker logs web-service

# Follow logs in real-time (Ctrl+C to exit)
docker logs -f web-service
```
You should see Flask startup messages and any HTTP requests being logged.

**Part F: Clean Up (When You're Done Testing)**
Once you've verified everything works, stop and remove the containers:
```bash
# Stop the containers
docker stop web-service greeting-service

# Remove the containers
docker rm web-service greeting-service

# Remove the network (optional)
docker network rm microservices-net
```
Note: We'll keep the Docker images (`greeting-service:v1` and `web-service:v1`) because we'll need them for Kubernetes!

**✅ Final Verification Checklist**
*   Both images built successfully
*   Both containers are running (`docker ps` shows them)
*   Backend responds at `http://localhost:5000/greet`
*   Frontend displays properly at `http://localhost:8080`
*   The webpage shows the backend's greeting message

**🎓 Key Takeaways**
*   Docker images are built from Dockerfiles and contain your application + dependencies
*   Docker networks allow containers to communicate using container names as hostnames
*   Environment variables (`-e` flag) configure how containers behave
*   Port mapping (`-p`) exposes container ports to your local machine
*   The frontend finds the backend using `http://greeting-service:5000` (container name as DNS)

**What You've Accomplished! 🎉**
You now have:
✅ Two working microservices
✅ Dockerized both services
✅ Tested them running locally with Docker
✅ Verified they communicate correctly

This is exactly how your application will work in Kubernetes, but Kubernetes will add:
*   Automatic healing (if a container crashes, restart it)
*   Load balancing (distribute traffic across multiple containers)
*   Service discovery (automatic DNS for finding services)
*   Scaling (easily run multiple copies)

---

## Phase 2: Deploy to Kubernetes

### Step 4: Introduction to Core Kubernetes Objects

**Why This Step?**
Before we write Kubernetes YAML files, you need to understand the core building blocks. Kubernetes uses different "objects" or "resources" to manage your applications. Think of them as Lego blocks—each piece has a specific purpose, and you combine them to build your application.

**The Three Core Kubernetes Objects (Using Analogies)**
1.  **Pod 🏠 - The Smallest Unit**
    *   **Analogy**: A Pod is like a single house where one or more containers live together.
    *   **What it is**:
        *   The smallest deployable unit in Kubernetes
        *   A wrapper around one or more containers (usually just one)
        *   Containers in the same Pod share:
            *   The same network (they can talk via `localhost`)
            *   The same storage volumes
            *   The same lifecycle (they start and stop together)
    *   **Key Point**: You rarely create Pods directly. Instead, you use Deployments (explained below).
    *   **Example**:
        ```
        Pod: greeting-service-pod
        └── Container: greeting-service (running your Flask app)
        ```
    *   **Real-world behavior**:
        *   If a Pod crashes, it's gone forever (Kubernetes won't restart it automatically unless managed by a Deployment)
        *   Each Pod gets its own IP address
        *   Pods are ephemeral (temporary)—they can be deleted and recreated at any time

2.  **Deployment 📋 - The Blueprint & Manager**
    *   **Analogy**: A Deployment is like a **construction company** that ensures you always have the right number of houses (Pods) built according to your blueprint.
    *   **What it is**:
        *   A controller that manages Pods
        *   You specify:
            *   How many replicas (copies) of a Pod you want
            *   The container image to use
            *   Update strategy (how to roll out new versions)
        *   Kubernetes continuously works to match your desired state
    *   **Why we need it**:
        *   **Automatic healing**: If a Pod crashes, the Deployment creates a new one
        *   **Scaling**: Want 5 copies? Just change the replica count
        *   **Rolling updates**: Update your app with zero downtime
        *   **Rollback**: If an update breaks, roll back to the previous version
    *   **Example**:
        ```
        Deployment: greeting-service-deployment
        ├── Manages 3 Pods:
        │   ├── greeting-service-pod-abc123
        │   ├── greeting-service-pod-def456
        │   └── greeting-service-pod-ghi789
        ```
    *   **Real-world behavior**:
        *   You delete a Pod? The Deployment immediately creates a new one
        *   You change the image from `v1` to `v2`? The Deployment gradually replaces old Pods with new ones
        *   One Pod crashes? The Deployment detects it and spins up a replacement

3.  **Service 🚪 - The Stable Address & Load Balancer**
    *   **Analogy**: A Service is like a **permanent street address** for a neighborhood of houses (Pods). Even if the houses get rebuilt or moved, the address stays the same.
    *   **What it is**:
        *   A stable network endpoint for accessing Pods
        *   Provides:
            *   A consistent DNS name (e.g., `greeting-service`)
            *   A stable virtual IP address
            *   Load balancing across multiple Pods
            *   Service discovery (other Pods can find it by name)
    *   **Why we need it**:
        *   **Pods are ephemeral**: Their IP addresses change when they restart
        *   **Multiple replicas**: With 3 backend Pods, which one should the frontend call? The Service load-balances automatically
        *   **Service discovery**: Instead of tracking IP addresses, use the Service name (e.g., `http://greeting-service:5000`)
    *   **Types of Services**:
        1.  **ClusterIP** (default): Only accessible inside the cluster
            *   Use for: Internal services (like our backend)
        2.  **NodePort**: Accessible from outside the cluster on a specific port (30000-32767)
            *   Use for: Quick testing or development
        3.  **LoadBalancer**: Creates an external load balancer (cloud providers only)
            *   Use for: Production external access
    *   **Example**:
        ```
        Service: greeting-service (ClusterIP)
        ├── DNS name: greeting-service.default.svc.cluster.local
        ├── Virtual IP: 10.96.100.50
        └── Routes traffic to Pods with label: app=greeting-service
            ├── Pod 1: 172.17.0.4:5000
            ├── Pod 2: 172.17.0.5:5000
            └── Pod 3: 172.17.0.6:5000
        ```
    *   **Real-world behavior**:
        *   A Pod dies and is replaced? The Service automatically updates its routing
        *   Multiple Pods available? The Service round-robins requests between them
        *   Another Pod needs to call it? Just use `http://greeting-service:5000`

#### How They Work Together

Let's see the full picture with our microservices:
```
┌─────────────────────────────────────────────────────────┐
│                    Kubernetes Cluster                    │
│                                                          │
│  ┌────────────────────────────────────────────────┐    │
│  │  Service: web-service (NodePort/LoadBalancer)  │    │
│  │  - Stable external access                      │    │
│  │  - http://localhost:30080                      │    │
│  └──────────┬─────────────────────────────────────┘    │
│             │ Load balances to:                         │
│             ↓                                            │
│  ┌────────────────────────────────────────────────┐    │
│  │  Deployment: web-service-deployment            │    │
│  │  - Manages 2 replicas                          │    │
│  └──────────┬─────────────────────────────────────┘    │
│             ↓                                            │
│  ┌──────────────────┐      ┌──────────────────┐        │
│  │ Pod: web-svc-1   │      │ Pod: web-svc-2   │        │
│  │ (172.17.0.8)     │      │ (172.17.0.9)     │        │
│  └────────┬─────────┘      └────────┬─────────┘        │
│           │                         │                   │
│           └─────────────┬───────────┘                   │
│                         │ Calls:                        │
│                         ↓ http://greeting-service:5000  │
│  ┌────────────────────────────────────────────────┐    │
│  │  Service: greeting-service (ClusterIP)         │    │
│  │  - Internal only                               │    │
│  │  - DNS: greeting-service                       │    │
│  └──────────┬─────────────────────────────────────┘    │
│             │ Load balances to:                         │
│             ↓                                            │
│  ┌────────────────────────────────────────────────┐    │
│  │  Deployment: greeting-service-deployment       │    │
│  │  - Manages 3 replicas                          │    │
│  └──────────┬─────────────────────────────────────┘    │
│             ↓                                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │ Pod: greet-1 │  │ Pod: greet-2 │  │ Pod: greet-3 │ │
│  │ (172.17.0.4) │  │ (172.17.0.5) │  │ (172.17.0.6) │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
│                                                          │
└─────────────────────────────────────────────────────────┘
```
**The Flow:**
*   User accesses `http://localhost:30080` (`web-service` Service)
*   Service routes to one of the `web-service` Pods
*   That Pod makes a request to `http://greeting-service:5000`
*   The `greeting-service` Service load-balances to one of its Pods
*   That Pod generates the response
*   Response flows back through the chain to the user

**Key Concepts Summary**
| Concept | Purpose | Analogy |
|---------|---------|---------|
| Pod | Runs your container(s) | A house |
| Deployment | Manages Pods, ensures desired count, handles updates | Construction company |
| Service | Stable network endpoint, load balancer | Permanent street address |
| Label | Key-value tags on objects | Tags you put on boxes |
| Selector | How Services find Pods | Matching tags to find the right boxes |

**Important Relationships**
*   **Deployments → Pods**:
    *   Deployments create and manage Pods
    *   Pods have labels (e.g., `app: greeting-service`)
    *   Deployments use a Pod template to define what Pods to create
*   **Services → Pods**:
    *   Services use selectors to find Pods
    *   If a Pod has labels that match the Service's selector, traffic is routed to it
    *   Example: Service selector `app: greeting-service` finds all Pods with that label

**✅ Self-Check Questions**
Before moving on, make sure you understand:
*   What happens if a Pod crashes?
    *   **Answer**: The Deployment detects it and creates a new Pod
*   Why can't we just use Pod IP addresses directly?
    *   **Answer**: Pod IPs change when they restart; Services provide stable endpoints
*   How does the `web-service` find the `greeting-service`?
    *   **Answer**: Using the Service DNS name: `http://greeting-service:5000`
*   What's the difference between a Pod and a Deployment?
    *   **Answer**: A Pod is a single instance; a Deployment manages multiple Pods and ensures they stay running

**🎓 Key Takeaways**
*   **Pod**: The basic unit that runs your container
*   **Deployment**: Ensures you always have the right number of Pods running
*   **Service**: Provides a stable way to access Pods, with load balancing
*   **Labels & Selectors**: How Services find and route traffic to the right Pods

Think of it like a restaurant:
*   Pods = Individual chefs making dishes
*   Deployment = Restaurant manager ensuring enough chefs are working
*   Service = The restaurant's front door (customers don't need to know which chef is cooking)

---

### Step 5: Create Kubernetes Deployments

**Why This Step?**
Now we'll write YAML configuration files that tell Kubernetes how to run our microservices. These Deployment files define:
*   Which container image to use
*   How many replicas (copies) to run
*   Labels for organizing and selecting Pods
*   Resource limits and health checks

YAML is like a recipe card that Kubernetes reads to create your application.

**Part A: Create the greeting-service Deployment**
Create a new directory for Kubernetes configs:
```bash
# Make sure you're in the project root
cd k8s-microservices

# Create a directory for Kubernetes YAML files
mkdir k8s-configs
```
Now create the file `k8s-configs/greeting-service-deployment.yaml`:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: greeting-service-deployment
  labels:
    app: greeting-service
spec:
  replicas: 2
  selector:
    matchLabels:
      app: greeting-service
  template:
    metadata:
      labels:
        app: greeting-service
    spec:
      containers:
      - name: greeting-service
        image: greeting-service:v1
        ports:
        - containerPort: 5000
        resources:
          requests:
            memory: "64Mi"
            cpu: "100m"
          limits:
            memory: "128Mi"
            cpu: "200m"
        livenessProbe:
          httpGet:
            path: /health
            port: 5000
          initialDelaySeconds: 10
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 5000
          initialDelaySeconds: 5
          periodSeconds: 5
```

**Part B: Create the web-service Deployment**
Create the file `k8s-configs/web-service-deployment.yaml`:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web-service-deployment
  labels:
    app: web-service
spec:
  replicas: 2
  selector:
    matchLabels:
      app: web-service
  template:
    metadata:
      labels:
        app: web-service
    spec:
      containers:
      - name: web-service
        image: web-service:v1
        ports:
        - containerPort: 8080
        env:
        - name: BACKEND_URL
          value: "http://greeting-service:5000"
        resources:
          requests:
            memory: "64Mi"
            cpu: "100m"
          limits:
            memory: "128Mi"
            cpu: "200m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 10
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 5
```

**Understanding the YAML Structure**
Let me break down the key sections of these files:
1.  **Metadata Section**
    ```yaml
    metadata:
      name: greeting-service-deployment
      labels:
        app: greeting-service
    ```
    *   `name`: The unique name of this Deployment
    *   `labels`: Key-value pairs to organize and identify objects (you can add multiple)

2.  **Spec Section - Deployment Configuration**
    ```yaml
    spec:
      replicas: 2
      selector:
        matchLabels:
          app: greeting-service
    ```
    *   `replicas`: How many Pod copies you want (we're starting with 2)
    *   `selector`: How this Deployment finds its Pods
        *   `matchLabels`: Must match the labels in the Pod template below

3.  **Template Section - Pod Blueprint**
    ```yaml
      template:
        metadata:
          labels:
            app: greeting-service
    ```
    *   `template`: The blueprint for creating Pods
    *   `labels`: These labels MUST match the selector above (this is how the Deployment knows which Pods it manages)

4.  **Container Configuration**
    ```yaml
        spec:
          containers:
          - name: greeting-service
            image: greeting-service:v1
            ports:
            - containerPort: 5000
    ```
    *   `containers`: List of containers in the Pod (usually just one)
    *   `name`: Container name (for identification)
    *   `image`: The Docker image to use (what we built earlier!)
    *   `ports/containerPort`: Which port the container listens on

5.  **Environment Variables (web-service only)**
    ```yaml
            env:
            - name: BACKEND_URL
              value: "http://greeting-service:5000"
    ```
    *   `env`: Environment variables passed to the container
    *   Notice we use `greeting-service` as the hostname—this will be the Service name we create next!

6.  **Resource Requests and Limits**
    ```yaml
            resources:
              requests:
                memory: "64Mi"
                cpu: "100m"
              limits:
                memory: "128Mi"
                cpu: "200m"
    ```
    *   `requests`: Minimum resources the container needs
        *   Kubernetes uses this for scheduling (finding a node with enough resources)
        *   `100m` = 100 millicores (0.1 CPU core)
        *   `64Mi` = 64 Mebibytes of RAM
    *   `limits`: Maximum resources the container can use
        *   If exceeded, the container may be terminated (OOMKilled for memory)
    *   Why this matters: Prevents one Pod from hogging all cluster resources.

7.  **Health Checks (Probes)**
    *   **Liveness Probe**:
        ```yaml
                livenessProbe:
                  httpGet:
                    path: /health
                    port: 5000
                  initialDelaySeconds: 10
                  periodSeconds: 10
        ```
        *   **Purpose**: Checks if the container is still running properly
        *   **Action**: If it fails, Kubernetes restarts the container
        *   `httpGet`: Makes an HTTP GET request to `/health` endpoint
        *   `initialDelaySeconds`: Wait 10 seconds after container starts before first check
        *   `periodSeconds`: Check every 10 seconds
    *   **Readiness Probe**:
        ```yaml
                readinessProbe:
                  httpGet:
                    path: /health
                    port: 5000
                  initialDelaySeconds: 5
                  periodSeconds: 5
        ```
        *   **Purpose**: Checks if the container is ready to receive traffic
        *   **Action**: If it fails, Kubernetes **removes the Pod from the Service** (no traffic sent to it)
        *   **Difference from liveness**: Doesn't restart the container, just stops sending traffic
        *   **Example scenario**: Your app needs 10 seconds to load data at startup. The readiness probe prevents traffic from reaching it until it's ready.

---

#### Visual Representation of the Deployment
```
Deployment: greeting-service-deployment
│
├── Replica Count: 2
│
├── Selector: app=greeting-service
│
└── Pod Template:
    ├── Labels: app=greeting-service
    └── Container Spec:
        ├── Image: greeting-service:v1
        ├── Port: 5000
        ├── Resources: 64Mi RAM / 0.1 CPU (requested)
        ├── Liveness Probe: GET /health every 10s
        └── Readiness Probe: GET /health every 5s

Creates:
├── Pod: greeting-service-deployment-abc123
└── Pod: greeting-service-deployment-def456
```

**Important YAML Syntax Rules**
⚠️ YAML is very picky about formatting!
*   Indentation matters: Use 2 spaces (not tabs!)
*   Colons: Must have a space after them (`key: value` not `key:value`)
*   Lists: Use a dash with a space (`- item` not `-item`)
*   Case-sensitive: `apiVersion` ≠ `ApiVersion`

**Common mistakes:**
```yaml
# ❌ Wrong - no space after colon
name:greeting-service

# ✅ Correct
name: greeting-service

# ❌ Wrong - tabs used for indentation
spec:
  replicas: 2

# ✅ Correct - 2 spaces
  spec:
    replicas: 2
```

**✅ Verification Step**
Check that your YAML files are created correctly:
```bash
# List the files
ls -l k8s-configs/

# View the greeting-service deployment
cat k8s-configs/greeting-service-deployment.yaml

# View the web-service deployment
cat k8s-configs/web-service-deployment.yaml
```
You should see both YAML files with all the content above.

Optional: Validate YAML syntax (if you have `kubectl` configured):
```bash
# Dry-run validation (doesn't actually create anything)
kubectl apply --dry-run=client -f k8s-configs/greeting-service-deployment.yaml
kubectl apply --dry-run=client -f k8s-configs/web-service-deployment.yaml
```
If the YAML is valid, you'll see:
```
deployment.apps/greeting-service-deployment created (dry run)
deployment.apps/web-service-deployment created (dry run)
```

---

#### Your Project Structure Now
```
k8s-microservices/
├── greeting-service/
│   ├── Dockerfile
│   ├── app.py
│   └── requirements.txt
├── web-service/
│   ├── Dockerfile
│   ├── app.py
│   └── requirements.txt
└── k8s-configs/
    ├── greeting-service-deployment.yaml
    └── web-service-deployment.yaml
```

---

**🎓 Key Takeaways**
1.  **Deployments are the controllers** that manage your Pods
2.  **`replicas`** determines how many copies of your Pod run
3.  **`selector.matchLabels`** MUST match **`template.metadata.labels`** (this is how Deployments find their Pods)
4.  **Resources** (requests/limits) prevent resource starvation
5.  **Liveness probes** restart unhealthy containers
6.  **Readiness probes** control when Pods receive traffic
7.  **Environment variables** can be set directly in the YAML

**Critical relationship:**
```
Deployment selector (app: greeting-service)
           ↓ MUST MATCH ↓
Pod template labels (app: greeting-service)
```

---

### Step 6: Create Kubernetes Services

**Why This Step?**
Deployments create Pods, but Pods have temporary, changing IP addresses. Services provide:
*   Stable DNS names (e.g., `greeting-service`)
*   Stable virtual IP addresses
*   Load balancing across multiple Pod replicas
*   Service discovery so Pods can find each other

Without Services, the `web-service` couldn't find the `greeting-service`!

**Understanding Service Types**
Before we create the files, let's clarify which Service type to use:
| Service Type | Accessibility | Use Case |
|--------------|---------------|----------|
| ClusterIP | Internal only | Backend services (`greeting-service`) |
| NodePort | External via Node IP:Port | Development/testing |
| LoadBalancer | External via cloud LB | Production (requires cloud provider) |

Our setup:
*   `greeting-service`: `ClusterIP` (internal only, backend)
*   `web-service`: `NodePort` (so we can access it from our browser)

**Part A: Create the greeting-service Service (ClusterIP)**
Create the file `k8s-configs/greeting-service-service.yaml`:
```yaml
apiVersion: v1
kind: Service
metadata:
  name: greeting-service
  labels:
    app: greeting-service
spec:
  type: ClusterIP
  selector:
    app: greeting-service
  ports:
  - protocol: TCP
    port: 5000
    targetPort: 5000
```

**Part B: Create the web-service Service (NodePort)**
Create the file `k8s-configs/web-service-service.yaml`:
```yaml
apiVersion: v1
kind: Service
metadata:
  name: web-service
  labels:
    app: web-service
spec:
  type: NodePort
  selector:
    app: web-service
  ports:
  - protocol: TCP
    port: 8080
    targetPort: 8080
    nodePort: 30080
```

**Understanding the Service YAML**
1.  **Basic Metadata**
    ```yaml
    metadata:
      name: greeting-service
      labels:
        app: greeting-service
    ```
    *   `name`: This becomes the DNS name! Other Pods can reach this service at `http://greeting-service:5000`
    *   `labels`: For organization (optional but recommended)

2.  **Service Type**
    ```yaml
    spec:
      type: ClusterIP  # or NodePort
    ```
    *   `ClusterIP`: Creates an internal-only virtual IP
    *   `NodePort`: Also exposes the service on a port (30000-32767) on every cluster node

3.  **The Selector - How Services Find Pods ⭐**
    ```yaml
      selector:
        app: greeting-service
    ```
    **This is critical!** The Service uses this selector to find Pods.
    **How it works:**
    1.  Service looks for Pods with the label `app: greeting-service`
    2.  Finds all matching Pods (created by our Deployment)
    3.  Automatically routes traffic to those Pods
    4.  Load-balances across all healthy Pods

    **The connection:**
    ```
    Service selector:       app: greeting-service
                                  ↓ MATCHES ↓
    Pod labels (from Deployment): app: greeting-service
    ```

4.  **Port Configuration**
    ```yaml
      ports:
      - protocol: TCP
        port: 5000
        targetPort: 5000
        nodePort: 30080  # Only for NodePort type
    ```
    Let me explain each port type:
    | Port Type | Meaning | Example |
    |-----------|---------|---------|
    | **port** | The port the Service listens on | Other Pods call `http://greeting-service:5000` |
    | **targetPort** | The port on the Pod/container | Must match `containerPort` in Deployment |
    | **nodePort** | External port on cluster nodes (30000-32767) | Access via `http://localhost:30080` |

    **Visual example for web-service:**
    ```
    Browser Request
         ↓
    http://localhost:30080  ← nodePort (external access)
         ↓
    Service: web-service
         ↓
    port: 8080  ← Service's internal port
         ↓
    targetPort: 8080  ← Pod's containerPort
         ↓
    Pod: web-service-xyz
    ```

#### How the Selector Works - Detailed Example
Let's trace how the `greeting-service` Service finds its Pods:
1.  Deployment creates Pods with labels:
    ```yaml
    # From greeting-service-deployment.yaml
    template:
      metadata:
        labels:
          app: greeting-service  ← Pod gets this label
    ```
2.  Service uses selector to find those Pods:
    ```yaml
    # From greeting-service-service.yaml
    selector:
      app: greeting-service  ← Service looks for this label
    ```
3.  Kubernetes automatically connects them:
    ```
    Service: greeting-service (10.96.100.50)
        ↓ selector: app=greeting-service
        ↓
    Finds these Pods:
    ├── greeting-service-deployment-abc123 (172.17.0.4:5000) ✓
    ├── greeting-service-deployment-def456 (172.17.0.5:5000) ✓
    └── greeting-service-deployment-ghi789 (172.17.0.6:5000) ✓

    Traffic to greeting-service:5000 is load-balanced to these 3 Pods!
    ```
    **If labels don't match:**
    ```
    Service: greeting-service
        ↓ selector: app=greeting-service
        ↓
    Finds: NOTHING ❌
    Result: Service has no endpoints, requests will fail!
    ```

---

#### Service DNS Names

Kubernetes automatically creates DNS entries for Services:

**Short form (within same namespace):**
```
greeting-service
```

**Full form (FQDN):**
```
greeting-service.default.svc.cluster.local
```
Where:
*   `greeting-service` = Service name
*   `default` = Namespace (we're using the default namespace)
*   `svc.cluster.local` = Kubernetes domain

In our `web-service` code, we use:
```python
BACKEND_URL = "http://greeting-service:5000"
```
This works because both services are in the same namespace (default).

---

#### Complete Service Flow Diagram
```
┌─────────────────────────────────────────────────────────┐
│  External User                                           │
│  http://localhost:30080                                  │
└───────────────────┬─────────────────────────────────────┘
                    │
                    ↓ (nodePort: 30080)
┌─────────────────────────────────────────────────────────┐
│  Service: web-service (NodePort)                         │
│  - Type: NodePort                                        │
│  - Selector: app=web-service                             │
│  - Port: 8080 → targetPort: 8080                         │
└───────────────────┬─────────────────────────────────────┘
                    │
                    ↓ (Routes to Pods with label app=web-service)
┌─────────────────────────────────────────────────────────┐
│  Pods:                                                   │
│  ├── web-service-deployment-abc (172.17.0.8:8080)       │
│  └── web-service-deployment-def (172.17.0.9:8080)       │
└───────────────────┬─────────────────────────────────────┘
                    │
                    ↓ (Makes request to http://greeting-service:5000)
┌─────────────────────────────────────────────────────────┐
│  Service: greeting-service (ClusterIP)                   │
│  - Type: ClusterIP                                       │
│  - DNS: greeting-service                                 │
│  - Selector: app=greeting-service                        │
│  - Port: 5000 → targetPort: 5000                         │
└───────────────────┬─────────────────────────────────────┘
                    │
                    ↓ (Routes to Pods with label app=greeting-service)
┌─────────────────────────────────────────────────────────┐
│  Pods:                                                   │
│  ├── greeting-service-deployment-abc (172.17.0.4:5000)  │
│  └── greeting-service-deployment-def (172.17.0.5:5000)  │
└─────────────────────────────────────────────────────────┘
```

**Why ClusterIP for Backend vs NodePort for Frontend?**
*   **`greeting-service` (ClusterIP)**:
    *   Only needs to be accessed by other Pods in the cluster
    *   Not exposed to the outside world (security!)
    *   Faster (no extra port mapping)
*   **`web-service` (NodePort)**:
    *   Needs to be accessed from your browser
    *   NodePort exposes it on `localhost:30080`
    *   In production, you'd use `LoadBalancer` or an `Ingress` instead

**✅ Verification Step**
Check that your Service YAML files are created:
```bash
# List the files
ls -l k8s-configs/

# View the greeting-service service
cat k8s-configs/greeting-service-service.yaml

# View the web-service service
cat k8s-configs/web-service-service.yaml
```
Validate the YAML (optional):
```bash
kubectl apply --dry-run=client -f k8s-configs/greeting-service-service.yaml
kubectl apply --dry-run=client -f k8s-configs/web-service-service.yaml
```
Expected output:
```
service/greeting-service created (dry run)
service/web-service created (dry run)
```

---

#### Your Complete Project Structure
```
k8s-microservices/
├── greeting-service/
│   ├── Dockerfile
│   ├── app.py
│   └── requirements.txt
├── web-service/
│   ├── Dockerfile
│   ├── app.py
│   └── requirements.txt
└── k8s-configs/
    ├── greeting-service-deployment.yaml
    ├── greeting-service-service.yaml
    ├── web-service-deployment.yaml
    └── web-service-service.yaml
```

---

**🎓 Key Takeaways**
1.  **Services provide stable network endpoints** for accessing Pods
2.  **Selectors connect Services to Pods** using label matching
3.  **ClusterIP** is for internal-only access (backend services)
4.  **NodePort** exposes services externally on a specific port
5.  **DNS names** are automatically created (Service name = DNS name)
6.  **`port`** = Service's port, **`targetPort`** = Pod's port
7.  **Load balancing** happens automatically across all matching Pods

**Critical relationships:**
```
Service selector labels MUST MATCH Pod labels from Deployment
                              ↓
        This is how traffic flows to the right Pods!
```

**Port mapping flow:**
```
nodePort (30080) → port (8080) → targetPort (8080) → containerPort (8080)
   ↑                   ↑              ↑                      ↑
External          Service        What port         What port the
access            listens on     Service           container
                                 forwards to       listens on
```

---

### Step 7: Deploy to the Cluster

**Why This Step?**
Now we'll actually deploy our application to Kubernetes! We'll:
*   Apply our YAML files using `kubectl`
*   Check that everything is running correctly
*   Access our application through the web browser
*   Learn essential `kubectl` commands for monitoring

This is where everything comes together! 🎉

**Part A: Verify Your Cluster is Running**
First, let's make sure your Kubernetes cluster is ready:
```bash
# Check cluster info
kubectl cluster-info

# Check that nodes are ready
kubectl get nodes
```
**Expected output:**
```
NAME             STATUS   ROLES           AGE   VERSION
docker-desktop   Ready    control-plane   5d    v1.28.2
```
If you see errors, make sure Docker Desktop/Minikube/Kind is running.

**Part B: Deploy the Deployments**
Let's deploy our Deployments first (which will create the Pods):
```bash
# Navigate to your project root
cd k8s-microservices

# Apply the greeting-service Deployment
kubectl apply -f k8s-configs/greeting-service-deployment.yaml

# Apply the web-service Deployment
kubectl apply -f k8s-configs/web-service-deployment.yaml
```
**Expected output:**
```
deployment.apps/greeting-service-deployment created
deployment.apps/web-service-deployment created
```

**✅ Verification: Check Deployments**
```bash
# View all Deployments
kubectl get deployments
```
**Expected output:**
```
NAME                          READY   UP-TO-DATE   AVAILABLE   AGE
greeting-service-deployment   2/2     2            2           30s
web-service-deployment        2/2     2            2           30s
```
Understanding the columns:
*   `READY`: `2/2` means 2 Pods are ready out of 2 desired
*   `UP-TO-DATE`: Pods running the latest configuration
*   `AVAILABLE`: Pods ready to receive traffic
*   `AGE`: How long since creation

**✅ Verification: Check Pods**
```bash
# View all Pods
kubectl get pods
```
**Expected output:**
```
NAME                                           READY   STATUS    RESTARTS   AGE
greeting-service-deployment-7d9f8c6b5d-abc12   1/1     Running   0          45s
greeting-service-deployment-7d9f8c6b5d-def34   1/1     Running   0          45s
web-service-deployment-6c8b9d5f7a-ghi56        1/1     Running   0          45s
web-service-deployment-6c8b9d5f7a-jkl78        1/1     Running   0          45s
```
Understanding Pod status:
*   `READY`: `1/1` means 1 container is ready out of 1
*   `STATUS`:
    *   `Running` ✅ Good!
    *   `Pending` ⏳ Waiting (probably pulling image)
    *   `CrashLoopBackOff` ❌ Container keeps crashing
    *   `ImagePullBackOff` ❌ Can't pull the Docker image
    *   `Error` ❌ Something went wrong

**If Pods show `ImagePullBackOff` or `ErrImagePull`:**
This is common! It means Kubernetes can't find your Docker images. This happens because:
*   Docker images built locally aren't automatically available to Kubernetes
*   We need to either push to a registry OR configure Kubernetes to use local images

**Solution for Minikube users:**
```bash
# Point your terminal to Minikube's Docker daemon
eval $(minikube docker-env)

# Rebuild your images
docker build -t greeting-service:v1 ./greeting-service
docker build -t web-service:v1 ./web-service

# Delete and recreate the Deployments
kubectl delete -f k8s-configs/greeting-service-deployment.yaml
kubectl delete -f k8s-configs/web-service-deployment.yaml
kubectl apply -f k8s-configs/greeting-service-deployment.yaml
kubectl apply -f k8s-configs/web-service-deployment.yaml
```
**Solution for Docker Desktop/Kind users:**
Your local images should already be available. If not, you may need to update the Deployment to set `imagePullPolicy: Never`:
```bash
# Add this line to both Deployment YAML files under containers:
# imagePullPolicy: Never

# Then reapply
kubectl apply -f k8s-configs/greeting-service-deployment.yaml
kubectl apply -f k8s-configs/web-service-deployment.yaml
```

**Part C: Deploy the Services**
Now let's create the Services so our Pods can communicate:
```bash
# Apply the greeting-service Service
kubectl apply -f k8s-configs/greeting-service-service.yaml

# Apply the web-service Service
kubectl apply -f k8s-configs/web-service-service.yaml
```
**Expected output:**
```
service/greeting-service created
service/web-service created
```

**✅ Verification: Check Services**
```bash
# View all Services
kubectl get services
```
**Expected output:**
```
NAME               TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)          AGE
kubernetes         ClusterIP   10.96.0.1       <none>        443/TCP          5d
greeting-service   ClusterIP   10.96.100.50    <none>        5000/TCP         20s
web-service        NodePort    10.96.200.100   <none>        8080:30080/TCP   20s
```
Understanding the columns:
*   `TYPE`: `ClusterIP` (internal) or `NodePort` (external)
*   `CLUSTER-IP`: The virtual IP of the Service
*   `EXTERNAL-IP`: For `LoadBalancer` type (we see `<none>` for `NodePort`)
*   `PORT(S)`:
    *   `ClusterIP`: `5000/TCP` (internal port)
    *   `NodePort`: `8080:30080/TCP` (internal:external)

**✅ Verification: Check Service Endpoints**
This shows which Pod IPs the Service is routing to:
```bash
# Check greeting-service endpoints
kubectl get endpoints greeting-service

# Check web-service endpoints
kubectl get endpoints web-service
```
**Expected output:**
```
NAME               ENDPOINTS                                              AGE
greeting-service   172.17.0.4:5000,172.17.0.5:5000       1m
web-service        172.17.0.8:8080,172.17.0.9:8080     1m
```
**What this shows:** Each Service has found 2 Pods (matching the label selector) and is ready to route traffic to them.
**If `ENDPOINTS` is empty (`<none>`):**
*   The Service selector doesn't match any Pod labels
*   Check that labels match between Service and Deployment

---

#### Part D: Access the Application

Now for the moment of truth—let's access our application!

##### Method 1: Direct Browser Access (Docker Desktop/Minikube)

**For Docker Desktop:**
```
http://localhost:30080
```
**For Minikube:**
```bash
# Get the Minikube IP
minikube ip

# Then access: http://<MINIKUBE-IP>:30080
# Example: http://192.168.49.2:30080
```
**For Kind:**
```bash
# Kind requires port forwarding
kubectl port-forward service/web-service 8080:8080

# Then access: http://localhost:8080
```

##### Method 2: Using `kubectl port-forward` (Works for all)
If the NodePort doesn't work, use port forwarding:
```bash
# Forward local port 8080 to the web-service Service
kubectl port-forward service/web-service 8080:8080
```
**Leave this running** and open your browser to:
```
http://localhost:8080
```

**✅ Verification: Test the Application**
You should see:
*   🚀 Kubernetes Microservices Demo heading
*   "Hello from the Backend!" message
*   Backend Pod: showing a pod name like `greeting-service-deployment-7d9f8c6b5d-abc12`

Refresh the page multiple times and watch the Backend Pod name change! This proves:
*   The Service is load-balancing between multiple backend Pods
*   The frontend is successfully calling the backend via the Service DNS name

##### Method 3: Testing with `curl`
```bash
# Test the web-service (if using port-forward on 8080)
curl http://localhost:8080

# Or if using NodePort
curl http://localhost:30080

# Test the greeting-service directly (from inside the cluster)
kubectl run test-pod --rm -it --image=curlimages/curl --restart=Never -- curl http://greeting-service:5000/greet
```
Expected output from `greeting-service`:
```json
{"message":"Hello from the Backend!","pod":"greeting-service-deployment-7d9f8c6b5d-abc12"}
```

#### Part E: Essential Monitoring Commands
Now let's learn the key `kubectl` commands you'll use daily:
1.  **Get Resources**
    ```bash
    # Get all Pods
    kubectl get pods

    # Get all Deployments
    kubectl get deployments

    # Get all Services
    kubectl get services

    # Get everything at once
    kubectl get all

    # Get Pods with more details (like node, IP)
    kubectl get pods -o wide

    # Watch Pods in real-time (updates automatically)
    kubectl get pods --watch
    ```

2.  **Describe Resources (Detailed information)**
    ```bash
    # Describe a specific Pod (replace with your actual Pod name)
    kubectl describe pod greeting-service-deployment-7d9f8c6b5d-abc12

    # Describe the Deployment
    kubectl describe deployment greeting-service-deployment

    # Describe the Service
    kubectl describe service greeting-service
    ```
    What describe shows:
    *   Events (creation, errors, restarts)
    *   Configuration details
    *   Status and conditions
    *   For Services: Endpoints (Pod IPs it routes to)

3.  **Check Pod Logs**
    ```bash
    # Get logs from a specific Pod (replace with your Pod name)
    kubectl logs greeting-service-deployment-7d9f8c6b5d-abc12

    # Follow logs in real-time (like `tail -f`)
    kubectl logs -f greeting-service-deployment-7d9f8c6b5d-abc12

    # Get logs from all Pods with a label
    kubectl logs -l app=greeting-service

    # Get logs from the previous container instance (if it crashed)
    kubectl logs greeting-service-deployment-7d9f8c6b5d-abc12 --previous
    ```

4.  **Quick Status Overview**
    ```bash
    # Check if everything is running
    kubectl get all

    # Check specific namespace (we're using 'default')
    kubectl get all -n default

    # Get Pod status with labels
    kubectl get pods --show-labels
    ```

#### Part F: Verify the Complete Setup
Let's do a final end-to-end check:
```bash
# 1. Check Deployments are ready
kubectl get deployments

# 2. Check all Pods are Running
kubectl get pods

# 3. Check Services have endpoints
kubectl get endpoints

# 4. Check Service DNS (from inside cluster)
kubectl run test-dns --rm -it --image=busybox --restart=Never -- nslookup greeting-service

# 5. Test backend directly
kubectl run test-backend --rm -it --image=curlimages/curl --restart=Never -- curl http://greeting-service:5000/greet

# 6. Access in browser
# http://localhost:30080 (or your Minikube IP)
```

**Troubleshooting Guide**
*   **Problem: Pods stuck in Pending**
    ```bash
    kubectl describe pod <pod-name>
    ```
    Common causes:
    *   Not enough resources in cluster
    *   Image pull issues
*   **Problem: Pods in CrashLoopBackOff**
    ```bash
    kubectl logs <pod-name>
    kubectl logs <pod-name> --previous
    ```
    Common causes:
    *   Application error in code
    *   Missing environment variables
    *   Port conflicts
*   **Problem: Can't access web-service**
    *   Check Service exists:
        ```bash
        kubectl get service web-service
        ```
    *   Check Service has endpoints:
        ```bash
        kubectl get endpoints web-service
        ```
    *   Check Pod logs:
        ```bash
        kubectl logs -l app=web-service
        ```
*   **Problem: web-service can't reach greeting-service**
    *   Check `greeting-service` Service exists:
        ```bash
        kubectl get service greeting-service
        ```
    *   Test DNS from `web-service` Pod:
        ```bash
        # Get a web-service Pod name
        POD=$(kubectl get pods -l app=web-service -o jsonpath='{.items[0].metadata.name}')
        
        # Test DNS resolution
        kubectl exec $POD -- nslookup greeting-service
        
        # Test HTTP connection
        kubectl exec $POD -- curl http://greeting-service:5000/greet
        ```

---

**✅ Final Verification Checklist**
Confirm everything is working:
*   [ ] `kubectl get deployments` shows `2/2 READY` for both Deployments
*   [ ] `kubectl get pods` shows all Pods in `Running` state
*   [ ] `kubectl get services` shows both Services with `CLUSTER-IP` assigned
*   [ ] `kubectl get endpoints` shows Pod IPs for both Services
*   [ ] Browser shows the application at `http://localhost:30080` (or your NodePort)
*   [ ] Refreshing the page shows different backend Pod names (load balancing works!)

---

**🎓 Key Takeaways**
1.  **`kubectl apply -f <file>`** deploys YAML to the cluster
2.  **`kubectl get <resource>`** shows current state
3.  **`kubectl describe <resource> <name>`** shows detailed info and events
4.  **`kubectl logs <pod-name>`** shows application logs
5.  **Services use selectors** to automatically find and route to Pods
6.  **NodePort** exposes services on `<node-ip>:<nodePort>`
7.  **DNS works automatically**: `greeting-service` resolves inside the cluster
8.  **Load balancing is automatic** across all healthy Pods

---

#### Your Deployed Architecture
```
Browser: http://localhost:30080
           ↓
Service: web-service (NodePort 30080)
           ↓ Load balances to:
Pods: web-service-xxx, web-service-yyy
           ↓ Calls http://greeting-service:5000
Service: greeting-service (ClusterIP)
           ↓ Load balances to:
Pods: greeting-service-aaa, greeting-service-bbb
```

**🎉 Congratulations!**
You've successfully deployed a multi-service application to Kubernetes! Your microservices are:
✅ Running in containers
✅ Managed by Deployments (auto-healing, scaling)
✅ Communicating via Services
✅ Load-balanced automatically

---

## Phase 3: Advanced Concepts & Day-2 Operations

### Step 8: Scaling and Updates

**Why This Step?**
Now that your application is running, you need to learn Day-2 operations:
*   **Scaling**: Adjust the number of Pods based on load
*   **Rolling Updates**: Deploy new versions without downtime
*   **Rollbacks**: Revert to a previous version if something breaks

These are essential skills for running production workloads in Kubernetes!

**Part A: Scaling - Adding More Replicas**
**Understanding Scaling**
When you scale, you're changing the number of Pod replicas. Kubernetes will:
*   Create new Pods if you scale up
*   Gracefully terminate Pods if you scale down
*   Automatically add new Pods to the Service's load balancing pool

##### Method 1: Scale Using `kubectl` Command
Let's scale the `greeting-service` from 2 to 3 replicas:
```bash
# Scale the greeting-service Deployment to 3 replicas
kubectl scale deployment greeting-service-deployment --replicas=3
```
**Expected output:**
```
deployment.apps/greeting-service-deployment scaled
```

**✅ Verification: Watch the Scaling Happen**
```bash
# Watch Pods being created in real-time
kubectl get pods --watch
```
You should see a new `greeting-service` Pod being created:
```
NAME                                           READY   STATUS              RESTARTS   AGE
greeting-service-deployment-7d9f8c6b5d-abc12   1/1     Running             0          10m
greeting-service-deployment-7d9f8c6b5d-def34   1/1     Running             0          10m
greeting-service-deployment-7d9f8c6b5d-ghi56   0/1     ContainerCreating   0          2s    ← New Pod
```
Wait a moment, then:
```
greeting-service-deployment-7d9f8c6b5d-ghi56   1/1     Running             0          10s
```
Press `Ctrl+C` to stop watching.

**Check the Deployment**
```bash
# View Deployment status
kubectl get deployment greeting-service-deployment
```
**Expected output:**
```
NAME                          READY   UP-TO-DATE   AVAILABLE   AGE
greeting-service-deployment   3/3     3            3           15m
```
Notice `READY` changed from `2/2` to `3/3`!

**Check Service Endpoints**
```bash
# Verify the Service now routes to 3 Pods
kubectl get endpoints greeting-service
```
**Expected output:**
```
NAME               ENDPOINTS                                              AGE
greeting-service   172.17.0.4:5000,172.17.0.5:5000,172.17.0.6:5000       15m
```
Now there are 3 IP addresses—the Service automatically discovered the new Pod!

**Test Load Balancing Across 3 Pods**
Refresh your browser multiple times at `http://localhost:30080` (or use your NodePort/port-forward).
You should now see 3 different backend Pod names rotating as you refresh:
*   `greeting-service-deployment-7d9f8c6b5d-abc12`
*   `greeting-service-deployment-7d9f8c6b5d-def34`
*   `greeting-service-deployment-7d9f8c6b5d-ghi56`

This proves:
✅ The Service is load-balancing across all 3 Pods
✅ New Pods are automatically added to the load balancer
✅ No downtime occurred during scaling

##### Method 2: Scale by Editing the YAML File
You can also scale by updating the Deployment YAML:
```bash
# Edit the greeting-service Deployment
kubectl edit deployment greeting-service-deployment
```
This opens the YAML in your default editor. Find the line:
```yaml
spec:
  replicas: 3
```
Change it to:
```yaml
spec:
  replicas: 5
```
Save and close (`:wq` in vim, `Ctrl+X` in nano).
Kubernetes immediately applies the change!

**✅ Verification: Check Scaling to 5**
```bash
# Watch the new Pods being created
kubectl get pods --watch
```
You should see 2 more `greeting-service` Pods being created.
```bash
# Verify 5 replicas are running
kubectl get deployment greeting-service-deployment
```
**Expected output:**
```
NAME                          READY   UP-TO-DATE   AVAILABLE   AGE
greeting-service-deployment   5/5     5            5           20m
```

##### Method 3: Scale by Updating the YAML File and Applying
This is the recommended approach for production:
```bash
# Edit your local YAML file
nano k8s-configs/greeting-service-deployment.yaml
```
Change the `replicas` field:
```yaml
spec:
  replicas: 2  # Change back to 2
```
Apply the change:
```bash
kubectl apply -f k8s-configs/greeting-service-deployment.yaml
```
**Expected output:**
```
deployment.apps/greeting-service-deployment configured
```

**Watch Pods Scale Down**
```bash
# Watch Pods being terminated
kubectl get pods --watch
```
You'll see Pods transitioning to `Terminating` status:
```
greeting-service-deployment-7d9f8c6b5d-ghi56   1/1     Terminating   0          5m
greeting-service-deployment-7d9f8c6b5d-jkl78   1/1     Terminating   0          2m
greeting-service-deployment-7d9f8c6b5d-mno90   1/1     Terminating   0          2m
```
Kubernetes gracefully shuts them down, and eventually you'll have 2 Pods remaining.

**What Happens When You Scale?**
*   **Scaling Up (2 → 5 replicas)**:
    *   Deployment detects desired state (5) doesn't match current state (2)
    *   Creates 3 new Pods from the Pod template
    *   Scheduler assigns them to nodes with available resources
    *   Pods start, readiness probes pass
    *   Service automatically adds new Pod IPs to its endpoint list
    *   Traffic is now distributed across all 5 Pods
*   **Scaling Down (5 → 2 replicas)**:
    *   Deployment detects desired state (2) doesn't match current state (5)
    *   Selects 3 Pods to terminate (newest first, by default)
    *   Service removes those Pod IPs from its endpoint list (no new traffic)
    *   Kubernetes sends `SIGTERM` to the containers (graceful shutdown)
    *   Waits up to 30 seconds (`terminationGracePeriodSeconds`)
    *   If still running, sends `SIGKILL` (force kill)
    *   Pods are deleted
*   No downtime! The Service stops sending traffic to terminating Pods before they shut down.

**Part B: Rolling Updates**
Now let's update our application to a new version with zero downtime.

**Step 1: Modify the Application Code**
Let's change the greeting message. Edit `greeting-service/app.py`:
```bash
nano greeting-service/app.py
```
Change the greeting message:
```python
@app.route('/greet', methods=['GET'])
def greet():
    hostname = socket.gethostname()
    greeting = {
        "message": "Hello from the UPDATED Backend! 🚀",  # Changed this line
        "pod": hostname,
        "version": "v2"  # Added version info
    }
    return jsonify(greeting)
```
Save the file.

**Step 2: Build a New Docker Image**
Build the new version with a `v2` tag:
```bash
# Navigate to project root
cd k8s-microservices

# Build the new image with v2 tag
docker build -t greeting-service:v2 ./greeting-service
```
For Minikube users, remember to use Minikube's Docker daemon:
```bash
eval $(minikube docker-env)
docker build -t greeting-service:v2 ./greeting-service
```

**✅ Verification: Check Both Images Exist**
```bash
docker images | grep greeting-service
```
**Expected output:**
```
greeting-service   v2      xyz789abc123   30 seconds ago   150MB
greeting-service   v1      abc123def456   1 hour ago       150MB
```
You should see both `v1` and `v2`.

**Step 3: Update the Deployment to Use v2**
Edit the Deployment YAML:
```bash
nano k8s-configs/greeting-service-deployment.yaml
```
Find the `image` line and change it from `v1` to `v2`:
```yaml
    spec:
      containers:
      - name: greeting-service
        image: greeting-service:v2  # Changed from v1 to v2
        ports:
        - containerPort: 5000
```
Save the file.

**Step 4: Apply the Update**
```bash
kubectl apply -f k8s-configs/greeting-service-deployment.yaml
```
**Expected output:**
```
deployment.apps/greeting-service-deployment configured
```

**Step 5: Watch the Rolling Update in Action**
```bash
# Watch Pods being updated
kubectl get pods --watch
```
**You'll see a rolling update pattern:**
```
NAME                                           READY   STATUS              RESTARTS   AGE
greeting-service-deployment-7d9f8c6b5d-abc12   1/1     Running             0          30m
greeting-service-deployment-7d9f8c6b5d-def34   1/1     Running             0          30m
greeting-service-deployment-8e7g9d6c5e-new01   0/1     ContainerCreating   0          2s    ← New v2 Pod
```
Then:
```
greeting-service-deployment-8e7g9d6c5e-new01   1/1     Running             0          10s   ← v2 ready
greeting-service-deployment-7d9f8c6b5d-abc12   1/1     Terminating         0          30m   ← v1 terminating
greeting-service-deployment-8e7g9d6c5e-new02   0/1     ContainerCreating   0          2s    ← Another v2
```
Finally:
```
greeting-service-deployment-8e7g9d6c5e-new01   1/1     Running   0          30s
greeting-service-deployment-8e7g9d6c5e-new02   1/1     Running   0          20s
```
Press `Ctrl+C` to stop watching.

**Understanding the Rolling Update Strategy**
Kubernetes uses a `RollingUpdate` strategy by default:
*   Creates 1 new Pod with the `v2` image
*   Waits for it to be Ready (readiness probe passes)
*   Adds it to the Service (starts receiving traffic)
*   Terminates 1 old Pod (`v1`)
*   Repeats until all Pods are `v2`

Key parameters (defaults):
*   `maxUnavailable`: 25% - Max Pods that can be down during update
*   `maxSurge`: 25% - Max extra Pods that can be created during update

For 2 replicas:
*   `maxSurge=1`: Can temporarily have 3 Pods (2 old + 1 new)
*   `maxUnavailable=0`: Always keeps at least 2 Pods running

Result: Zero downtime! 🎉

**✅ Verification: Check the Update Status**
```bash
# Check Deployment status
kubectl get deployment greeting-service-deployment

# Check rollout status
kubectl rollout status deployment greeting-service-deployment
```
**Expected output:**
```
deployment "greeting-service-deployment" successfully rolled out
```

**Check Rollout History**
```bash
# View revision history
kubectl rollout history deployment greeting-service-deployment
```
**Expected output:**
```
deployment.apps/greeting-service-deployment
REVISION  CHANGE-CAUSE
1         <none>
2         <none>
```
You have 2 revisions: `v1` (revision 1) and `v2` (revision 2).

**Step 6: Test the New Version**
Access your application in the browser: `http://localhost:30080`
You should now see:
*   "Hello from the UPDATED Backend! 🚀"
The new version message!

Refresh multiple times—you'll see it's consistently the new version across both Pods.

**Part C: Rollback (Undoing an Update)**
What if the new version has a bug? Let's roll back!

**Rollback to Previous Version**
```bash
# Undo the last deployment (go back to v1)
kubectl rollout undo deployment greeting-service-deployment
```
**Expected output:**
```
deployment.apps/greeting-service-deployment rolled back
```

**Watch the Rollback**
```bash
kubectl get pods --watch
```
You'll see the same rolling pattern, but this time going back to `v1`:
*   New Pods created with `v1` image
*   Old Pods (`v2`) terminated
*   Zero downtime!

**✅ Verification: Check You're Back on v1**
Access the application: `http://localhost:30080`
You should see the original message:
*   "Hello from the Backend!" (no "UPDATED")

**Rollback to a Specific Revision**
```bash
# View history
kubectl rollout history deployment greeting-service-deployment

# Rollback to a specific revision (e.g., revision 2)
kubectl rollout undo deployment greeting-service-deployment --to-revision=2
```
This rolls forward to `v2` again.

**Pause and Resume Rollouts**
You can pause a rollout (useful for testing):
```bash
# Pause the rollout
kubectl rollout pause deployment greeting-service-deployment

# Make changes... (e.g., update image)
kubectl set image deployment/greeting-service-deployment greeting-service=greeting-service:v2

# Resume the rollout
kubectl rollout resume deployment greeting-service-deployment
```

**Part D: Update Strategy Configuration**
You can customize the rolling update behavior. Edit your Deployment:
```yaml
spec:
  replicas: 2
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 0  # Keep all Pods running during update
      maxSurge: 1        # Allow 1 extra Pod during update
```
**Options:**
*   `maxUnavailable: 0`: No downtime (at least 2 Pods always available)
*   `maxSurge: 1`: Creates 1 new Pod before terminating old ones
*   `maxUnavailable: 1, maxSurge: 0`: Replace Pods one-by-one (slower but no extra resources)

---

#### Visual: Rolling Update Flow
```
Initial State (v1):
Pod-A (v1) ─┐
            ├─ Service ← Traffic
Pod-B (v1) ─┘

Step 1: Create new Pod
Pod-A (v1) ─┐
Pod-B (v1) ─┤─ Service ← Traffic
Pod-C (v2) ─┘ (creating...)

Step 2: New Pod ready, terminate old Pod
Pod-B (v1) ─┐
Pod-C (v2) ─┤─ Service ← Traffic
Pod-A (v1)   (terminating...)

Step 3: Create another new Pod
Pod-B (v1) ─┐
Pod-C (v2) ─┤─ Service ← Traffic  
Pod-D (v2) ─┘ (creating...)

Step 4: Final state (v2)
Pod-C (v2) ─┐
            ├─ Service ← Traffic
Pod-D (v2) ─┘
```
✅ Zero downtime throughout!

**✅ Final Verification Checklist**
*   Scaled `greeting-service` from 2 to 3 replicas successfully
*   Service automatically load-balanced to all 3 Pods
*   Built a new Docker image (`v2`)
*   Performed rolling update from `v1` to `v2` with zero downtime
*   Verified the new version in browser
*   Successfully rolled back to `v1`
*   Understand rollout history and revision management

**🎓 Key Takeaways**
*   Scaling is as simple as changing replicas count
*   Services automatically adapt to scaled Pods (no configuration needed)
*   Rolling updates deploy new versions gradually with zero downtime
*   Rollbacks let you quickly revert to a previous version
*   Kubernetes tracks revision history so you can roll back to any version
*   `RollingUpdate` strategy controls how updates happen (`maxSurge`, `maxUnavailable`)
*   Always tag your images (`v1`, `v2`, `v3`) never use `:latest` in production

**Essential Commands Summary**
```bash
# Scaling
kubectl scale deployment <name> --replicas=<number>

# Update image
kubectl set image deployment/<name> <container>=<image>:<tag>

# Rollout status
kubectl rollout status deployment/<name>

# Rollout history
kubectl rollout history deployment/<name>

# Rollback (undo)
kubectl rollout undo deployment/<name>

# Rollback to specific revision
kubectl rollout undo deployment/<name> --to-revision=<number>

# Pause rollout
kubectl rollout pause deployment/<name>

# Resume rollout
kubectl rollout resume deployment/<name>
```

**What You've Mastered! 🎉**
You can now:
✅ Scale applications up and down
✅ Deploy new versions with zero downtime
✅ Roll back problematic deployments
✅ Understand how Kubernetes manages application lifecycle

These are critical production skills! Most Kubernetes Day-2 operations involve scaling and updating workloads.