# Use an optimized Python base image
FROM python:3.10-slim

# Set the working directory
WORKDIR /task-agent-api

# Copy and install dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Ensure environment variables are loaded
ENV PYTHONUNBUFFERED=1

# Expose the FastAPI server port
EXPOSE 8000

# Run the FastAPI application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
