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
    
    # Define direct URLs to different versions (most recent first)
    DIRECT_URLS=(
        "https://www.minecraft.net/bedrockdedicatedserver/bin-linux/bedrock-server-1.21.71.01.zip"
        "https://minecraft.azureedge.net/bin-linux/bedrock-server-1.20.62.02.zip"
        "https://raw.githubusercontent.com/MCBEBackup/MinecraftBedrockServer/main/1.20.62.02.zip"
        "https://dl.devfee.org/minecraft/server/bedrock-server-1.20.62.02.zip"
        "https://download.mcbedrock.com/bedrock-server-1.20.62.02.zip"
    )
    
    # Try each URL in sequence
    download_success=false
    for url in "${DIRECT_URLS[@]}"; do
        echo "Trying download from: $url"
        if curl -L --fail -s -o bedrock-server.zip "$url"; then
            download_success=true
            echo "Download successful!"
            break
        else
            echo "Failed to download from $url"
        fi
    done
    
    # If all direct links fail, try creating a basic server
    if [ "$download_success" = false ]; then
        echo "All download attempts failed. Trying to download an older version..."
        # Try a last resort - an older version from a different source
        if curl -L --fail -s -o bedrock-server.zip "https://cdn.discordapp.com/attachments/1094003845623676929/1175146085115682997/bedrock-server-1.20.51.02.zip"; then
            download_success=true
            echo "Downloaded older version successfully!"
        else
            echo "All download attempts failed, creating dummy server."
        fi
    fi
    
    if [ "$download_success" = true ]; then
        echo "Extracting downloaded server..."
        unzip -q bedrock-server.zip
        rm bedrock-server.zip
        chmod +x bedrock_server
        
        echo "Bedrock server extracted to $SERVER_DIR"
        ls -la "$SERVER_DIR"
    else
        echo "ERROR: All download attempts failed."
        echo "Creating a dummy server file for testing..."
        # Create a dummy file so the server thinks it exists
        echo "#!/bin/bash" > bedrock_server
        echo "echo 'This is a dummy server for testing. Real server download failed.'" >> bedrock_server
        echo "echo 'Please check logs for download errors.'" >> bedrock_server
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
server_pid=$!
echo "Minecraft server process started with PID $server_pid"

# Start the Flask web server
echo "Starting web server on port $PORT..."
cd /app
exec gunicorn --bind 0.0.0.0:$PORT app:app 