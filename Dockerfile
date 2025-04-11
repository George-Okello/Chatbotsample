# Use Python 3.12 slim as base image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Copy files
COPY . .

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip
RUN pip install --upgrade pip

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install additional package for SerpAPI
RUN pip install google-search-results

# Expose Chainlit default port
EXPOSE 8000

# Run Chainlit app
CMD ["chainlit", "run", "main.py", "-w"]
