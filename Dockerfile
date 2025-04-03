FROM itzg/minecraft-bedrock-server:latest

# Copy custom config files
COPY server.properties /data/server.properties

# Expose HTTP port
EXPOSE 19132

# Environment variables for server configuration
ENV EULA=TRUE
ENV GAMEMODE=survival
ENV DIFFICULTY=normal
ENV LEVEL_NAME=Bedrock
ENV SERVER_NAME="My Bedrock Server"
ENV MAX_PLAYERS=10
ENV SERVER_PORT=19132
