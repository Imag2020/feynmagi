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

def parse_agent(response):
    print("[DEBUG] parse agent ----- parsing -----")
    print(response)
    print("[DEBUG] parse agent  end ----- parsing -----")
    
    command_pattern = re.compile(r"""
    ###\s*AGENT\s*###\s*      # Match the COMMAND header
    \s*(.*?)\s*          # Match the command name after 'Agent'
    (?:Args?|Arguments?)\s*:?\s*(.*)  # Match 'Arg', 'Args', 'Arguments' followed by optional ':' and then capture the rest
    """, re.VERBOSE | re.IGNORECASE)
    
    match = command_pattern.search(response)
    
    if match:
        print("[DEBUG] matched")
        command_name = match.group(1).strip() if match.group(1) else None
        arguments = match.group(2).strip() if match.group(2) else None
        print("[DEBUG] found ....", command_name, arguments)
        command_name = command_name.lower()
        if "web" in command_name:
            command_name = "web"
        elif "developer" in command_name:
            command_name = "developer"
        elif "interpreter" in command_name:
            command_name = "interpreter"
        elif "rag" in command_name:
            command_name = "rag"
        elif "memory" in command_name:
            command_name = "memory"
        elif "creator" in command_name:
            command_name = "agent"
        return command_name, arguments
    
    return None, None

def parse_command(response):
    print("[DEBUG] parse command ----- parsing -----")
    print(response)
    print("[DEBUG] parse command end ----- parsing -----")
    
    command_pattern = re.compile(r"""
    ###\s*COMMAND\s*###\s*      # Match the COMMAND header
    Command\s*:\s*(.*?)\s*      # Match the command name after 'Command:'
    Args\s*:\s*(.*)             # Match 'Args:' followed by the arguments
    """, re.VERBOSE | re.IGNORECASE)
    
    match = command_pattern.search(response)
    
    if match:
        print("[DEBUG] matched")
        command_name = match.group(1).strip().lower() if match.group(1) else None
        arguments_str = match.group(2).strip() if match.group(2) else None
        
        print("[DEBUG] found ....", command_name, arguments_str)
        
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
        # Parse the arguments into a dictionary
        arguments = {}
        if arguments_str:
            arguments_list = re.split(r'\s*[;,]\s*', arguments_str)  # Split by ',' or ';' with optional whitespace
            for arg in arguments_list:
                if ':' in arg:
                    key, value = arg.split(':', maxsplit=1)  # Split by ':' with optional whitespace
                    key = key.strip().strip('"')
                    value = value.strip().strip('"')
                    arguments[key.lower()] = value            
        return command_name, arguments
    
    return None, None

def current_datetime_string():
    now = datetime.now()
    current_time_str = now.strftime("%Y-%m-%d %H:%M:%S")
    return current_time_str

def get_context(user_input="",tag=None):
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

    if command_name in ['default','web','memory','rag','interpreter']:
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
        logger.send_text(f"<BR>______{thread_id} 1  _________{cfg.actual_agent} Agent Thinking ________________<BR>")
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
                cfg.actual_agent="default"
                break
            else:
                print("[DEBUG] no agent name provided")
                logger.write_log("[DEBUG] no agent name provided")
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
                    break 
                logger.write_log(f" {thread_id} ret_cmd=cmd.execute_command {command_name} artgs={arguments} ")
                ret_cmd=cmd.execute_command(command_name, arguments)
                
                if ret_cmd is not None:
                    result = f" {thread_id} Command {command_name} returned : " + ret_cmd
                    logger.write_log(f"resule = {result} append and break ")
                    print(f" ret_cmd = {result} maj actual_message and continue")
                    actual_message = result
                    continue
            else:
                logger.write_log(" break ")
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

        