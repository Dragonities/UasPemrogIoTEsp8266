from machine import Pin, ADC
from time import sleep
import network
import machine
from umqtt.simple import MQTTClient
import ubinascii
import micropython
import esp
import gc
import dht
import urandom
import time

esp.osdebug(None)
gc.collect()

ssid = 'PCU_Sistem_Kontrol'
password = 'lasikonn'
station = network.WLAN(network.STA_IF)
station.active(True)
station.connect(ssid, password)

sensor_dht = dht.DHT11(Pin(14))  # pin d5
LDR = ADC(0)  # pin A0
RELAY_PIN = 2  # pin d4
led_pin = machine.Pin(5, machine.Pin.OUT)
previous_value = 0
is_delayed = False


while not station.isconnected():
    pass

print('connect success')
print(station.ifconfig())

broker = '192.168.41.71'
clientid = ubinascii.hexlify(machine.unique_id())
topicsub = b'4171/dht11/temp'
topicpub_temp = b'4171/dht11/temp'
topicpub_hum = b'4171/dht11/hum'
topicpub_ldr = b'4171/ldr'

topicpub_random = b'4171/random'
topicpub_relay = b'4171/relay'


def subscribecallback(topic, msg):
    print(topic, msg)
    # if topic == b'.....' and msg == b'.....'
    #   .....


def connect():
    global clientid, broker, topicsub, topicpub
    client = MQTTClient(clientid, broker)
    client.set_callback(subscribecallback)
    client.connect()
    client.subscribe(topicsub)
    print('Connected to %s, subscribed to %s' % (broker, topicsub))
    return client


def restartandconnect():
    print('failed to connect, restarting....')
    sleep(10)
    machine.reset()


def relay(topic, message):
    global previous_value, is_delayed
    if message == b'mati':
        if not is_delayed:
            relay.off()
            sleep(2)
            relay.on()
            is_delayed = True
            print('Delayed for 5 seconds before next operation...')
            time.sleep(5)  # Penundaan 5 detik
            is_delayed = False
            previous_value += 1
            if previous_value > 100:
                previous_value = 100
            client.publish(topicpub_random, '%d' % previous_value)
        
    elif message == b'nyala':
        if not is_delayed:
            relay.off()
            sleep(2)
            relay.on()
            is_delayed = True
            print('Delayed for 5 seconds before next operation...')
            time.sleep(5)  # Penundaan 5 detik
            is_delayed = False
            previous_value -= 1
            if previous_value < 0:
                previous_value = 0
            client.publish(topicpub_random, '%d' % previous_value)


def read_sensor_dht():
    while True:
        try:
            sleep(1)
            sensor_dht.measure()
            temp = sensor_dht.temperature()
            hum = sensor_dht.humidity()
            return temp, hum
        except OSError as e:
            print('Failed to read sensor.')


def read_LDR():
    while True:
        try:
            LDR_Parkir = LDR.read()
            sleep(1)
            HasilLDR = LDR_Parkir
            return HasilLDR
        except OSError as e:
            print('Failed to read sensor.')


try:
    client = connect()
except OSError as e:
    restartandconnect()

client.set_callback(relay)

relay = machine.Pin(RELAY_PIN, machine.Pin.OUT)
relay.off()

while True:
    try:
        sleep(1)
        temp, hum = read_sensor_dht()
        HasilLDR = read_LDR()
        msg = client.check_msg()

        if msg != 'None':
            client.publish(topicpub_temp, '%3.1f' % temp)
            client.publish(topicpub_hum, '%3.1f' % hum)
            client.publish(topicpub_ldr, '%3.1f' % HasilLDR)

            if not is_delayed:
                random_data = urandom.getrandbits(1) + 1
                time.sleep(7)  # Penundaan 1 detik
                  
                if random_data == 1:
                    previous_value += 1
                    if previous_value > 100:
                        previous_value = 100

                    relay.off()
                    sleep(2)  # Relay menyala selama 2 detik
                    relay.on()

                elif random_data == 2:
                    previous_value -= 1
                    if previous_value < 0:
                        previous_value = 0
                    relay.off()
                    sleep(2)  # Relay menyala selama 2 detik
                    relay.on()

                client.publish(topicpub_random, '%d' % previous_value)
                client.subscribe(topicpub_relay)
                client.subscribe(topicpub_ldr)

        if HasilLDR < 50:
            led_pin.on()
        else:
            led_pin.off()

    except OSError as e:
        restartandconnect()








