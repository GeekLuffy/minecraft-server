FROM openjdk:17-jdk-slim

WORKDIR /server

RUN apt-get update && apt-get install -y wget && \
    wget -O paper.jar https://api.papermc.io/v2/projects/paper/versions/1.21.4/builds/222/downloads/paper-1.21.4-222.jar

COPY paper.jar .
COPY entrypoint.sh /entrypoint.sh
COPY eula.txt .
COPY server.properties .
COPY plugins/ ./plugins/
COPY config/ ./config/

EXPOSE 25565  # Java Edition
EXPOSE 19132/udp  # Bedrock Edition

RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
