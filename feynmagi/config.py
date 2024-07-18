###########################################################################################
#
# FeynmAGI V0.1
# Imed MAGROUNE
# 2024-06
#
#########################################################################################
import threading
from . import logger
from . import helper
import abc
import dataclasses
import orjson
from typing import Any, List, Optional
import numpy as np
import os
from .socketio_instance import get_socketio
from . import vectorsdb as vbdb
from threading import Lock
import os
import json

from .sessions import SessionHistory
import pkg_resources


full_message_history = []
session_message_history = []
agent_message_history = []
actual_agent="default"
actual_session_id=0
actual_model="phi3:latest"
actual_engine = "llm"
llm_connect="local"



class Singleton(type):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]

class Config(metaclass=Singleton):
    def __init__(self):
        self.config_file = pkg_resources.resource_filename('feynmagi', 'data/config.txt')
        self.json_str = 'response'
        self.debug_mode = False
        self.continuous_mode = True
        self.speak_mode = True
        self.openaikey = ""
        self.groqkey = ""
        self.openai_organisation = ""
        self.openai_project = ""
        self.api_endpoint = "http://localhost:11434/api/generate"
        self.api_chat_endpoint = "http://localhost:11434/api/chat"
        self.embedding_endpoint = "http://localhost:11434/api/embeddings"
        self.openai_model = "gpt4o"
        self.groq_model = "llama3-70B-8192"
        self.load_config()

    def load_config(self):
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r', encoding='utf-8') as file:
                config_data = json.load(file)
                self.json_str = config_data.get('json_str', self.json_str)
                self.debug_mode = config_data.get('debug_mode', self.debug_mode)
                self.continuous_mode = config_data.get('continuous_mode', self.continuous_mode)
                self.speak_mode = config_data.get('speak_mode', self.speak_mode)
                self.openaikey = config_data.get('openaikey', self.openaikey)
                self.groqkey = config_data.get('groqkey', self.groqkey)
                self.openai_organisation = config_data.get('openai_organisation', self.openai_organisation)
                self.openai_project = config_data.get('openai_project', self.openai_project)
                self.api_endpoint = config_data.get('api_endpoint', self.api_endpoint)
                self.api_chat_endpoint = config_data.get('api_chat_endpoint', self.api_chat_endpoint)
                self.embedding_endpoint = config_data.get('embedding_endpoint', self.embedding_endpoint)
                self.openai_model = config_data.get('openai_model', self.openai_model)
                self.groq_model = config_data.get('groq_model', self.groq_model)
        else:
            self.save_config()

    def save_config(self):
        config_data = {
            'json_str': self.json_str,
            'debug_mode': self.debug_mode,
            'continuous_mode': self.continuous_mode,
            'speak_mode': self.speak_mode,
            'openaikey': self.openaikey,
            'groqkey': self.groqkey,
            'openai_organisation': self.openai_organisation,
            'openai_project': self.openai_project,
            'api_endpoint': self.api_endpoint,
            'api_chat_endpoint': self.api_chat_endpoint,
            'embedding_endpoint': self.embedding_endpoint,
            'openai_model': self.openai_model,
            'groq_model': self.groq_model,
        }
        with open(self.config_file, 'w', encoding='utf-8') as file:
            json.dump(config_data, file, indent=4)

    def save_config(self):
        """Save the configuration to a file."""
        config_data = {
            'json_str': self.json_str,
            'debug_mode': self.debug_mode,
            'continuous_mode': self.continuous_mode,
            'speak_mode': self.speak_mode,
            'openaikey': self.openaikey,
            'groqkey': self.groqkey,
            'openai_organisation': self.openai_organisation,
            'openai_project': self.openai_project,
            'api_endpoint': self.api_endpoint,
            'api_chat_endpoint': self.api_chat_endpoint,
            'embedding_endpoint': self.embedding_endpoint,
            'openai_model': self.openai_model,
            'groq_model': self.groq_model
        }
        with open(self.config_file, 'w', encoding='utf-8') as file:
            json.dump(config_data, file)

    def set_continuous_mode(self, value: bool):
        """Set the continuous mode value."""
        self.continuous_mode = value
        self.save_config()

    def set_speak_mode(self, value: bool):
        """Set the speak mode value."""
        self.speak_mode = value
        self.save_config()

    def set_openaikey(self, value: str):
        """Set the openai key value."""
        self.openaikey = value
        self.save_config()

    def set_groqkey(self, value: str):
        """Set the groq key value."""
        self.groqkey = value
        self.save_config()

    def set_debug_mode(self, value: bool):
        """Set the debug mode value."""
        self.debug_mode = value
        self.save_config()

    def set_connect_llm(self, value: str):
        """Set the connect_llm value."""
        self.connect_llm = value
        self.save_config()

    def set_openai_organisation(self, value: str):
        """Set the openai organisation value."""
        self.openai_organisation = value
        self.save_config()

    def set_openai_project(self, value: str):
        """Set the openai project value."""
        self.openai_project = value
        self.save_config()

    def set_api_endpoint(self, value: str):
        """Set the API endpoint value."""
        self.api_endpoint = value
        self.save_config()

    def set_api_chat_endpoint(self, value: str):
        """Set the API chat endpoint value."""
        self.api_chat_endpoint = value
        self.save_config()

    def set_embedding_endpoint(self, value: str):
        """Set the embedding endpoint value."""
        self.embedding_endpoint = value
        self.save_config()

    def set_openai_mode(self, value: str):
        """Set the openai mode value."""
        self.openai_mode = value
        self.save_config()

    def set_groq_model(self, value: str):
        """Set the groq model value."""
        self.groq_model = value
        self.save_config()


class SysInfo(metaclass=Singleton):
    """
    Information class to store the state of System Usage
    """
    #global localmem
    def __init__(self):
        """Initialize the Config class"""
        self.nb_local_vectors = -1
        self.status='Waiting'
        # self.chroma_longmem='./longmem/'
        # self.memory_backend = os.getenv("MEMORY_BACKEND", 'local')
        #self.smart_token_limit = int(os.getenv("SMART_TOKEN_LIMIT", 8000))

    def set_nb_local_vectors(self, value: int):
        """Set the continuous mode value."""
        self.nb_local_vectors = value
        # update display
        self.show_inf()

    def set_status(self, value: str):
        """Set the continuous mode value."""
        self.status = value
        # update display
        self.show_inf()
        
    def show_inf(self):
        """ Display system Info on Console """
        # formatge output
        socketio = get_socketio() 
        out_info=f"<div>{self.status}</div><div>V : {self.nb_local_vectors}</div>"
        if socketio is not None:
            socketio.emit('update_system_info', {'system_info': out_info})     
        else:
            logger.debug("SocketIo None !!")

logging=logger.logging
logger = logging.getLogger()
logging.getLogger('watchdog.observers.inotify_buffer').setLevel(logging.INFO)
dir_path=pkg_resources.resource_filename('feynmagi', 'data/')
fhandler = logging.FileHandler(filename=dir_path+'mylog.log', mode='a')
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fhandler.setFormatter(formatter)
logger.addHandler(fhandler)

logger.setLevel(logging.INFO)
stop_event = threading.Event()
yes_event = threading.Event()
no_event = threading.Event()
feed_event = threading.Event()
event_data = {}

cfg = Config()
inf = SysInfo()
session_history = SessionHistory()
vdb = vbdb.VectorDB()
dir_path=pkg_resources.resource_filename('feynmagi', 'data/')
ragdb = vbdb. RagVectorDB(dir_path+"ragmem4")

# Création de locks pour chaque variable partagée
cfg_lock = Lock()
session_history_lock = Lock()
session_message_history_lock = Lock()
agent_message_history_lock = Lock()


# vdb = vectorsdb.LMVectorDB("mem01")

