###########################################################################################
#
# FeynmAGI V0.1
# Imed MAGROUNE
# 2024-06
#
#########################################################################################
from flask_socketio import SocketIO

socketio = None

def init_socketio(app):
    return SocketIO(app)
    
def set_socketio(sio):
    global socketio
    socketio = sio

def get_socketio():
    return socketio

