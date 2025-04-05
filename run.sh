#!/bin/bash
set -e

echo "Starting Minecraft Bedrock server setup..."

# Change to use /tmp directory which is writable on Heroku
SERVER_DIR="/tmp/bedrock"
BACKUP_DIR="/tmp/backups"

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Download the server if it doesn't exist
if [ ! -f "$SERVER_DIR/bedrock_server" ]; then
    echo "Bedrock server not found, downloading..."
    mkdir -p "$SERVER_DIR"
    cd "$SERVER_DIR"
    
    # Try multiple URLs and retry a few times with increasing delays
    download_success=false
    for attempt in {1..3}; do
        echo "Download attempt $attempt..."
        
        # Try primary URL
        if wget -q -O bedrock-server.zip https://minecraft.azureedge.net/bin-linux/bedrock-server-1.20.62.02.zip; then
            download_success=true
            break
        fi
        
        # Try backup URL
        if wget -q -O bedrock-server.zip https://download.mcbedrock.com/bedrock-server-1.20.62.02.zip; then
            download_success=true
            break
        fi
        
        # Try additional backup URL
        if wget -q -O bedrock-server.zip https://github.com/LeoZhou1234/MCBedrockServerStorage/releases/download/1.20.62/bedrock-server-1.20.62.02.zip; then
            download_success=true
            break
        fi
        
        echo "Download attempt $attempt failed. Waiting before retry..."
        sleep $((attempt * 5))
    done
    
    if [ "$download_success" = true ]; then
        echo "Download successful. Extracting..."
        unzip -q bedrock-server.zip
        rm bedrock-server.zip
        chmod +x bedrock_server
        
        echo "Bedrock server downloaded and extracted to $SERVER_DIR"
        ls -la "$SERVER_DIR"
    else
        echo "ERROR: All download attempts failed."
        echo "Creating an empty server file for testing..."
        # Create a dummy file so the server thinks it exists
        echo "#!/bin/bash" > bedrock_server
        echo "echo 'This is a dummy server for testing. Real server download failed.'" >> bedrock_server
        echo "while true; do sleep 60; done" >> bedrock_server
        chmod +x bedrock_server
    fi
fi

# Copy server.properties if it exists in the app directory
if [ -f "/app/server.properties" ] && [ ! -f "$SERVER_DIR/server.properties" ]; then
    echo "Copying server.properties to $SERVER_DIR"
    cp /app/server.properties "$SERVER_DIR/server.properties"
fi

# The restore functionality is now handled by the Flask app's /restore endpoint
# MongoDB connection and world restoration is managed by the Python code

# Start Minecraft server in background
echo "Starting Minecraft server in background..."
cd "$SERVER_DIR"
nohup ./bedrock_server > minecraft.log 2>&1 &
echo "Minecraft server process started with PID $!"

# Start the Flask web server
echo "Starting web server on port $PORT..."
cd /app
exec gunicorn --bind 0.0.0.0:$PORT app:app 