#!/bin/bash
set -e

echo "Starting Minecraft Bedrock server setup..."

# Download the server if it doesn't exist
if [ ! -f /opt/bedrock/bedrock_server ]; then
    echo "Bedrock server not found, downloading..."
    mkdir -p /opt/bedrock
    cd /opt/bedrock
    
    # Download latest Bedrock server
    wget -q -O bedrock-server.zip https://minecraft.azureedge.net/bin-linux/bedrock-server-1.20.62.02.zip || \
    wget -q -O bedrock-server.zip https://download.mcbedrock.com/bedrock-server-1.20.62.02.zip
    
    unzip -q bedrock-server.zip
    rm bedrock-server.zip
    chmod +x bedrock_server
    
    echo "Bedrock server downloaded and extracted to /opt/bedrock"
    ls -la /opt/bedrock
fi

# Start the Flask web server
echo "Starting web server on port $PORT..."
cd /app
exec gunicorn --bind 0.0.0.0:$PORT app:app 