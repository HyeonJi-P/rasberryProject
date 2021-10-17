#-*- coding:utf-8 -*-
import json
import time
import sys
sys.path.insert(0, '/home/pi/.local/lib/python2.7/site-packages')
import paho.mqtt.client as mqtt
import Adafruit_DHT #Adafruit 기능을 가져옴

DHT11=Adafruit_DHT.DHT11
DHT11_PIN = 13 #온습도센서
temp=[0,0,0,0,0] #온도 리스트
hum=[0,0,0,0,0] #습도 리스트

client = mqtt.Client() #Mqtt Client 오브젝트 생성
client.username_pw_set("DtzOeQCJE7a8zztJRX9F")
client.connect("demo.thingsboard.io", 1883) #MQTT 서버에 연결


for i in range(5):
    #DHT11 sensor read 5times
    h, t = Adafruit_DHT.read_retry(DHT11, DHT11_PIN) #센서정보를 읽어오기 위한 코드
    print(h)
    print(t)
    if h is None and t is None:
        print("Read Err")
    hum[i]=h #리스트에 저장
    temp[i]=t            
    time.sleep(1) #센서 읽는 주기. 
    if i==4:
        print("here")
        tsum=0 #온도 합산용 지역변수
        hsum=0 #습도 합산용 지역변수
        for j in range(5):
            tsum+=temp[j]
            hsum+=hum[j]
        print("here22")
        tempAvg=tsum/5
        humAvg=hsum/5



sensor_data = {'temperature':tempAvg, 'hum':humAvg}
print(sensor_data)
client.publish("v1/devices/me/telemetry", json.dumps(sensor_data),1) #토픽과 메세지 발행


client.loop(2) #timeout 2sec.

