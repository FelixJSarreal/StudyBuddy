#!/usr/bin/env python3
from flask import Flask
import RPi.GPIO as GPIO

app = Flask(__name__)
LED_PIN = 17

GPIO.setmode(GPIO.BCM)
GPIO.setup(LED_PIN, GPIO.OUT)
GPIO.output(LED_PIN, GPIO.LOW)

@app.route('/led/on')
def led_on():
    GPIO.output(LED_PIN, GPIO.HIGH)
    return "LED ON", 200

@app.route('/led/off')
def led_off():
    GPIO.output(LED_PIN, GPIO.LOW)
    return "LED OFF", 200

@app.route('/')
def status():
    return "LED Control Server Running", 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

