FROM node:20-slim

WORKDIR /app

# Install Pi Coding Agent
RUN npm install -g @earendil-works/pi-coding-agent

# Install Python for FastAPI server
RUN apt-get update && apt-get install -y python3 python3-pip && \
    rm -rf /var/lib/apt/lists/*

# Copy server files
COPY server.py .
COPY requirements.txt .

# Install Python dependencies
RUN pip3 install --break-system-packages -r requirements.txt

# Create .pi directory
RUN mkdir -p /app/.pi

EXPOSE 3000

CMD ["python3", "server.py"]
