###########################################################################################
#
# FeynmAGI V0.1
# Imed MAGROUNE
# 2024-06
#
#########################################################################################
from .logger import * 
import abc
import dataclasses
import orjson
from typing import Any, List, Optional

import numpy as np
import os
from . import helper
from . import logger
from . import vectorsdb 
import traceback
from . import websearch as webs
from . import config as cfg

import os
import html
import json
import base64

import threading
from . import autollm

from . import agentdev as dev
from .tasks import add_task, thread_manager
import pkg_resources


def calculate(num1, operator, num2):
    num1=float(num1)
    num2=float(num2)
    if operator == '+':
        return num1 + num2
    elif operator == '-':
        return num1 - num2
    elif operator == '*' or operator == 'x':
        return num1 * num2
    elif operator == '/' or operaror == '÷':
        if num2 != 0:
            return num1 / num2
        else:
            return "Error: Division by zero."
    else:
        return "Error: Unsupported operator."
        

def get_command(response_json):
    """Parse the response and return the command name and arguments"""
    logger.debug(f"get_command {response_json}")
    print("=========================> get command")
    print("get command",type(response_json),response_json)
    try:
        if "command" not in response_json:
            return "exit" , "Missing 'command' object in JSON"

        command = response_json["command"]

        if "name" not in command:
            return "exit", "Missing 'name' field in 'command' object"

        command_name = command["name"]

        if command_name == None:
            return "exit", "Missing 'name' field in 'command' object"


        # Use an empty dictionary if 'args' field is not present in 'command' object
        arguments = command.get("args", {})

        return command_name, arguments
    except json.decoder.JSONDecodeError:
        return "exit", "Invalid JSON"
    # All other errors, return "Error: + error message"
    except Exception as e:
        return "Error:", str(e)

def get_thoughts(response_json):
    """Parse the response and return the command name and arguments"""
    logger.debug(f"get_thoughts {response_json}")
    print("=========================> get command")
    print("get thoughts",type(response_json),response_json)
    try:
        if "thoughts" not in response_json:
            return "Error:" , "Missing 'command' object in JSON"

        thoughts = response_json["thoughts"]

        if "speak" not in thoughts:
            return "Error:", "Missing 'speak' field in 'thoughts' object"

        speak = thoughts["speak"]

        # Use an empty dictionary if 'args' field is not present in 'command' object

        return speak
    except json.decoder.JSONDecodeError:
        return "Error:", "Invalid JSON"
    # All other errors, return "Error: + error message"
    except Exception as e:
        return "Error:", str(e)


def execute_command(command_name, arguments):
    """Execute the command and return the result"""

    print(f"__________________ //{command_name}//",command_name,"  args : ", arguments)
    print("____________________________________________//")
    memory = cfg.vdb
    command_name=command_name.lower().strip()
    try:
        if command_name == "output" :
            message=arguments.get("output","")
            if message == "" or message == None :
                message=arguments["message"]

            print("printing output",message)
            send_text(message)
            return "exit"
            
        if command_name == "do-nothing" or  command_name == "exit" :
            return "exit"
        elif command_name == "ask":
            question=arguments["question"]
            if question ==  None:
                question = "Any additional information?"
            return send_popup(question)
            
        elif command_name == "google" or command_name == "google search" :
           
            return webs.quick_search(arguments['query'])
            
        elif command_name == "calculate" :
            return calculate(arguments["num1"],arguments["operator"],arguments["num2"])
        elif command_name == "rag" :
            return " Nothing found "
        elif command_name == "agent" :
            return " Agent started "
        elif command_name == "memory" :
            return " Memorized "
        elif command_name == "developer" :
            return " agent started "
        elif command_name == "interpreter" :
            return " started  "
            
        elif command_name == "start-agent":
            logger.say_text(f"Starting agent {arguments['agent']} for {arguments['objective']}")
            return start_agent(
                arguments["agent"],
                arguments["objective"])

        elif command_name == "help":
            message="Help" # arguments["file"]
            return logger.say_text(message)
            
        elif command_name == "dev-code":
            objective=arguments["objective"]
            language = arguments["language"]
            framework = arguments["framework"]
            file_name = arguments["file_name"]
            return dev.dev_code(objective,language,framework,file_name)

        elif command_name == "create_conda_env":
            env_name=arguments["env_name"]
            return dev.create_conda_env(env_name)   
            
        elif command_name == "execute-code":
            
            file_name=arguments["file_name"]
            input=arguments["input"]
            environment=arguments["environment"]
            status,output,error = dev.exec_code_in_conda_env(environment,file_name,input)

            print("____________    exec in conda en v --------------")
            print("status = ", status)
            print("error = ",error)
            print("output = ",output)
            print("_ end ___________    exec in conda en v --------------")
            
            if not status:
                return 'exec command return : ' + output
            return 'error in exec command '+error   
        
        elif command_name == "read-file":
            return read_file(arguments["file"])    
        elif command_name == "display-file":
            return display_file(arguments["file"])       
        elif command_name == "write-to-file":
            return write_to_file(arguments["file"], arguments["text"])
        elif command_name == "append-to-file":
            return append_to_file(arguments["file"], arguments["text"])
        elif command_name == "delete-file":
            return delete_file(arguments["file"])
            
       
        elif command_name == "browse-website":
            return webs.browse_website(arguments["url"], arguments["question"])
        # TODO: Change these to take in a file rather than pasted code, if
        # non-file is given, return instructions "Input should be a python
        # filepath, write your code to file and try again"
        elif command_name == "evaluate-code":
            return ai.evaluate_code(arguments["code"])
        elif command_name == "improve-code":
            return ai.improve_code(arguments["suggestions"], arguments["code"])
        elif command_name == "write-tests":
            return ai.write_tests(arguments["code"], arguments.get("focus"))
        elif command_name == "execute_python_file":  # Add this command
            return execute_python_file(arguments["file"])
        elif command_name == "generate-image":
            return generate_image(arguments["prompt"])
        elif command_name == "do-nothing":
            return "No action performed."
        elif command_name == "task-complete":
            shutdown()
        else:
            return f"Unknown command '{command_name}'. Please refer to the 'COMMANDS' list for available commands and only respond in the specified JSON format."
    # All errors, return "Error: + error message"
    except Exception as e:
        return "Error: " + str(e)


def get_datetime():
    """Return the current date and time"""
    return "Current date and time: " + \
        datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def display_file(file_path):
    """
    Reads the contents of a file and displays them in a black background box with buttons to copy and download.
    
    :param file_path: Path to the file to be read
    """
    dir_path=pkg_resources.resource_filename('feynmagi', 'data/working/')
    file_path=dir_path+file_path
    if not os.path.exists(file_path):
        return logger.say_text(f"Error: File '{file_path}' does not exist.")
    
    with open(file_path, 'r',encoding='utf-8') as file:
        contents = file.read()
        
    file_name = os.path.basename(file_path)
    
    html_content = f"""
    <div style="background-color: black; color: white; padding: 20px; border-radius: 5px; position: relative;">
        <pre id="fileContent" style="white-space: pre-wrap; word-wrap: break-word; color: white;">{contents}</pre>
        <button id="copyButton" title="Copy" style="position: absolute; top: 10px; right: 60px; background-color: white; color: black; border: none; padding: 10px; cursor: pointer;"><span class="bi bi-copy"></span></button>
        <a id="downloadButton" href="data:text/plain;charset=utf-8,{contents}" download="{file_name}" style="position: absolute; top: 10px; right: 10px; background-color: white; color: black; border: none; padding: 10px; text-decoration: none; text-align: center;"><span class="bi bi-download"></span></a>
    </div>
    <script>
        $(document).ready(function() {{
            $('#copyButton').click(function() {{
                const text = $('#fileContent').text();
                const tempInput = $('<input>');
                $('body').append(tempInput);
                tempInput.val(text).select();
                document.execCommand('copy');
                tempInput.remove();
                alert('Copied to clipboard');
            }});
        }});
    </script>
    """
   
    send_textfile(html_content)
    return("File Displyed")

def read_file(file_path):
    dir_path=pkg_resources.resource_filename('feynmagi', 'data/working/')
    file_path=dir_path+file_path
    """
    Reads the contents of a file and returns them.
    
    :param file_path: Path to the file to be read
    :return: Contents of the file
    """
    if not os.path.exists(file_path):
        return f"Error: File '{file_path}' does not exist."
    
    with open(file_path, 'r',encoding='utf-8') as file:
        contents = file.read()
    return f"\n\n--start\n{contents}\n--end"

def write_to_file(file_path, text):
    dir_path=pkg_resources.resource_filename('feynmagi', 'data/working/')
    file_path=dir_path+file_path
    """
    Writes text to a file, overwriting any existing content.
    
    :param file_path: Path to the file to be written to
    :param text: Text to write to the file
    :return: Success message
    """
    with open(file_path, 'w',encoding='utf-8') as file:
        file.write(text)
        file.close()
    
    return f"Successfully wrote to '{file_path}'."

def append_to_file(file_path, text):
    dir_path=pkg_resources.resource_filename('feynmagi', 'data/working/')
    file_path=dir_path+file_path
    """
    Appends text to a file.
    
    :param file_path: Path to the file to append to
    :param text: Text to append to the file
    :return: Success message
    """
    with open(file_path, 'a' ,encoding='utf-8') as file:
        file.write(text)
    return f"Successfully appended to '{file_path}'."