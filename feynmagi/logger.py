###########################################################################################
#
# FeynmAGI V0.1
# Imed MAGROUNE
# 2024-06
#
#########################################################################################
import logging

from .socketio_instance import init_socketio, get_socketio
import pkg_resources


def typewriter_log(message, level='info'):
    socketio = get_socketio()
    socketio.emit('typewriter_log', {'message': message})


def send_text(message):
    socketio = get_socketio()
    socketio.emit('response_token', {'token': message})

def say_text(message):
    socketio = get_socketio()
    socketio.emit('say_text', {'message': message})
    
def send_textfile(message):
    socketio = get_socketio()
    socketio.emit('display_file', {'message': message})
    
def send_popup(message):
    socketio = get_socketio()
    socketio.emit('popup', {'message': message})

def write_log(message):
    dir_path=pkg_resources.resource_filename('feynmagi', 'data/')
    with open(dir_path+"dials.txt", "a",encoding='utf-8') as myfile:
        myfile.write(message)
        myfile.write("\n")
        



