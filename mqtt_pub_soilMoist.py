#-*- coding:utf-8 -*-
import json
import time
import sys
sys.path.insert(0, '/home/pi/.local/lib/python2.7/site-packages')
import paho.mqtt.client as mqtt
import spidev


def read_spi_adc(adcChannel): #adc 읽는 함수
    adcValue=0
    buff=spi.xfer2([1,(8+adcChannel)<<4,0])
    adcValue = ((buff[1]&3)<<8)+buff[2]
    return adcValue

def map(value,min_adc,max_adc,min_hum,max_hum): #0에서1024를 보기편하게 퍼센트로 변환
    adc_range=max_adc-min_adc
    hum_range=max_hum-min_hum
    scale_factor=float(adc_range)/float(hum_range)
    return min_hum+((value-min_adc)/scale_factor)

soil_moist=[0,0,0,0,0] #토양수분
soilAvg = 0
adcChannel = 0

spi=spidev.SpiDev() #아날로그컨버터 설정
spi.open(0,0)
spi.max_speed_hz=500000

client = mqtt.Client() #Mqtt Client 오브젝트 생성
client.username_pw_set("i8Z9q746hzgY214QCOrw")
client.connect("demo.thingsboard.io", 1883) #MQTT 서버에 연결


for i in range(5):
    adcValue = read_spi_adc(adcChannel)
    shum = 100-int(map(adcValue,0,1023,0,100))

    print(shum)

    soil_moist[i]=shum #리스트에 저장
           
    if i==4:
        print("here")
        ssum=0 
        for j in range(5):
            ssum+=soil_moist[j]
        print("here22")
        soilAvg=ssum/5
    
    time.sleep(1) #센서 읽는 주기. 



sensor_data = {'soil_moist':soilAvg}
print(sensor_data)
client.publish("v1/devices/me/telemetry", json.dumps(sensor_data),1) #토픽과 메세지 발행


client.loop(2) #timeout 2sec.

