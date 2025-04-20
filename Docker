# Use official Python image
FROM python:3.12-slim

# Set work directory
WORKDIR /app

# Copy project files
COPY . /app

# Install system dependencies (if needed, e.g., for building wheels)
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Expose port used by Chainlit
EXPOSE 8000

# Default command to run the Chainlit app
CMD ["chainlit", "run", "main.py", "-w"]
