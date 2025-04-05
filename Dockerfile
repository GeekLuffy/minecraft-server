FROM python:3.11-slim

WORKDIR /app

# Install dependencies
RUN apt-get update && \
    apt-get install -y wget unzip curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy Python application files
COPY app.py .
COPY requirements.txt .
COPY run.sh .

# Make run script executable
RUN chmod +x run.sh

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy server configuration
COPY server.properties /opt/bedrock/server.properties

# The server binary will be downloaded at startup
RUN mkdir -p /opt/bedrock

# Environment variables for Minecraft server
ENV EULA=TRUE
ENV GAMEMODE=survival
ENV DIFFICULTY=normal
ENV LEVEL_NAME=Bedrock
ENV SERVER_NAME="My Bedrock Server"
ENV MAX_PLAYERS=10
ENV SERVER_PORT=19132

# Expose Minecraft port (both TCP and UDP)
EXPOSE 19132/tcp
EXPOSE 19132/udp

# Expose web port for Python app (dynamic from Heroku)
EXPOSE 8080

# Command to run when the container starts
CMD ["/app/run.sh"]
