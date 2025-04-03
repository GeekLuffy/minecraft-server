#!/bin/sh
echo "Starting Minecraft Server..."
java -Xms4G -Xmx7G -XX:+UseG1GC -XX:+ParallelRefProcEnabled -jar paper.jar nogui
