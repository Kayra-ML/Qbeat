# Use an official Python runtime as a parent image, slim version for smaller size
FROM python:3.12-slim

# Create a non-root user for security
RUN useradd -m -r botuser

# Set the working directory
WORKDIR /app

# Install FFmpeg and Opus (required for audio streaming)
RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg libopus0 libsodium-dev libffi-dev build-essential && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements file first to leverage Docker cache
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Change ownership of the app directory to the non-root user
RUN chown -R botuser:botuser /app

# Switch to the non-root user
USER botuser

# Command to run the bot, -u ensures unbuffered output for Railway logging
CMD ["python", "-u", "bot.py"]
