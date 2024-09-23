import threading
import re
from datetime import datetime
from .socketio_instance import get_socketio
from . import helper
from . import logger
from . import commands as cmd

from . import llmsapis 
from . import config as cfg
from .tasks import add_task, thread_manager, start_autosession_task

import pkg_resources
import json
from .socketio_instance import get_socketio
from .agents import AgentManager
from .tools import tools
from . import commands as cmd
from . import websearch as webs
from . import agentdev as dev
from .mailing import send_email
import pkg_resources
from .agents import AgentManager

from .mcts import mcts_action

agent_manager = AgentManager()

class PAgent:
    def __init__(self, system: str = "") -> None:
        self.system = system
        self.messages: list = []
        if self.system:
            self.messages.append({"role": "system", "content": system})

    def __call__(self, message="",mode="default"):
        if message:
            self.messages.append({"role": "user", "content": message})
        result = self.execute(mode)
        self.messages.append({"role": "assistant", "content": result})
        return result

    def execute(self,mode):
        '''
        print("")
        print("_________________________________ start messages at turn _________________________________________")
        for m in self.messages:
            print("")
            print(f"__--__{m}__--__")
            print("")
        print("_________________________________ end messages at turn _________________________________________")
        print("")
        '''
        if mode =="default":
            ret="" # llm(json.dumps(self.messages))
            for response_text in llmsapis.llmchatgenerator(self.messages, temperature=0., stream=True, raw=False):
                ret += response_text
        else:
            ret = mcts_action(self.messages)
            print(f"______ mcts return : {repr(ret)}______")
        return ret.replace("\\n","\n")

import re


def extraire_param(texte):
    # Utilisation d'une expression régulière pour chercher le motif "chaine 1" : "chaine 2"
    match = re.match(r'^"([^"]+)"\s*:\s*"([^"]+)"$', texte)
    if match:
        # Si le motif est trouvé, retourner 'chaine 2'
        return match.group(2)
    else:
        # Sinon, retourner le texte original
        return texte

def parse_arguments(text):
    params = {}
    key = ""
    value = ""
    mode = "key"
    i = 0
    while i < len(text):
        if mode == "key":
            if text[i] == '"':
                start = i + 1
                i += 1
                while i < len(text) and (text[i] != '"' or (text[i-1] == '\\' and text[i] == '"')):
                    i += 1
                key = text[start:i]
                i += 1  # Skip closing quote
                mode = "colon"
            else:
                i += 1
        elif mode == "colon":
            if text[i] == ':':
                mode = "value"
            i += 1
        elif mode == "value":
            if text[i] == '"':
                start = i + 1
                i += 1
                while i < len(text):
                    if text[i] == '"' and text[i-1] != '\\':
                        break
                    i += 1
                value = text[start:i]
                i += 1  # Skip closing quote if it exists
                params[key] = value
                key, value = "", ""
                mode = "comma"
            else:
                i += 1
        elif mode == "comma":
            if text[i] == ',':
                mode = "key"
            i += 1
    return params
def play(agent_name, agent_system, agent_prompt, max_iterations=50, input_text = None,mode="default"):
    global tools
    socketio = get_socketio()
    agent_manager = AgentManager()
    aagent = agent_manager.find_agent_by_name(agent_name)
    if aagent and aagent.tools:
        tools_str = "\nYour available actions are:\n\n"
        for tool in aagent.tools:
            if tool in tools:
                tools_str += f"{tools[tool]}\n\n"
        agent_system = agent_system.format(tools=tools_str)
        print(f"__________ final system={agent_system} ______")
    
    agent = PAgent(system=agent_system)
    next_prompt = agent_prompt
    if input_text is not None and input_text != "":
        if "{input}" in next_prompt:
            next_prompt=next_prompt.format(input=input_text)
            
    socketio.emit('output_agent', {"token": next_prompt})
    i = 0
    
    while i < max_iterations:
        socketio.emit('output_agent', {"token": f" iteration  : ____________ {i} __________________"})
        i += 1
        result = agent(next_prompt,mode)
        print(result)
        socketio.emit('output_agent', {"token": f"{result}"})

        if "PAUSE" in result and "Action" in result:
            actions = re.findall(r"\*?\*?Action:?\*?\*?\s*?\s*([a-z_]+)\s*:\s*(.+)", result, re.IGNORECASE)
            if not actions:
                if "Action: None" in result:
                    socketio.emit('output_agent', {"token": "Exit for Action Now"})
                    break
                next_prompt = "Observation: Last action syntax is wrong, please choose action only from tools list above"
                socketio.emit('output_agent', {"token": next_prompt})
                continue
            
            chosen_tool, args = actions[0][0], actions[0][1]
            args_list = parse_arguments(args)
            print(f"tool=___{chosen_tool}___")
            print(f"args=___{args_list}___")
            if chosen_tool in aagent.tools:
                #args_list = [arg.replace('\'', '\\\'') for arg in args_list]  # escape single quotes
                try:
                    result_tool = eval(f"{chosen_tool}(**args_list)")
                    next_prompt = f"Observation: {result_tool}"
                except Exception as e:
                    result_tool = str(e)
                    next_prompt = f"Observation: {result_tool}"
            else:
                if "none" in chosen_tool.lower() or "exit" in chosen_tool.lower()  in chosen_tool is None:
                    break
                next_prompt = f"Observation: {chosen_tool} tool not found"
                
            print(next_prompt)
            socketio.emit('output_agent', {"token": next_prompt})
        else:
            next_prompt = "Observation: Last output syntax is wrong, please check Action from tools list above then PAUSE"
            socketio.emit('output_agent', {"token": next_prompt})
            

        if "Answer" in result:
            break
    print(f"End Agent result={result}")
    socketio.emit('output_agent', {"token": "<br><b><span style='color:blue'>End Agent</span></b><br>"})
    socketio.emit('output_agent', {"token": result})





def google(query):
    return webs.search(query)

def weblinks(query):
    return webs.weblinks(query)

def scrap(url):
    return webs.scrap(url)

def display_file(file_path):
    return cmd.display_file(file_path)

def read_file(file_path):
    return cmd.read_file(file_path)

def  write_to_file(file_path, text):
    return cmd.write_to_file(file_path, text)

def append_to_file(file_path, text):
    return cmd.append_to_file(file_path, text)

def dev_code(objective,language,framework,file_name):
    return dev.dev_code(objective,language,framework,file_name)

def exec_code(environment,file_name,input):
    return dev.exec_code_in_conda_env(environment,file_name,input)

def email(to, subject, body, attachment=None):
   
    if attachment is not None and "none" not in attachment.lower():
        return send_email(to, subject, body, attachment)
    else:
        return send_email(to, subject, body)


def calculate(operation: str) -> float:
    return eval(operation)


def call_agent(agent, context):
    if agent is None or agent ==  "":
        return "Error, agent name not valid"
    if context is None or context =="":
        return "Error, context to pass to agent is empty"
    aagent = agent_manager.find_agent_by_name(agent)

    if not aagent:
        return f"Error, agent {agent} not found"
        
    # start agent in a new thread and exit
    agent_system = aagent.system
    agent_prompt = aagent.prompt
    print(f"Playing Sub Agent {agent} system={agent_system} prompt={agent_prompt}")
    t = threading.Thread(target=background_thread, args=(agent, agent_system, agent_prompt, context))
    t.daemon = True  # Permet au thread de s'arrêter avec le programme
    t.start()
    return "agent called"

# Fonction pour exécuter en arrière-plan
def background_thread(agent_name, agent_system, agent_prompt, context):
    play(agent_name, agent_system, agent_prompt, input_text=f"{context}")
