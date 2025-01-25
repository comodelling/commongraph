FROM python:3.11-slim

# Set the working directory to /app
WORKDIR /app

# Set PYTHONPATH to include /app for absolute imports
ENV PYTHONPATH=/app:/app/backend

# Copy the requirements file
COPY backend/requirements.txt ./backend/requirements.txt

# Install the dependencies
RUN pip install --no-cache-dir -r backend/requirements.txt

# Copy the application code to /app/backend
COPY backend/ ./backend/

# Copy the VERSION file to /app/VERSION
COPY VERSION /app/VERSION

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
