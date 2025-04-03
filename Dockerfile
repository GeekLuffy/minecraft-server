FROM openjdk:17-jdk-slim

WORKDIR /server

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
