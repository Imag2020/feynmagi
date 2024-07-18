###########################################################################################
#
# FeynmAGI V0.1
# Imed MAGROUNE
# 2024-06
#
#########################################################################################
import threading
import re
from datetime import datetime
from .socketio_instance import get_socketio
from . import helper
from . import logger
from . import commands as cmd

from . import llmsapis 
from . import config as cfg
from .tasks import add_task, thread_manager

import pkg_resources
import json

# Protéger les variables globales avec des verrous
lock = threading.Lock()

actual_max_tokens = 8000

def get_global_variable(var_name):
    with lock:
        value = globals().get(var_name)
        print(f"[DEBUG] Getting global variable {var_name}: {value}")
        return value

def set_global_variable(var_name, value):
    with lock:
        globals()[var_name] = value
        print(f"[DEBUG] Setting global variable {var_name} to: {value}")

def extract_command_and_arguments(text):
    """
    Extrait le nom de l'agent ou de la commande après '### AGENT ###' ou '### COMMAND ###',
    et convertit la ligne suivante d'arguments en dictionnaire, ou la traite comme une simple description
    si ce n'est pas un format clé:valeur.

    :param text: Chaîne de caractères contenant le texte à analyser
    :return: Tuple (name, arguments_dict)
    """
    lines = text.splitlines()
    found = False
    name = None
    arguments = {}
    json_data_accumulated = ""
    
    for line in lines:
        if '### AGENT ###' in line or '### COMMAND ###' in line:
            found = True
            continue
        if found:
            if name is None:
                name = line.strip()
                continue
            line = line.strip()
            json_data_accumulated += line
            if json_data_accumulated.startswith('{') and '}' in json_data_accumulated:
                try:
                    arguments = json.loads(json_data_accumulated)
                    break
                except json.JSONDecodeError:
                    continue  # Continue accumulating if JSON is not complete
            else:
                # Handling key:value pairs directly
                args_parts = re.findall(r'(\w+)\s*:\s*("[^"]*"|\'[^\']*\'|\S+)', line)
                if args_parts:
                    for key, val in args_parts:
                        val = val.strip().strip('\'"')
                        arguments[key.strip()] = val
                if not args_parts:  # If no key:value pairs were found, store as query
                    arguments['query'] = line
                break
    print("")
    print("")
    print("____________________________________________________________________________________")
    print(f"__________ returning {name} / {arguments} ___")
    print("")
    print("")
    print("____________________________________________________________________________________")
    # return name, json.dumps(arguments)
    return name, arguments

def parse_agent(response):
    
    command_name,arguments = extract_command_and_arguments(response)
    if command_name:
        
        command_name = command_name.lower()
        if "web" in command_name:
            command_name = "web"
        elif "developer" in command_name:
            command_name = "developer"
        elif "interpreter" in command_name:
            command_name = "interpreter"
        elif "project" in command_name:
            command_name = "project"
        elif "memory" in command_name:
            command_name = "memory"
        elif "manager" in command_name:
            command_name = "project"
        return command_name, arguments
    
    return None, None

def parse_command(response):
    
    command_name,arguments = extract_command_and_arguments(response)
    if command_name:
        if "google" in command_name:
            command_name = "google"
        elif "calc" in command_name:
            command_name = "calculate"
        elif "write" in command_name:
            command_name = "write-to-file"
        elif "read" in command_name:
            command_name = "read-file"
        elif "append" in command_name:
            command_name = "append-to-file"
        elif "display" in command_name:
            command_name = "display-file"
        return command_name, arguments
    
    return None, None

def current_datetime_string():
    now = datetime.now()
    current_time_str = now.strftime("%Y-%m-%d %H:%M:%S")
    return current_time_str

def get_context(user_input="",tag=None):
    if isinstance(user_input, dict):
        user_input='\n'.join(user_input)
    if tag is None:
        return f"Please note that current date and time is : {current_datetime_string()}"
    else:
        cn = cfg.ragdb.find_similar_d(user_input, n=1, tag=tag, min_similarity=0.4)
        if cn == []:
            return "No context Found\n"
        return cn[0][0]
        

def update_session_history(m_history, new_message, max_tokens):
    m_history.append(new_message)
    total_tokens = sum(helper.count_tokens(msg['content']) for msg in m_history)
    while total_tokens > max_tokens:
        total_tokens -= helper.count_tokens(m_history.pop(0)['content'])

def check_command_name(command_name):

    if command_name in ['default','web','memory','project','interpreter','manager']:
        return command_name
    return "na"

def manage_prompt_length(dialogues, max_tokens, tokens_count):
    """
    Supprime les dialogues les plus anciens de la liste jusqu'à ce que le nombre total de tokens soit inférieur à max_tokens.

    :param dialogues: Liste de dictionnaires contenant les dialogues. Chaque dictionnaire a une structure comme {'role': 'user', 'content': 'text'}.
    :param max_tokens: Le nombre maximum de tokens autorisés.
    :param tokens_count: Fonction qui calcule le nombre de tokens d'une chaîne de caractères.
    :return: La liste mise à jour des dialogues.
    """
    # Calcul du nombre total de tokens dans la liste actuelle
    total_tokens = sum(tokens_count(dialogue['content']) for dialogue in dialogues)

    # Suppression des dialogues les plus anciens si le total de tokens dépasse max_tokens
    while total_tokens > max_tokens and dialogues:
        # Suppression du dialogue le plus ancien
        removed_tokens = tokens_count(dialogues.pop(0)['content'])
        # Mise à jour du total de tokens
        total_tokens -= removed_tokens

    return dialogues
    
    
def start_autosession(user_input,tag=None):
    if isinstance(user_input, dict):
        user_input=json.dumps(user_input)
    print(f" ___________  start auto session user_input = {user_input} _")
    logger.write_log(f"[DEBUG] Starting autosession...{cfg.session_message_history} and {cfg.agent_message_history} ")  # Log de diagnostic
    socketio = get_socketio()
    logger.write_log(f"[DEBUG] SocketIO instance: {socketio}")  # Log de diagnostic
    context = get_context(user_input,tag)
    print(f"-----------____{tag}____________ context=",context)
    print("cfg.ragdb.get_stats() ", cfg.ragdb.get_stats())
    thread_id = threading.get_ident()
    # m_history = []

    if cfg.actual_agent == "default":
        m_history = cfg.session_message_history
        logger.write_log("m_history = cfg.session_message_history")
        if  cfg.session_message_history == [] or cfg.session_message_history is None:
            logger.write_log("not session_message_history")
            file_path=pkg_resources.resource_filename('feynmagi', 'prompts/system_default.txt')
            if tag is None:
                file_path=pkg_resources.resource_filename('feynmagi', 'prompts/system_default.txt')
                system_prompt = open(file_path, 'r', encoding='utf-8').read()
                actual_message = system_prompt + context + '\nuser input : ' + user_input
            else:
                file_path=pkg_resources.resource_filename('feynmagi', 'prompts/system_rag.txt')
                system_prompt = open(file_path, 'r', encoding='utf-8').read()
                # got context here 
                actual_message = system_prompt.format(user_input=user_input,context=context) 
                
            
            
        else:
            logger.write_log(f" 1 actual_message = {user_input}")
            actual_message = user_input
    else:
        m_history = cfg.agent_message_history
        logger.write_log("m_history = cfg.agent_message_history")
        if  cfg.agent_message_history == [] or cfg.agent_message_history is None:
            logger.write_log("not agent_message_history")
            file_path=pkg_resources.resource_filename('feynmagi', f'prompts/system_{cfg.actual_agent}.txt')
            system_prompt = open(file_path, 'r', encoding='utf-8').read()
            actual_message = system_prompt + context + '\nYour mission : ' + user_input + '\nNow help me please'
            
        else:
            logger.write_log(f" 2 actual_message = {user_input}")
            actual_message = user_input

    while True:
        logger.send_text(f"<BR>_______________{cfg.actual_agent} Agent Thinking ________________<BR>")
        logger.write_log(f"<BR>_____{thread_id} 2   __________{cfg.actual_agent} Agent Thinking ________________<BR>")
        print(f"<BR>____________{cfg.actual_agent} Agent Thinking ________________<BR>")
        
        
        

        logger.write_log(f"000 =================================={cfg.actual_agent} =======================================================================")
        logger.write_log(actual_message)
        update_session_history(m_history, {"role": "user", "content": actual_message}, actual_max_tokens)
        logger.write_log(f"111 ========================================={cfg.actual_agent} ================================================================")

        print(f"_______{thread_id} _________start pinting m_history")
        for i, h in enumerate(m_history):
            print(f"[DEBUG]  ==== ________{thread_id} _______________ i={i}")
            logger.write_log(f"[DEBUG] printng ==== _________{thread_id} ______________ i={i}")
            print(h)
            logger.write_log(str(h))
            print(f"[DEBUG] ==== __________{thread_id} _____________ fin i={i}")
            logger.write_log(f"[DEBUG] end printing ==== fin _____{thread_id} __________________ i={i}")
        
        print(f"________{thread_id} ________ end pinting m_history") 
        assistant_reply = ""
        for response_text in llmsapis.llmchatgenerator(m_history, temperature=0., stream=True, raw=False):
            assistant_reply += response_text
            socketio.emit('response_token', {'token': response_text})
        logger.write_log(assistant_reply)
        logger.write_log("222 end assistant_reply =========================================================================================================")

        if not assistant_reply:
            logger.say_text(f"Auto LLM assistant returned None ... breaking")
            logger.write_log("222 Auto LLM assistant returned None ... break   ===========")
            break

        new_message = {
            "role": "assistant",
            "content": assistant_reply
        }
        #cfg.session_message_history.append(new_message)
        update_session_history(m_history, new_message, actual_max_tokens)

        if cfg.actual_agent == "default":
            command_name, arguments = parse_agent(assistant_reply)
        else:
            command_name, arguments = parse_command(assistant_reply)
            

        if cfg.actual_agent == "default":
            logger.write_log(" cfg.actual_agent = default")
            print(f"  {thread_id} cfg.actual_agent = default")
            if command_name:
                print(f"_==========   >>>>>>> [DEBUG] {thread_id} calling agent ....{command_name}.{arguments}")
                logger.write_log(f" {thread_id} [DEBUG] calling agent ....{command_name}.{arguments}")
                command_name=check_command_name(command_name)
                if command_name=="na":
                    result = f"Agent {command_name} does not exit !  " 
                    print(result)
                    logger.write_log(f" result = {result}")
                    print(f"  {thread_id} result = {result}")
                    break
                    
                cfg.actual_agent= command_name
                thread = threaded_autosession(arguments)  # Relancer start_autosession avec les arguments
                if thread:
                    thread.join()  # Wait for the autosession thread to complete
                    print(f"[DEBUG] {thread_id} Autosession thread has completed")
                    socketio.emit('end_message', {'token': '<br>'})
                cfg.actual_agent="default"
                break
            else:
                print("[DEBUG] no agent name provided")
                logger.write_log("[DEBUG] no agent name provided")
                socketio.emit('end_message', {'token': '<br>'})
                break
        else:
            logger.write_log(" cfg.actual_agent ! = default")
            print(f"  {thread_id} cfg.actual_agent ! = default")
            if command_name:
                print("[DEBUG] calling command ....")
                logger.write_log("[DEBUG] calling command ....")
                if command_name == "exit":
                    logger.say_text(f"{cfg.actual_agent} exiting to default agent")
                    print(f" {thread_id} __ 555 __ {cfg.actual_agent} exiting to default agent by break ")
                    logger.write_log(f" ---------------   444 ")
                    connect_message = { 'role' : 'user', 'content' : f" {cfg.actual_agent} exited with context : {arguments}"}
                    update_session_history(cfg.session_message_history, connect_message, actual_max_tokens)
                    cfg.agent_message_history=[]
                    cfg.actual_agent= "default"
                    socketio.emit('end_message', {'token': '<br>'})
                    break 
                logger.write_log(f" {thread_id} ret_cmd=cmd.execute_command {command_name} artgs={arguments} ")
                ret_cmd=cmd.execute_command(command_name, arguments)
                
                if ret_cmd is not None:
                    result = f"Command {command_name} returned : " + ret_cmd
                    logger.write_log(f"resule = {result} append and break ")
                    print(f" ret_cmd = {result} maj actual_message and continue")
                    actual_message = result
                    continue
            else:
                logger.write_log(" break ")
                socketio.emit('end_message', {'token': '<br>'})
                break

'''

def threaded_autosession(message,tag=None):
    # Démarrer un thread pour la session automatique
    thread_id = threading.get_ident() 
    thread = threading.Thread(target=start_autosession, args=(message,tag))
    thread.start()
    print(f"[DEBUG] threaded_autosession {thread_id} == > Thread for autosession started")
'''

def threaded_autosession(message, tag=None):
    # Démarrer un thread pour la session automatique
    thread = threading.Thread(target=start_autosession, args=(message, tag))
    thread.start()
    thread_id = thread.ident
    print(f"[DEBUG] threaded_autosession {thread_id} == > Thread for autosession started")
    return thread

        