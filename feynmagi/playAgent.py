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


class PAgent:
    def __init__(self, system: str = "") -> None:
        self.system = system
        self.messages: list = []
        if self.system:
            self.messages.append({"role": "system", "content": system})

    def __call__(self, message=""):
        if message:
            self.messages.append({"role": "user", "content": message})
        result = self.execute()
        self.messages.append({"role": "assistant", "content": result})
        return result

    def execute(self):
       
        ret="" # llm(json.dumps(self.messages))
        for response_text in llmsapis.llmchatgenerator(self.messages, temperature=0., stream=True, raw=False):
            ret += response_text
        print(f"______ llm return : {repr(ret)}______")
        return ret.replace("\\n","\n")
'''
def play(agent_name, agent_system,agent_prompt, max_iterations=10):
    global tools
    socketio = get_socketio()
    agent_manager = AgentManager()
    # get tools 
    aagent = agent_manager.find_agent_by_name(agent_name)
    if aagent:
        if aagent.tools != []:
            
            tools_str="\nYour available actions are:\n\n\n"
            ftools_str = ""
            for tool in aagent.tools:  # Ici, `agent.tools` devrait être une liste de clés
                if tool in tools:     # Vérifie que la clé existe dans le dictionnaire `tools`
                    tools_str += f"{tools[tool]}\n\n"
            agent_system=agent_system.format(tools=tools_str)
            print(f"__________ final system={agent_system} ______")
    # format system prompt
    # test if {tools} in systel ?
    
    agent = PAgent(system=agent_system)
    
    next_prompt = agent_prompt
    socketio.emit('output_agent', {"token" : next_prompt})
    i = 0
  
    while i < max_iterations:
        i += 1
        result = agent(next_prompt)
        print(result)
        socketio.emit('output_agent', {"token" : f"{result}"})

        if "PAUSE" in result and "Action" in result:
            action = re.findall(r"Action\s*:?\s*([a-z_]+)\s*:\s*(.+)", result, re.IGNORECASE)

            print(f"actipn=___{action}___")
            socketio.emit('output_agent', {"token" : f"{action}"})
            if action == None or action==[]:
                next_prompt = "Observation: Action syntax is wrong"
                socketio.emit('output_agent', {"token" : next_prompt})
                continue
                
            chosen_tool = action[0][0]
            print(f"tool=___{chosen_tool}___")
            socketio.emit('output_agent', {"token" : f"{chosen_tool}"})
            arg = action[0][1]
            arg=arg.replace('\'','\\\'')
            print(f"arg=___{arg}___")
            if chosen_tool in aagent.tools:
                try:
                    result_tool = eval(f"{chosen_tool}('{arg}')")
                    next_prompt = f"Observation: {result_tool}"
                except Exception as e:
                    result_tool =f"{e}"
                    next_prompt = f"Observation: {result_tool}"
                    

            else:
                next_prompt = "Observation: Tool not found"
                

            print(next_prompt)
            socketio.emit('output_agent', {"token" : next_prompt})
            continue

        if "Answer" in result:
            break
    print(f"End Agent result={result}")
    socketio.emit('output_agent', {"token" : result } )
'''

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

    
def play(agent_name, agent_system, agent_prompt, max_iterations=10):
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
    socketio.emit('output_agent', {"token": next_prompt})
    i = 0
  
    while i < max_iterations:
        i += 1
        result = agent(next_prompt)
        print(result)
        socketio.emit('output_agent', {"token": f"{result}"})

        if "PAUSE" in result and "Action" in result:
            actions = re.findall(r"Action\s*:?\s*([a-z_]+)\s*:\s*(.+)", result, re.IGNORECASE)
            if not actions:
                next_prompt = "Observation: Action syntax is wrong"
                socketio.emit('output_agent', {"token": next_prompt})
                continue
            
            chosen_tool, args = actions[0][0], actions[0][1].split(", ")
            
            # Appliquer 'extraire_chaine' à chaque argument
            args_list = [extraire_param(arg) for arg in args]
            print(f"tool=___{chosen_tool}___")
            print(f"args=___{args_list}___")
            if chosen_tool in aagent.tools:
                args_list = [arg.replace('\'', '\\\'') for arg in args_list]  # escape single quotes
                try:
                    result_tool = eval(f"{chosen_tool}(*args_list)")
                    next_prompt = f"Observation: {result_tool}"
                except Exception as e:
                    result_tool = str(e)
                    next_prompt = f"Observation: {result_tool}"
            else:
                next_prompt = "Observation: Tool not found"
                
            print(next_prompt)
            socketio.emit('output_agent', {"token": next_prompt})
            continue

        if "Answer" in result:
            break
    print(f"End Agent result={result}")
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
'''
def email(to_email, subject, body, attachment_path=None):
    to= extraire_param(to_email)
    attach=extraire_param(attachment_path)
    
    if attach is not None and attach != "None":
        send_email(to_email, subject, body, attach)
    else:
    
        send_email(to, extraire_param(subject), extraire_param(body),attach)
'''
def email(to, subject, body, attachment_path=None):
    print("________________________ attachment_path = ", attachment_path, "_____end")
    if attachment_path is not None and "none" not in attachment_path.lower():
        send_email(to, subject, body, attachment_path)
    else:
        send_email(to, subject, body,attachment_path)


def calculate(operation: str) -> float:
    return eval(operation)


def get_planet_mass(planet) -> float:
    match planet.lower():
        case "earth":
            return 5.972e24
        case "jupiter":
            return 1.898e27
        case "mars":
            return 6.39e23
        case "mercury":
            return 3.285e23
        case "neptune":
            return 1.024e26
        case "saturn":
            return 5.683e26
        case "uranus":
            return 8.681e25
        case "venus":
            return 4.867e24
        case _:
            return 0.0
