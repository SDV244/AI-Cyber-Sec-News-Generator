# Use the official Microsoft Playwright image as the base
# This image already contains all system dependencies for chromium
FROM mcr.microsoft.com/playwright/python:v1.44.0-jammy

# Set working directory
WORKDIR /app

# Install system dependencies required for WeasyPrint 
# (Playwright image handles most, but we need specific Pango/Cairo libs for PDF generation)
RUN apt-get update && apt-get install -y \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libharfbuzz0b \
    libfontconfig1 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies (including Streamlit)
RUN python -m pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir streamlit watchdog

# The base image already has the browsers installed, but we run this just to be certain
# it links correctly to our installed playwright python package
RUN playwright install chromium

# Copy application code
COPY . .

# Add local user bin to PATH so streamlit can be found as fallback
ENV PATH="/usr/local/bin:/root/.local/bin:${PATH}"

# Expose port for Streamlit
EXPOSE 8501

# Run the Streamlit app
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
