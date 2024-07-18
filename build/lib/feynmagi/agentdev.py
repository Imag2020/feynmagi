###########################################################################################
#
# FeynmAGI V0.1
# Imed MAGROUNE
# 2024-06
#
#########################################################################################


from .llmsapis import *
from .config import stop_event, logger
from .helper import *


import concurrent.futures
import ast
import subprocess
import os
import ast
import pkg_resources


def dev_code(objective, language, framework, file_name):
    dir_path = pkg_resources.resource_filename('feynmagi', 'data/working/')
    prompt = f"""Act as an AI agent expert in code developing, write me a {language} code for this objective: {objective}.
please output only the full code including requirements importations.
please include comments to explain the code.
output nothing else but the code as to write into a code file delemited by markdowns.
"""
    f_prompt = format_prompt(message=prompt)
    ret = llm(f_prompt)

    # Extract the code from the markdown text
    code = extract_code_from_markdown(ret)
    
    if code:
        write_code_to_file(os.path.join(dir_path, file_name), code)
        extract_requirements_from_py(os.path.join(dir_path, file_name))
        print(file_name + " file code generated")
        return file_name + " file code generated"
    else:
        print("Failed to extract code from the response.")
        return "Failed to extract code from the response."

def write_code_to_file(file_path, text):
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(text)
    return f"Successfully wrote to '{file_path}'."

def extract_requirements_from_py(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        tree = ast.parse(file.read(), filename=file_path)

    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name.split('.')[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.add(node.module.split('.')[0])

    # Create a requirements.txt file
    requirements_path = os.path.join(os.path.dirname(file_path), 'requirements.txt')
    with open(requirements_path, 'w', encoding='utf-8') as req_file:
        for imp in sorted(imports):
            req_file.write(f"{imp}\n")
    
    return f"Successfully wrote requirements to '{requirements_path}'"

def create_conda_env(env_name, requirements_file=None):
    try:
        # Create conda environment
        subprocess.run(f"conda create -n {env_name} python=3.8 -y", shell=True, check=True)

        # Install requirements
        if requirements_file is not none and requirements_file!= "":
            subprocess.run(f"conda install --name {env_name} --file {requirements_file} -y", shell=True, check=True)

        print(f"Conda environment '{env_name}' created and packages installed.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Failed to create conda environment or install packages: {e}")
        return False

def exec_code_in_conda_env(env_name, file_name, input_data):
    try:
        # Activate conda environment and run script with input data
        result = subprocess.run(
            f"conda run -n {env_name} python {file_name}",
            input=input_data,
            shell=True,
            check=True,
            capture_output=True,
            text=True
        )
        return  0, result.stdout, ''
        
    except subprocess.CalledProcessError as e:
        return e.returncode, e.output, e.stderr
        
    except Exception as e:
        return  1,'',str(e)


def intercept_error_message(e):
    error_message = str(e)
    if "ContainerError" in error_message:
        return "An error occurred in the Docker container execution."
    elif "FileNotFoundError" in error_message:
        return "The specified file was not found."
    else:
        return error_message

