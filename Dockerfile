# Step 1: Use a specific, slim, and secure Python base image
# This matches the Python 3.10 version on your server.
FROM python:3.10-slim-bullseye

# Step 2: Set environment variables for Python
# Prevents Python from writing .pyc files to the container
ENV PYTHONDONTWRITEBYTECODE 1
# Ensures that Python output is sent straight to the terminal without being buffered
ENV PYTHONUNBUFFERED 1

# Step 3: Set the working directory inside the container
WORKDIR /app

# Step 4: Create a non-root user for security
# Running containers as a non-root user is a critical security best practice.
RUN useradd -m appuser
USER appuser

# Step 5: Install dependencies
# Copy only the requirements file first to leverage Docker's build cache.
# This step will only be re-run if the requirements file changes.
COPY --chown=appuser:appuser requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Step 6: Copy your application code into the container
# This includes wsgi.py, server.py, config.py, and the src/, migrations/, templates/ folders.
COPY --chown=appuser:appuser . .

# Step 7: Expose the port that Gunicorn will run on inside the container
EXPOSE 8000

# Step 8: Define the command to run your application
# We know from our manual testing that the correct command is 'wsgi:payverve'
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "wsgi:payverve"]
