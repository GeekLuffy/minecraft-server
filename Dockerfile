FROM ubuntu:22.04

RUN apt update && apt install -y openjdk-17-jdk curl unzip

WORKDIR /minecraft

ENV PAPER_VERSION=1.21.4

RUN curl -L -o paper.jar "https://api.papermc.io/v2/projects/paper/versions/$PAPER_VERSION/builds/222/downloads/paper-$PAPER_VERSION-222.jar"

RUN ls -lh paper.jar && file paper.jar


COPY server.properties . 
COPY eula.txt . 
COPY start.sh .

RUN chmod +x start.sh

EXPOSE 25565

CMD ["sh", "./start.sh"]
