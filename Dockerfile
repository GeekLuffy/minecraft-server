FROM eclipse-temurin:21-jdk

WORKDIR /server

# Install required packages including unzip for ngrok
RUN apt-get update && apt-get install -y wget && \
    wget -O paper.jar https://api.papermc.io/v2/projects/paper/versions/1.21.4/builds/222/downloads/paper-1.21.4-222.jar


RUN ls -lah paper.jar

COPY entrypoint.sh /entrypoint.sh
COPY eula.txt .
COPY server.properties .
COPY plugins/ ./plugins/
COPY config/ ./config/

EXPOSE 25565  # Java Edition
EXPOSE 19132  # Bedrock Edition (TCP now, not UDP)

RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
