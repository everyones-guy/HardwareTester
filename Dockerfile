# Use a Python base image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Set SQLite database as a fallback
ENV DATABASE_URL="sqlite:///instance/fallback.db"

# Run the application
CMD ["gunicorn", "-b", "0.0.0.0:5000", "HardwareTester:app"]
