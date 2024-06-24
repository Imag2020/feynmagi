###########################################################################################
#
# FeynmAGI V0.1
# Imed MAGROUNE
# 2024-06
#
#########################################################################################
import json
import requests
from . import helper
from . import logger

from . import config as cfg
from openai import OpenAI
from groq import Groq


def openai_llm(messages):
    
    client = OpenAI(
      organization=cfg.cfg.openai_organisation , 
      project=cfg.cfg.openai_project , 
        api_key=cfg.cfg.openaikey
    )
    stream = client.chat.completions.create(
        model= cfg.cfg.openai_model, 
        messages=messages,
        stream=True,
    )
    
    ret=""
    for chunk in stream:
        if cfg.stop_event.is_set():
            print("stopped")
            break
        if chunk.choices[0].delta.content is not None:
            print(chunk.choices[0].delta.content, end="")
            ret+=chunk.choices[0].delta.content
    return ret
    '''
    for chunk in stream:
        if cfg.stop_event.is_set():
            print("stopped")
            break
        if chunk.choices[0].delta.content is not None:
            print("open ai ",chunk.choices[0].delta.content)
            yield chunk.choices[0].delta.content
    '''


def groq_llm(messages):
    if cfg.stop_event.is_set():
        print("stopped")
        
    client = Groq(api_key=cfg.cfg.groqkey)

    chat_completion = client.chat.completions.create(
        messages=messages,
        model=cfg.cfg.groq_model, #"llama3-70B-8192",
    )
    return chat_completion.choices[0].message.content
    
def llmgenerator(messages, temperature=0, stream=True , raw=True):

    if cfg.llm_connect == "openai" :
        print("llm calling open Ai")
        ret =  openai_llm({'role':'user', 'content': messages})
        print("zzzzzzzzz",ret)
        yield ret
        return
        
    if cfg.llm_connect == "groq":
        print("llm calling groq Ai")
        ret = groq_llm({'role':'user', 'content': messages})
        print("rrrrrrrrrr",ret )
        yield ret
        return
        
    headers = {
        "Content-Type": "application/json",
    }
    json_options= {
    "seed": 123,
    "temperature": temperature,
   }
    data = {
        
        "model" :  cfg.actual_model,
        "prompt": messages,
        #"format": "json",
        "raw" : raw,
        "options": json_options,
        "temperature": temperature,
        "stream": stream,
        "n_predict" : 8048,
        "repeat_penalty": 1.2,
    }
    print("request")
    try:
        print("trying")
        response = requests.post(cfg.cfg.api_endpoint, headers=headers, data=json.dumps(data), stream=stream)
        print("end request",response)
        if response.status_code == 200:
            #print("response 200")
            for line in response.iter_lines():
                #print("line=",line)
                if cfg.stop_event.is_set():  # Vérifiez si l'événement a été déclenché
                    break
                if line:
                    line = line.decode('utf-8').strip()
                    #print("fetch")
                    try:
                        yield json.loads(line)[cfg.cfg.json_str]
                    except :
                        print(f"Impossible de décoder la ligne JSON : {line}")
                        continue
                   
        else:
            print(f"API Error {response.status_code}: {response.text}")
            # raise Exception(f"API Error {response.status_code}: {response.text}")
    except Exception as error:
        print(f"Request Error {str(error)}")
        raise Exception(f"Request  Error {str(error)}")

def llimgenerator(message, temperature=0, stream=True , raw=True, image=None):
    print("llm i generator")
    #got stop options
    # Convert the text back to a list
    print(cfg.actual_model)
    headers = {
        "Content-Type": "application/json",
    }

    data = {
        
        "model" :  "llava-llama3:latest", #cfg.actual_model,
        "prompt": message,
        "images" : [image],
        "options" : {
            "num_ctx": 4096,
            "num_keep": 4,
            "stop": [
                "<|start_header_id|>",
                "<|end_header_id|>",
                "<|eot_id|>"
                ]
            }
    }
    print("request")
    response = requests.post(cfg.cfg.api_endpoint, headers=headers, data=json.dumps(data), stream=stream)
    print("after request")
    if response.status_code == 200:
        print("response 200")
        for line in response.iter_lines():
            print("line=",line)
            if cfg.stop_event.is_set():  # Vérifiez si l'événement a été déclenché
                break
            if line:
                line = line.decode('utf-8').strip()
                try:
                    yield json.loads(line)[cfg.cfg.json_str]
                except :
                    print(f"Impossible de décoder la ligne JSON : {line}")
                    continue
                   
    else:
        print(f"API Error {response.status_code}: {response.text}")
        raise Exception(f"API Error {response.status_code}: {response.text}")


def llmchatgenerator(messages, temperature=0, stream=True, raw=True, image=None, max_tokens=2048):
    '''
    print("start  @@@@@@@@@@@@@@@@@")
    for m in messages:
        print(m['role'])
        print(m['content'])
        print("____________________________")
    print("end @@@@@@@@@@@@@@@@@")
    '''
    if cfg.llm_connect=="openai":
        yield openai_llm(messages)

    if cfg.llm_connect=="groq":
        yield groq_llm(messages) 
    
    headers = {
        "Content-Type": "application/json",
    }

    data = {
        "model": cfg.actual_model,
        "messages": messages,
        "stream" : stream,
        "options": {
            "seed": 101,
            "temperature": temperature
          }
    }
                
    response = requests.post(cfg.cfg.api_chat_endpoint, headers=headers, data=json.dumps(data), stream=stream)

    if response.status_code == 200:
        for line in response.iter_lines():
            if cfg.stop_event.is_set():
                break
            if line:
                line = line.decode('utf-8').strip()
                #print("stripped line=", line, "", "")
                try:
                    content = json.loads(line)["message"]["content"]
                    yield content
                except Exception as e:
                    print(f"Impossible de décoder la ligne JSON : {line}, erreur: {e}")
                    continue
    else:
        print(f"API Error {response.status_code}: {response.text}")
        raise Exception(f"API Error {response.status_code}: {response.text}")
    

def llm(prompt,temperature=0):
    
    if cfg.llm_connect == "openai" :
        print("calling open Ai llm")
        return openai_llm(prompt)
        
    if cfg.llm_connect == "groq":
        print("calling groq Ai llm")
        return groq_llm(prompt)
    
    ret=""
    print("calling local API")
    for response_text in llmgenerator(prompt, temperature, stream=False):
        ret+=response_text
    return ret




EMBEDDING_ENDPOINT = "http://localhost:11434/api/embeddings"
def embeddings(prompt):
    headers = {
        "Content-Type": "application/json",
    }

    data = {
        "model" :  "nomic-embed-text",
        "prompt": prompt
    }
    response = requests.post(cfg.cfg.embedding_endpoint, headers=headers, data=json.dumps(data))
    return response.json()['embedding']


