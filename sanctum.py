#!/usr/bin/env python3

import os
import hashlib
import struct
import pyaudio
from picovoice import Picovoice
import pigpio
import requests
import asyncio
from kasa import SmartBulb
import time

gpio = pigpio.pi()
gpio.set_mode(27, pigpio.OUTPUT)
gpio.set_mode(17, pigpio.OUTPUT)
gpio.set_mode(22, pigpio.OUTPUT)

lights = SmartBulb('192.168.0.18')

colours = {
        'black': (0, 0, 0),
        'blue': (0, 0, 10),
        'green': (0, 10, 0),
        'orange': (10, 5, 0),
        'pink': (10, 2, 2),
        'purple': (10, 0, 10),
        'red': (10, 0, 0),
        'white': (10, 10, 10),
        'yellow': (10, 10, 0),
        'warm': (10, 5, 2),
        'cold': (8, 8, 10)
        }

ledsColour = 'black'

def setColor(red, green, blue):
    gpio.set_PWM_dutycycle(27, red)
    gpio.set_PWM_dutycycle(17, green)
    gpio.set_PWM_dutycycle(22, blue)

keyword_path = 'computer_raspberry-pi.ppn'
context_path = 'Sanctum_raspberry-pi_2021-02-15-utc_v1_6_0.rhn'

def wake_word_callback():
    print('Hotword Detected')
    setColor(*colours['blue'])
    play('computerbeep_10.mp3')
    #say('Yes you sef')

def inference_callback(inference):
    global colours
    global ledsColour

    if not inference.is_understood:
        say("Sorry, I didn't understand that.")
    elif inference.intent == 'tellJoke':
        joke()
    elif inference.intent == 'lightsDim':
        print(inference)
    elif inference.intent == 'lightsMax':
        print(inference)
    elif inference.intent == 'lightsBrightness':
        print(inference)
    elif inference.intent == 'lightsColor':
        if (not ('which' in inference.slots)) or inference.slots['which'] == 'window':
            ledsColour = inference.slots['color']
    elif inference.intent == 'lightsState':
        if (not ('which' in inference.slots)) or inference.slots['which'] == 'main':
            if inference.slots['state'] == 'on':
                asyncio.run(lights.turn_on())
            else:
                asyncio.run(lights.turn_off())

        if (not ('which' in inference.slots)) or inference.slots['which'] == 'window':
            if inference.slots['state'] == 'on':
                ledsColour = 'warm'
            else:
                ledsColour = 'black'
    elif inference.intent == 'redAlert':
        setColor(*colours['red'])
        play('tos_red_alert_3.mp3');
    elif inference.intent == 'lightFold':
        print(inference)
    elif inference.intent == 'sayTime':
        say(time.strftime('%H:%M'))
        print(inference)

    setColor(*colours[ledsColour])

def play(sound):
    os.system('play sfx/' + sound)

def say(text):
    hash = hashlib.md5(text.encode()).hexdigest()
    file = 'speech-cache/{}.wav'.format(hash)
    cmd = 'play {}'.format(file)
    if not os.path.isfile(file):
        cmd = 'pico2wave -w {} "{}" && {}'.format(file, text, cmd)
    os.system(cmd)

def joke():
    j = requests.get('https://v2.jokeapi.dev/joke/Any?format=txt').text
    print(j)
    say(j)

handle = Picovoice(
        keyword_path=keyword_path,
        wake_word_callback=wake_word_callback,
        context_path=context_path,
        inference_callback=inference_callback)

pa = pyaudio.PyAudio()

audio_stream = pa.open(
                rate=16000,
                channels=1,
                format=pyaudio.paInt16,
                input=True,
                frames_per_buffer=512,
                input_device_index=6
                )

while True:
    pcm = audio_stream.read(512, exception_on_overflow = False)
    pcm = struct.unpack_from("h" * 512, pcm)

    handle.process(pcm)


#finally:
#    if porcupine is not None:
#        porcupine.delete()
#
#    if audio_stream is not None:
#        audio_stream.close()
#
#    if pa is not None:
#            pa.terminate()
