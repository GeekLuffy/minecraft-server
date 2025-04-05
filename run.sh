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
    echo "Bedrock server not found, setting up..."
    mkdir -p "$SERVER_DIR"
    cd "$SERVER_DIR"
    
    # Check for local copy first (zip format only)
    download_success=false
    
    # Check for zip file
    if [ -f "/app/bedrock-server-1.21.71.zip" ]; then
        echo "Found local copy of bedrock-server-1.21.71.zip, using it..."
        cp /app/bedrock-server-1.21.71.zip ./bedrock-server.zip
        download_success=true
        echo "Local zip copy used successfully!"
    else
        # Define direct URLs to different versions (most recent first)
        DIRECT_URLS=(
            "https://minecraft.azureedge.net/bin-linux/bedrock-server-1.21.71.01.zip"
            "https://dl.dejavucraft.eu/bedrock-server-1.21.71.01.zip"
            "https://www.mediafire.com/file/p49u0ztqjrz8vz2/bedrock-server-1.21.71.01.zip/file"
            "https://minecraft.azureedge.net/bin-linux/bedrock-server-1.20.62.02.zip"
        )
        
        # Try each URL in sequence
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
    fi
    
    if [ "$download_success" = true ]; then
        # Extract zip file
        echo "Extracting zip server..."
        unzip -q bedrock-server.zip
        rm bedrock-server.zip
        
        # Debug - list all files in the directory
        echo "Listing extracted files:"
        ls -la
        
        # Special handling based on actual file structure we've seen
        if [ -f "bedrock_server" ]; then
            echo "Found bedrock_server executable in root directory"
            chmod +x bedrock_server
        else
            # Try to find the bedrock_server executable in subdirectories
            echo "Searching for bedrock_server executable:"
            find . -type f -name "bedrock_server" || echo "No bedrock_server found"
            
            # If bedrock_server is in a subdirectory, move it up
            BEDROCK_EXECUTABLE=$(find . -type f -name "bedrock_server" | head -1)
            if [ -n "$BEDROCK_EXECUTABLE" ]; then
                echo "Found bedrock_server at: $BEDROCK_EXECUTABLE"
                # If in subdirectory, move everything up
                if [[ "$BEDROCK_EXECUTABLE" == *"/"* ]]; then
                    SUBDIR=$(dirname "$BEDROCK_EXECUTABLE")
                    echo "Moving files from subdirectory $SUBDIR"
                    mv "$SUBDIR"/* .
                    rmdir "$SUBDIR" || true
                fi
                chmod +x bedrock_server
            else
                echo "ERROR: bedrock_server executable not found in the extracted files!"
                # Create dummy executable
                echo "#!/bin/bash" > bedrock_server
                echo "echo 'This is a dummy server. Real server executable not found in zip.'" >> bedrock_server
                echo "echo 'Please check the contents of your zip file.'" >> bedrock_server
                echo "while true; do sleep 60; done" >> bedrock_server
            fi
        fi
        
        echo "Bedrock server extracted to $SERVER_DIR"
        ls -la "$SERVER_DIR"
    else
        echo "ERROR: All setup attempts failed."
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

# Final check if bedrock_server exists
if [ ! -f "./bedrock_server" ]; then
    echo "ERROR: bedrock_server not found, creating dummy..."
    echo "#!/bin/bash" > bedrock_server
    echo "echo 'This is a dummy server. Real server executable not found.'" >> bedrock_server
    echo "echo 'Please check the logs for details.'" >> bedrock_server
    echo "while true; do sleep 60; done" >> bedrock_server
    chmod +x bedrock_server
fi

# Make sure permissions are set correctly
chmod 755 bedrock_server
ls -la bedrock_server

# Start server through the shell to avoid permission issues
nohup bash -c "./bedrock_server > minecraft.log 2>&1" &
server_pid=$!
echo "Minecraft server process started with PID $server_pid"

# Start the Flask web server
echo "Starting web server on port $PORT..."
cd /app
exec gunicorn --bind 0.0.0.0:$PORT app:app 