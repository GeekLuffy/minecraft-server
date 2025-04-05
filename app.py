import os
import subprocess
import threading
import time
from flask import Flask, render_template_string

app = Flask(__name__)

# Start Minecraft server in a separate thread
def start_minecraft_server():
    # Path to bedrock_server executable from the Docker container
    server_path = "/opt/bedrock/bedrock_server"
    
    # If we're running locally without Docker, don't try to start the server
    if not os.path.exists(server_path):
        print("Running in development mode - Minecraft server not started")
        return
        
    print("Starting Minecraft Bedrock server...")
    process = subprocess.Popen([server_path], 
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
    # Get the server address from Heroku environment variables or use localhost
    server_address = os.environ.get('HEROKU_APP_NAME', 'localhost')
    if server_address != 'localhost':
        server_address += '.herokuapp.com'
    
    return render_template_string(html, server_address=server_address)

if __name__ == '__main__':
    # Get the port from Heroku environment variable
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port) 