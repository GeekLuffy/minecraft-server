import os
import subprocess
import threading
import time
import glob
from flask import Flask, render_template_string, request

app = Flask(__name__)

# Start Minecraft server in a separate thread
def start_minecraft_server():
    # Path to bedrock_server executable - try different possible locations
    possible_paths = [
        "/opt/bedrock/bedrock_server",
        "/data/bedrock_server", 
        "/bedrock_server"
    ]
    
    server_path = None
    for path in possible_paths:
        if os.path.exists(path):
            server_path = path
            break
    
    if not server_path:
        print("ERROR: Could not find bedrock_server executable!")
        print("Checking server directories:")
        os.system("find /opt -type d | sort")
        print("Searching for bedrock_server executable:")
        os.system("find / -name 'bedrock_server' 2>/dev/null || echo 'Not found'")
        return
        
    print(f"Found Minecraft server at: {server_path}")
    print("Directory contents:")
    os.system(f"ls -la {os.path.dirname(server_path)}")
    
    # Create a wrapper script to execute the server
    wrapper_path = "/tmp/run_minecraft.sh"
    with open(wrapper_path, "w") as f:
        f.write("#!/bin/bash\n")
        f.write(f"cd {os.path.dirname(server_path)}\n")
        f.write(f"exec {server_path}\n")
    
    os.chmod(wrapper_path, 0o755)
    print(f"Created wrapper script at {wrapper_path}")
    
    print("Starting Minecraft Bedrock server...")
    try:
        process = subprocess.Popen([wrapper_path], 
                                  stdout=subprocess.PIPE,
                                  stderr=subprocess.STDOUT,
                                  universal_newlines=True)
        
        # Keep the process running and log output
        while True:
            output = process.stdout.readline()
            if output:
                print(output.strip())
            # If process has terminated
            if process.poll() is not None:
                break
        
        print("Minecraft server has stopped with return code:", process.returncode)
    except Exception as e:
        print(f"Error starting Minecraft server: {e}")

# Start the server in a background thread
minecraft_thread = threading.Thread(target=start_minecraft_server)
minecraft_thread.daemon = True
minecraft_thread.start()

# Simple status page
@app.route('/')
def index():
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Minecraft Bedrock Server Status</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
                text-align: center;
            }
            .status {
                padding: 20px;
                background-color: #e8f5e9;
                border-radius: 10px;
                margin: 20px 0;
            }
            h1 {
                color: #2e7d32;
            }
        </style>
    </head>
    <body>
        <h1>Minecraft Bedrock Server</h1>
        <div class="status">
            <h2>Server Status: Running</h2>
            <p>Server is running on port 19132</p>
            <p>Connect using the server address:</p>
            <code>{{ server_address }}</code>
        </div>
        <p>To connect from Minecraft Bedrock Edition:</p>
        <ol style="text-align: left; display: inline-block;">
            <li>Open Minecraft</li>
            <li>Click "Play"</li>
            <li>Go to "Servers" tab</li>
            <li>Click "Add Server"</li>
            <li>Enter any name you want</li>
            <li>For the address, enter the server address shown above</li>
            <li>For the port, enter 19132</li>
            <li>Click "Save" and then connect to your server!</li>
        </ol>
    </body>
    </html>
    """
    # Get the server address from request URL
    server_address = request.host.split(':')[0]
    
    return render_template_string(html, server_address=server_address)

if __name__ == '__main__':
    # Get the port from Heroku environment variable
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port) 