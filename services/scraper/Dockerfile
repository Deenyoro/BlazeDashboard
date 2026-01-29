FROM mcr.microsoft.com/playwright:v1.40.0-focal

WORKDIR /app

# Install cron
RUN apt-get update && apt-get install -y cron && rm -rf /var/lib/apt/lists/*

# Copy package files and install dependencies
COPY package*.json ./
RUN npm install

# Copy application files
COPY . .

# Make scheduler script executable
RUN chmod +x scheduler.sh

# Create exports and logs directories
RUN mkdir -p /exports/logs

# Set timezone to EST
ENV TZ=America/New_York
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Default command for manual runs
CMD ["node", "scraper.js", "incremental"]
