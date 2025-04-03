FROM ubuntu:22.04

WORKDIR /server

# Install required packages
RUN apt-get update && apt-get install -y wget unzip curl libcurl4 libssl3 && \
    rm -rf /var/lib/apt/lists/*

# Download and set up Bedrock server
RUN wget -O bedrock-server.zip https://minecraft.azureedge.net/bin-linux/bedrock-server-1.21.71.01.zip && \
    unzip bedrock-server.zip && \
    rm bedrock-server.zip && \
    chmod +x bedrock_server

# Copy config files
COPY server.properties .
COPY entrypoint.sh /entrypoint.sh

EXPOSE 19132/tcp
EXPOSE 19132/udp

RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
