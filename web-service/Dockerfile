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