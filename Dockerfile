FROM itzg/minecraft-bedrock-server:latest as minecraft

# Second stage for Python application
FROM python:3.11-slim

WORKDIR /app

# Copy Python application files
COPY app.py .
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy Minecraft server files from the first stage
COPY --from=minecraft /opt/bedrock /opt/bedrock

# Copy server.properties to the right location
COPY server.properties /opt/bedrock/server.properties

# Environment variables for Minecraft server
ENV EULA=TRUE
ENV GAMEMODE=survival
ENV DIFFICULTY=normal
ENV LEVEL_NAME=Bedrock
ENV SERVER_NAME="My Bedrock Server"
ENV MAX_PLAYERS=10
ENV SERVER_PORT=19132

# Expose web port for Python app
EXPOSE $PORT

# Expose Minecraft port
EXPOSE 19132

# Command to run when the container starts
CMD ["gunicorn", "--bind", "0.0.0.0:$PORT", "app:app"]
