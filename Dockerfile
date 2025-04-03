FROM ubuntu:22.04

RUN apt update && apt install -y openjdk-17-jdk curl unzip

WORKDIR /minecraft

RUN curl -o paper.jar https://api.papermc.io/v2/projects/paper/versions/1.20.4/builds/latest/downloads/paper-1.20.4.jar

COPY server.properties . 
COPY eula.txt . 
COPY start.sh .

RUN chmod +x start.sh

EXPOSE 25565

CMD ["sh", "./start.sh"]
