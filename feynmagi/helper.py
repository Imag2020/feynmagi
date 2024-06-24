###########################################################################################
#
# FeynmAGI V0.1
# Imed MAGROUNE
# 2024-06
#
#########################################################################################
from IPython.display import display, HTML
from typing import Any, List, Optional
import numpy as np
import os
import abc
import dataclasses
import orjson
from jinja2 import Template

import re
import subprocess
import requests 
import json
from datetime import datetime

from . import config as cfg

def get_timestamp():
    return datetime.now().strftime("%Y%m%d%H%M%S")
    
def delete_after_substring(s, substring):
    index = s.find(substring)
    if index != -1:
        return s[:index]
    return s
    
def convert_go_template_to_jinja2(template_str):
    # Convert Go template syntax to Jinja2 syntax
    template_str = re.sub(r'{{\s*if\s*\.([^\s]+)\s*}}', r'{% if \1 %}', template_str)
    template_str = re.sub(r'{{\s*end\s*}}', r'{% endif %}', template_str)
    template_str = re.sub(r'{{\s*\.\s*([^\s]+)\s*}}', r'{{ \1 }}', template_str)
    return template_str

def format_prompt(message=None,system=None, response=None, model=None):
    #formatting prompt
    if model:
        template_str=get_model_info(model)['template']
    else:
        template_str=get_model_info(cfg.actual_model)['template']
    template_str=convert_go_template_to_jinja2(template_str)
    if response is None:
        template_str = delete_after_substring(template_str, "{{ Response }}")
    template = Template(template_str)
    data = {
        'System': system if system is not None else "",
        'Prompt': message if message is not None else "",
        'Response': response if response is not None else ""
    }

    
     
    ret = template.render(data)

    if response is not None and "{{ Response }}" not in template_str:
        ret+="\n"+response
        
    print( ".........................temp=",template_str, "model",model, "default", cfg.actual_model, "................" )
    return ret # template.substitute(data)
    
def count_tokens(prompt):
    nb_word =count_words(prompt)
    nb_tokens=int(nb_word/0.75)
    return nb_tokens
    
def is_valid_int(value):
    try:
        int(value)
        return True
    except ValueError:
        return False

def remove_suffix_if_present(original_string, suffix):
    if original_string.endswith(suffix):
        # Supprime le suffixe en découpant la chaîne jusqu'à la longueur du suffixe
        return original_string[:-len(suffix)]
    return original_string


def count_words(text):
    if not text:
        return 0  # Return 0 if the text is empty or None

    count = 0
    in_word = False

    for char in text:
        if char.isalpha():
            if not in_word:
                count += 1  # Start of a new word
                in_word = True
        else:
            in_word = False  # End of a word

    return count


def check_process(process_name):
    # Exécuter la commande avec un pipeline, en utilisant shell=True pour interpréter la pipeline
    command = f"ps -ef | grep '{process_name}' | grep -v grep"
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    # Obtenir la sortie standard et d'erreur
    stdout, stderr = process.communicate()
    
    # Convertir la sortie standard en string si nécessaire (Python 3)
    output = stdout.decode('utf-8') if hasattr(stdout, 'decode') else stdout
    
    # Vérifier si le processus est trouvé
    if process_name in output:
        return True
    else:
        return False

def replace_newlines_in_quotes(text):
    # Définition du motif pour détecter les chaînes entre guillemets
    pattern = r'"(.*?)"'
    
    # Fonction pour remplacer les retours à la ligne par \n à l'intérieur des chaînes entre guillemets
    def replace_newlines(match):
        # Remplacement des retours à la ligne par \n dans la chaîne détectée
        return match.group(0).replace('\n', '\\n')
    
    # Utilisation de re.sub avec la fonction de remplacement sur le texte complet
    return re.sub(pattern, replace_newlines, text, flags=re.DOTALL)

# Define a function to format text with color using CSS
def color_text(text, color):
    return f'<span style="color: {color};">{text}</span>'

def color_text(text, color):
    # Replace newline characters with <br> tags
    text_with_line_breaks = text.replace('\n', '<br>')
    return f'<span style="color: {color};">{text_with_line_breaks}</span>'

def printc(texte,color="orange"):
    colored_text = color_text(texte,color)
    display(HTML(colored_text))

def nettoyer_chaine(chaine):
    # Remplacer les espaces et tabulations multiples par un seul espace
    chaine_propre = re.sub(r'\s+', ' ', chaine)
    return chaine_propre
class SafeDict(dict):
    def __missing__(self, key):
        return f"{{{key}}}"  # Retourne le nom de la clé entre accolades ou une autre valeur par défaut

class Singleton(abc.ABCMeta, type):
    """
    Singleton metaclass for ensuring only one instance of a class.
    """

    _instances = {}

    def __call__(cls, *args, **kwargs):
        """Call method for the singleton metaclass."""
        if cls not in cls._instances:
            cls._instances[cls] = super(
                Singleton, cls).__call__(
                *args, **kwargs)
        return cls._instances[cls]


class AbstractSingleton(abc.ABC, metaclass=Singleton):
    pass

class MemoryProviderSingleton(AbstractSingleton):
    @abc.abstractmethod
    def add(self, data):
        pass

    @abc.abstractmethod
    def get(self, data):
        pass

    @abc.abstractmethod
    def clear(self):
        pass

    @abc.abstractmethod
    def get_relevant(self, data, num_relevant=5):
        pass

    @abc.abstractmethod
    def get_stats(self):
        pass
'''
@dataclasses.dataclass
class CacheContent:
    texts: List[str] = dataclasses.field(default_factory=list)
    embeddings: np.ndarray = dataclasses.field(
        default_factory=create_default_embeddings
    )
'''

def check_sys_info():

    output=""
    return output
    
        

def extract_code_from_markdown(markdown_text):
    # Use a regular expression to find the content between the code block delimiters
    code_match = re.search(r"```(?:\w+)?\n(.*?)```", markdown_text, re.DOTALL)
    if code_match:
        return code_match.group(1).strip()
    else:
        return None

def get_tags(url):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Check if the request was successful
        data = response.json()  # Parse the JSON response
        return data
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return None

def get_models():
    url = "http://localhost:11434/api/tags"
    return get_tags(url)

def post_show(url, data):
    headers = {'Content-Type': 'application/json'}
    try:
        response = requests.post(url, data=json.dumps(data), headers=headers)
        response.raise_for_status()  # Check if the request was successful
        response_data = response.json()  # Parse the JSON response
        return response_data
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return None
def get_model_info(model):
    url = "http://localhost:11434/api/show"
    data = {
        "name": model
    }

    response_data = post_show(url, data)
    return response_data
