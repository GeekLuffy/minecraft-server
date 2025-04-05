import os
import subprocess
import threading
import time
import glob
import zipfile
import datetime
import base64
import io
from bson import Binary
from pymongo import MongoClient
from flask import Flask, render_template_string, request, redirect, url_for, send_file

app = Flask(__name__)

# Server directory
SERVER_DIR = "/tmp/bedrock"
WORLDS_DIR = f"{SERVER_DIR}/worlds"
BACKUP_DIR = "/tmp/backups"

# MongoDB setup
def get_mongodb_client():
    mongodb_uri = os.environ.get('MONGODB_URI')
    if not mongodb_uri:
        print("MongoDB URI not set in environment variables")
        return None
    
    try:
        client = MongoClient(mongodb_uri)
        return client
    except Exception as e:
        print(f"Error connecting to MongoDB: {e}")
        return None

# Start Minecraft server in a separate thread
def start_minecraft_server():
    # Path to bedrock_server executable
    server_path = f"{SERVER_DIR}/bedrock_server"
    
    if not os.path.exists(server_path):
        print(f"ERROR: Could not find bedrock_server executable at {server_path}!")
        return
        
    print(f"Found Minecraft server at: {server_path}")
    
    # Start the server
    print("Starting Minecraft Bedrock server...")
    try:
        # Use shell=True to bypass permission issues
        process = subprocess.Popen(f"cd {SERVER_DIR} && ./bedrock_server", 
                                  shell=True,
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
        # Try alternative approach with bash -c
        try:
            print("Trying alternative approach with bash...")
            process = subprocess.Popen(["bash", "-c", f"cd {SERVER_DIR} && ./bedrock_server"],
                                      stdout=subprocess.PIPE,
                                      stderr=subprocess.STDOUT,
                                      universal_newlines=True)
            # Rest of code same as above
            while True:
                output = process.stdout.readline()
                if output:
                    print(output.strip())
                if process.poll() is not None:
                    break
            print("Minecraft server has stopped with return code:", process.returncode)
        except Exception as e2:
            print(f"Second attempt also failed: {e2}")

# Start the server in a background thread
minecraft_thread = threading.Thread(target=start_minecraft_server)
minecraft_thread.daemon = True
minecraft_thread.start()

# Function to create a backup of the world
def create_world_backup():
    if not os.path.exists(WORLDS_DIR):
        return None, "Worlds directory not found"
    
    try:
        # Create a backup filename with timestamp
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f"world_backup_{timestamp}.zip"
        backup_path = f"{BACKUP_DIR}/{backup_filename}"
        
        # Create backup directory if it doesn't exist
        os.makedirs(BACKUP_DIR, exist_ok=True)
        
        # Create a zip file containing the worlds directory
        with zipfile.ZipFile(backup_path, 'w') as zipf:
            for root, _, files in os.walk(WORLDS_DIR):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, os.path.dirname(WORLDS_DIR))
                    zipf.write(file_path, arcname)
        
        print(f"Created backup at {backup_path}")
        return backup_path, backup_filename, None
    except Exception as e:
        print(f"Error creating backup: {e}")
        return None, None, str(e)

# Function to upload backup to MongoDB
def upload_to_mongodb(file_path, filename):
    client = get_mongodb_client()
    if not client:
        return False, "MongoDB connection failed"
    
    try:
        # Read the zip file
        with open(file_path, 'rb') as f:
            zip_data = f.read()
        
        # Get the database and collection
        db = client.minecraft_backups
        backups = db.world_backups
        
        # Prepare metadata
        metadata = {
            'filename': filename,
            'timestamp': datetime.datetime.now(),
            'size': len(zip_data),
            'world_data': Binary(zip_data)  # Store the binary data
        }
        
        # Insert the backup
        result = backups.insert_one(metadata)
        
        # Cleanup old backups (keep only the 5 most recent)
        old_backups = list(backups.find().sort('timestamp', -1).skip(5))
        if old_backups:
            old_ids = [b['_id'] for b in old_backups]
            backups.delete_many({'_id': {'$in': old_ids}})
        
        return True, f"Uploaded to MongoDB (ID: {result.inserted_id})"
    except Exception as e:
        return False, f"MongoDB upload error: {str(e)}"
    finally:
        client.close()

# Function to get a list of backups from MongoDB
def get_backups_from_mongodb():
    client = get_mongodb_client()
    if not client:
        return []
    
    try:
        db = client.minecraft_backups
        backups = db.world_backups
        
        # Get all backups, sorted by timestamp (newest first)
        backup_list = list(backups.find({}, {'filename': 1, 'timestamp': 1, 'size': 1}).sort('timestamp', -1))
        return backup_list
    except Exception as e:
        print(f"Error fetching backups from MongoDB: {e}")
        return []
    finally:
        client.close()

# Function to download a backup from MongoDB
def download_from_mongodb(backup_id):
    client = get_mongodb_client()
    if not client:
        return None, None, "MongoDB connection failed"
    
    try:
        db = client.minecraft_backups
        backups = db.world_backups
        
        # Find the backup by ID
        from bson.objectid import ObjectId
        backup = backups.find_one({'_id': ObjectId(backup_id)})
        
        if not backup:
            return None, None, "Backup not found"
        
        return backup['world_data'], backup['filename'], None
    except Exception as e:
        return None, None, f"MongoDB download error: {str(e)}"
    finally:
        client.close()

# Simple status page
@app.route('/')
def index():
    # Check if server is running
    server_running = os.path.exists(f"{SERVER_DIR}/bedrock_server")
    
    # Check if real server or dummy server
    is_dummy = False
    if server_running:
        with open(f"{SERVER_DIR}/bedrock_server", 'r') as f:
            content = f.read()
            if "dummy server" in content:
                is_dummy = True
    
    # Check if worlds directory exists and get world names
    worlds = []
    if os.path.exists(WORLDS_DIR):
        worlds = [d for d in os.listdir(WORLDS_DIR) if os.path.isdir(os.path.join(WORLDS_DIR, d))]
    
    # Get backups from MongoDB
    backups = get_backups_from_mongodb()
    
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
            .backup {
                padding: 20px;
                background-color: #e3f2fd;
                border-radius: 10px;
                margin: 20px 0;
                text-align: left;
            }
            .error {
                padding: 20px;
                background-color: #ffebee;
                border-radius: 10px;
                margin: 20px 0;
                text-align: left;
            }
            h1 {
                color: #2e7d32;
            }
            button {
                background-color: #4CAF50;
                border: none;
                color: white;
                padding: 10px 20px;
                text-align: center;
                text-decoration: none;
                display: inline-block;
                font-size: 16px;
                margin: 10px 2px;
                cursor: pointer;
                border-radius: 5px;
            }
            .warning {
                color: #f44336;
                font-weight: bold;
            }
            table {
                width: 100%;
                border-collapse: collapse;
                margin-top: 15px;
            }
            table, th, td {
                border: 1px solid #ddd;
            }
            th, td {
                padding: 8px;
                text-align: left;
            }
            th {
                background-color: #f2f2f2;
            }
            tr:nth-child(even) {
                background-color: #f9f9f9;
            }
            a {
                color: #2196F3;
                text-decoration: none;
            }
            a:hover {
                text-decoration: underline;
            }
        </style>
    </head>
    <body>
        <h1>Minecraft Bedrock Server</h1>
        <div class="status">
            <h2>Server Status: {{ "Running" if server_running else "Not Running" }}</h2>
            {% if server_running and not is_dummy %}
            <p>Server is running on port 19132</p>
            <p>Connect using the server address:</p>
            <code>{{ server_address }}</code>
            {% elif server_running and is_dummy %}
            <p class="warning">Running in DUMMY mode. The server couldn't be downloaded.</p>
            <p>You can try to:</p>
            <ol style="text-align: left; display: inline-block;">
                <li>Wait a few minutes and refresh this page</li>
                <li>Restart the app from Heroku dashboard</li>
                <li>Manually download the server file (see below)</li>
            </ol>
            <div class="error">
                <h3>Manual Server Download</h3>
                <p>If automatic download keeps failing, try these steps:</p>
                <ol>
                    <li>Download the Bedrock server ZIP from <a href="https://www.minecraft.net/en-us/download/server/bedrock" target="_blank">official Minecraft site</a> or a mirror</li>
                    <li>Extract it locally</li>
                    <li>Compress the server files into a ZIP named "bedrock-server.zip"</li>
                    <li>Upload it to /tmp/bedrock/ directory on this Heroku app (contact support if needed)</li>
                </ol>
            </div>
            {% else %}
            <p class="warning">Server is not running. Please check the logs.</p>
            {% endif %}
        </div>
        
        <div class="backup">
            <h2>World Backup</h2>
            {% if worlds %}
            <p>Worlds found: {{ worlds|join(", ") }}</p>
            <form action="/backup" method="post">
                <button type="submit">Create Backup</button>
            </form>
            
            {% if backups %}
            <h3>Available Backups</h3>
            <table>
                <tr>
                    <th>Filename</th>
                    <th>Date</th>
                    <th>Size</th>
                    <th>Actions</th>
                </tr>
                {% for backup in backups %}
                <tr>
                    <td>{{ backup.filename }}</td>
                    <td>{{ backup.timestamp.strftime('%Y-%m-%d %H:%M:%S') }}</td>
                    <td>{{ (backup.size / (1024*1024))|round(2) }} MB</td>
                    <td>
                        <a href="/download/{{ backup._id }}">Download</a> | 
                        <a href="/restore/{{ backup._id }}" onclick="return confirm('Are you sure you want to restore this backup? Current world data will be lost.');">Restore</a>
                    </td>
                </tr>
                {% endfor %}
            </table>
            {% endif %}
            
            <p class="warning">NOTE: Due to Heroku's ephemeral filesystem, worlds will be lost when the server restarts.</p>
            <p>World data is automatically backed up to MongoDB every 15 minutes.</p>
            {% else %}
            <p>No worlds found yet. Start playing first!</p>
            {% endif %}
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
    
    return render_template_string(html, 
                                  server_address=server_address,
                                  server_running=server_running,
                                  is_dummy=is_dummy,
                                  worlds=worlds,
                                  backups=backups)

@app.route('/backup', methods=['POST'])
def backup():
    backup_path, backup_filename, error = create_world_backup()
    
    if error:
        return f"Error creating backup: {error}", 500
    
    # Upload to MongoDB
    success, message = upload_to_mongodb(backup_path, backup_filename)
    
    if success:
        return f"Backup created and uploaded to MongoDB: {backup_filename}<br>{message}<br><a href='/'>Back to Server Status</a>"
    else:
        # If MongoDB upload failed, offer direct download
        return f"""
        Backup created: {backup_filename}<br>
        {message}<br>
        <a href='/download_file/{backup_filename}'>Download Backup</a><br>
        <a href='/'>Back to Server Status</a>
        """

@app.route('/download/<backup_id>')
def download(backup_id):
    # Download from MongoDB
    backup_data, filename, error = download_from_mongodb(backup_id)
    
    if error:
        return f"Error downloading backup: {error}", 500
    
    # Create a BytesIO object from the binary data
    byte_io = io.BytesIO(backup_data)
    
    # Return the file
    return send_file(
        byte_io,
        mimetype='application/zip',
        as_attachment=True,
        download_name=filename
    )

@app.route('/download_file/<filename>')
def download_file(filename):
    if not filename.startswith('world_backup_') or not filename.endswith('.zip'):
        return "Invalid filename", 400
    
    file_path = f"{BACKUP_DIR}/{filename}"
    if not os.path.exists(file_path):
        return "Backup file not found", 404
    
    return send_file(file_path, as_attachment=True)

@app.route('/restore/<backup_id>')
def restore(backup_id):
    # Download from MongoDB
    backup_data, filename, error = download_from_mongodb(backup_id)
    
    if error:
        return f"Error downloading backup: {error}", 500
    
    try:
        # Save the backup to a temporary file
        temp_path = f"{BACKUP_DIR}/temp_restore.zip"
        with open(temp_path, 'wb') as f:
            f.write(backup_data)
        
        # Clear existing worlds directory
        if os.path.exists(WORLDS_DIR):
            import shutil
            shutil.rmtree(WORLDS_DIR)
        
        # Create worlds directory
        os.makedirs(WORLDS_DIR, exist_ok=True)
        
        # Extract the backup
        with zipfile.ZipFile(temp_path, 'r') as zip_ref:
            zip_ref.extractall(WORLDS_DIR)
        
        # Remove the temporary file
        os.remove(temp_path)
        
        return f"Backup {filename} has been restored.<br><a href='/'>Back to Server Status</a>"
    except Exception as e:
        return f"Error restoring backup: {str(e)}", 500

if __name__ == '__main__':
    # Create backup directory if it doesn't exist
    os.makedirs(BACKUP_DIR, exist_ok=True)
    
    # Get the port from Heroku environment variable
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port) 