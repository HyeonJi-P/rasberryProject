# rasberryProject
2020라즈베리파이 스마트화분

<H2>How to commit&push</H2>
git add .
git commit -m "comment"
git push -u origin main

down load 
git pull

if have problem when pull
git fetch --all
git reset --hard origin/main
git pull origin main

mqtt설치
 pip install paho-mqtt

 mosquitto_pub -d -q 1 -h "demo.thingsboard.io" -p "1883" -t "v1/devices/me/telemetry" -u "엑세스토큰값" -m {"temperature":25}