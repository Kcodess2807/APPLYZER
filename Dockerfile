# Use slim python base image
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV ENVIRONMENT=production
ENV DEBUG=false

# Set work directory
WORKDIR /app

# Install system dependencies (e.g. for psycopg2, latex if needed)
# RUN apt-get update && apt-get install -y --no-install-recommends \
#     build-essential \
#     libpq-dev \
#     texlive-latex-base texlive-fonts-recommended texlive-fonts-extra texlive-latex-extra \
#     && rm -rf /var/lib/apt/lists/*

# Install python dependencies first to cache the layer
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . /app/

# Expose port
EXPOSE 8000

# Command to run the application (matches Makefile/main.py instructions)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
