ARG BUILD_FROM
FROM $BUILD_FROM

# Install required packages
RUN apk add --no-cache \
    python3 \
    py3-pip \
    chromium \
    chromium-chromedriver \
    tzdata

# Set environment for headless Chrome
ENV CHROME_BIN=/usr/bin/chromium-browser \
    CHROME_PATH=/usr/lib/chromium/ \
    CHROMEDRIVER_PATH=/usr/bin/chromedriver

# Create app directory
WORKDIR /app

# Copy application files
COPY requirements.txt .
COPY src/ ./src/
COPY cli.py .
COPY api_server.py .
COPY default.yml ./config/
COPY run.sh .

# Install Python dependencies
RUN pip3 install --no-cache-dir -r requirements.txt

# Make run script executable
RUN chmod +x run.sh

# Copy data will be mounted at /data
CMD ["/app/run.sh"]
