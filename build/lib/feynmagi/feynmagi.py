###########################################################################################
#  
# FeynmAGI V0.1  
# Imed MAGROUNE  
# 2024-06
#
#########################################################################################
from flask import Flask, render_template, request, jsonify, send_from_directory
from .socketio_instance import init_socketio, set_socketio
from  . import config as cfg
from . import autollm  # Importer votre module
from flask import current_app
from flask import send_file
import base64
import time
from pydub import AudioSegment
import numpy as np
import io
import threading
from  . import llmsapis as llm
from datetime import datetime
from . import logger
from . import helper
import subprocess
from scipy.io import wavfile
import tempfile
import librosa
from .audio import transcribe_audio
from werkzeug.utils import secure_filename
import os

from . import digest
from jinja2 import Environment, FileSystemLoader, select_autoescape, Template

from .tasks import add_task, thread_manager, start_autosession_task, start_digest_url_task,start_digest_doc_task, start_rag_task
import webbrowser
import torch
from . import interpreter as ex
from . import agentdev
import pkg_resources

device = "cuda" if torch.cuda.is_available() else "cpu"

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'static', 'uploads')

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'static', 'uploads')
print("Static folder set to:", app.static_folder)
print("Upload folder set to:", app.config['UPLOAD_FOLDER'])

socketio = init_socketio(app)
set_socketio(socketio)  # Passer l'instance socketio à autollm

@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory(app.static_folder, filename)
    
@socketio.on('interllm')
def handle_interllm_request(data):
    message = data['message']
    print(f"[DEBUG] Received message: {message}")  # Log de diagnostic
    socketio.start_background_task(target=thread_manager, message=message)

'''

def thread_manager(message):
    print(f"[DEBUG] Starting thread manager with message: {message}")  # Log de diagnostic
    autollm.start_autosession(message)
'''

audio_available=False
image_available=False

def help():
    global device
    global audio_available
    global image_available
    
    models=helper.get_models()
    options=[]
    if models is not None:
        for m in models['models']:
            if "embed" not in m['name']:
                options.append(m['name'])
    llama_msg=""
    version,retcode=check_ollama_installed()
    if  retcode:
        llama_msg="Ollama is not installed here, for local LLMs you must install it <a href='https://ollama.com/'><button id='install_ollama' class='icon-btn' title='Install ollama'> <span class='bi bi-cloud-arrow-down-fill'></span></button></a>"
    else:
        llama_msg="Your "+version['output']
        
    
    openai_msg=""
    if cfg.cfg.openaikey=="":
        openai_msg="Your OpenAI API key is empty"
    elif cfg.cfg.openai_organisation=="":
        openai_msg="Your OpenAI organization is empty"
    elif cfg.cfg.openai_project=="":
        openai_msg="Your OpenAI Project is empty"
        

    groq_msg=""
    if cfg.cfg.groqkey=="":
        groq_msg="Your Groq API key is empty"

    model_msg=""
    if not retcode:
        if "phi3:latest" not in  options:
            model_msg="For best local LLM experience please pull phi3 model : ollama run phi3 <button id='installphi3' class='icon-btn' title='pull phi3'><span class='bi bi-microsoft-fill'></span></button>"

    if "llava-llama3:latest"  in options:
        image_available = True
        
    

    my_platform=ex.get_platform()
    ffmpeg_msg=""
    if not ex.check_ffmpeg_installed():
        ffmpeg_msg="Please install ffmpeg for lcoal audio <button id='installffmpeg' class='icon-btn' title='Install ffmpeg'><span class='bi bi-mic-fill'></span></button>"
    else:
        audio_available=True
        
    
    response_text = f"""
    <div class="helpdiv">
        <h2>Let's start </h2>
        <p>My env: {my_platform} / {device} <br> {ffmpeg_msg} </p>
        <p>{llama_msg}</p>
        <p>{openai_msg}</p>
        <p>{groq_msg}</p>
        <p>{model_msg}</p>
    </div>
    """
    return response_text

@socketio.on('connect')
def handle_connect():
    
    
    models=helper.get_models()
    options=[]
    if models is not None:
        for m in models['models']:
            if "embed" not in m['name']:
                options.append(m['name'])
    socketio.emit('update_select', {'options': options})
    
    socketio.emit('history', cfg.session_history.list_sessions())
    if 'phi3:latest' in options:
        socketio.emit('set_select', {'model': "phi3:latest"})
    else:
        cfg.actual_model=options[0]
        
    cfg.actual_session_id=helper.get_timestamp()
    print(f"on connect cfg.llm_connect: {cfg.llm_connect}")
    
    version, retcode=check_ollama_installed()
    if  retcode:
        socketio.emit('error', {'message': 'Ollama is not installed ! for local LLM please install it first'})
    socketio.emit('response_token', {'token': help()})
    
    

@socketio.on('delete_session')
def handle_delete_session(data):
    session_id = data['session_id']
    if cfg.session_history.delete_session(session_id):
        socketio.emit('session_deleted', {'session_id': session_id, 'status': 'success'})
    else:
        socketio.emit('session_deleted', {'session_id': session_id, 'status': 'file_not_found'})
    

@socketio.on('select_change')
def handle_select_change(message):
    selected_option = message['option']
    print(f"Option selected: {selected_option}")
    cfg.actual_model=selected_option
    # Vous pouvez ajouter ici d'autres logiques comme mettre à jour une base de données, etc.

@socketio.on('connect_llm')
def handle_api_change(message):
    selected_option = message['api']
    print(f"Connect Option selected: {selected_option}")

    if selected_option == "openai" and cfg.cfg.openaikey=="":
        socketio.emit('error', {'message': 'OpenAI key not set, please update your config '})
        return
    if selected_option == "groq" and cfg.cfg.groqkey=="":
        socketio.emit('error', {'message': 'Groq key not set, please update your config '})
        return
        
    cfg.llm_connect=selected_option

    print(f"on change cfg.llm_connect: {cfg.llm_connect}")
    # Vous pouvez ajouter ici d'autres logiques comme mettre à jour une base de données, etc.

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('pull_model')
def pull_model():
    print("pulling default model")
    socketio.emit('error', {'message': 'Pulling model please wait few minutes'})
    try:
        print("trying")
        result,status = ex.execute_command("ollama pull phi3")
        # Capture du code de retour et de la sortie
        ret=result
        print(ret)
    except FileNotFoundError:
        # Si la commande n'est pas trouvée, retourner False
        print("error")
        ret= "Command ollama not found ! "
        socketio.emit('error', {'message': ret})

@socketio.on('pull_ffmpeg')
def pull_ffmpegl():
    print("Installing ffmpeg")
    socketio.emit('error', {'message': 'Installing ffmpeg please wait few minutes'})
    try:
        print("trying")
        result= ex.install_ffmpeg()
        # Capture du code de retour et de la sortie
        print(result)
    except FileNotFoundError:
        # Si la commande n'est pas trouvée, retourner False
        print("error")
        ret= "ffmpeg failed, please install it manually"
        socketio.emit('error', {'message': ret})
    


@app.route('/get-text-file')
def get_text_file():
    path_to_text_file=pkg_resources.resource_filename('feynmagi', 'data/dials.txt')
    return send_file(path_to_text_file, as_attachment=True)


@socketio.on('load_session')
def handle_load_session(data):
    session_id = data.get('session_id')
    session = cfg.session_history.load_session(session_id)
    print("got session", session)
    if session:
        socketio.emit('session', session)
        cfg.session_message_history=session
    else:
        socketio.emit('error', {'message': 'Session not found'})

@socketio.on('new_llm')
def handle_new_llm():
    cfg.actual_engine="llm"
    print("engine = llm")
    if cfg.session_message_history != [] :
        cfg.session_history.save_session(cfg.session_message_history,cfg.actual_session_id)
    cfg.session_message_history.clear()
    cfg.agent_message_history.clear()
    socketio.emit('clean_output')
    actual_agent="default"
    cfg.actual_session_id=helper.get_timestamp()

@socketio.on('new_agent')
def handle_new_agent():
    global actual_engine
    print("engine = agent")
    cfg.actual_engine="agent"
    if cfg.session_message_history != [] :
        cfg.session_history.save_session(cfg.session_message_history,cfg.actual_session_id)
    cfg.session_message_history.clear()
    cfg.agent_message_history.clear()
    socketio.emit('clean_output')
    cfg.actual_agent="default"
    cfg.actual_session_id=helper.get_timestamp()
    

@socketio.on('new_image')
def handle_new_iamge():
    global image_available
    print("engine = image")
    cfg.actual_engine="image"
    if cfg.session_message_history != [] :
        cfg.session_history.save_session(cfg.session_message_history,cfg.actual_session_id)
    cfg.session_message_history.clear()
    cfg.agent_message_history.clear()
    socketio.emit('clean_output')
    cfg.actual_agent="default"
    cfg.actual_session_id=helper.get_timestamp()
    if not image_available:
        socketio.emit('error', {'message': 'Please pull llava-llama3 model first ! '})

@socketio.on('new_document')
def handle_new_document():
    print("engine = rag")
   
    cfg.actual_engine="rag"
    if cfg.session_message_history != [] :
        cfg.session_history.save_session(cfg.session_message_history,cfg.actual_session_id)
    cfg.session_message_history.clear()
    cfg.agent_message_history.clear()
    socketio.emit('clean_output')
    cfg.actual_agent="rag"
    cfg.actual_session_id=helper.get_timestamp()
    # agentdev.testdev()
    
@app.route('/get_config')
def get_config():
    config_data = {
        'continuous_mode': cfg.cfg.continuous_mode,
        'speak_mode': cfg.cfg.speak_mode,
        'openaikey': cfg.cfg.openaikey,
        'groqkey': cfg.cfg.groqkey,
        'openai_organisation': cfg.cfg.openai_organisation,
        'openai_project': cfg.cfg.openai_project,
        'api_endpoint': cfg.cfg.api_endpoint,
        'api_chat_endpoint': cfg.cfg.api_chat_endpoint,
        'embedding_endpoint': cfg.cfg.embedding_endpoint,
        'openai_mode': cfg.cfg.openai_model,
        'groq_model': cfg.cfg.groq_model
    }
    return jsonify(config_data)

@socketio.on('set_config')
def handle_system_set_config_request(data):
    cfg.cfg.continuous_mode = data.get('continuousmode', cfg.cfg.continuous_mode)
    cfg.cfg.speak_mode = data.get('speakmode', cfg.cfg.speak_mode)
    cfg.cfg.openaikey = data.get('openaikey', cfg.cfg.openaikey)
    cfg.cfg.groqkey = data.get('groqkey', cfg.cfg.groqkey)
    cfg.cfg.openai_organisation = data.get('openaiorganisation', cfg.cfg.openai_organisation)
    cfg.cfg.openai_project = data.get('openaiproject', cfg.cfg.openai_project)
    cfg.cfg.api_endpoint = data.get('apiendpoint', cfg.cfg.api_endpoint)
    cfg.cfg.api_chat_endpoint = data.get('chatapiendpoint', cfg.cfg.api_chat_endpoint)
    cfg.cfg.embedding_endpoint = data.get('embedapiendpoint',cfg. cfg.embedding_endpoint)
    cfg.cfg.openai_model = data.get('openaimodel', cfg.cfg.openai_model)
    cfg.cfg.groq_model = data.get('groqmodel', cfg.cfg.groq_model)
    
    cfg.save_config()

    socketio.emit('config_updated', {'status': 'success'})



    
@socketio.on('digest_url')
def handle_digest_url(data):
    print(data)
    url = data['url']
    scrabbing=data['scrabbing']
    tag=data['tag']
    if tag =="":
        tag="default"
    # digest.scrab_webpages(url,scrabbing)
    print("digest_url",url,scrabbing,tag)
    add_digest_url_task(url,scrabbing,tag)

def add_digest_url_task(url,scrabbing,tag):
    add_task(2, start_digest_url_task, url,scrabbing,tag)
    print("[DEBUG] Task digest url added to queue")

@socketio.on('popup')
def handle_popup(data):
    message = data['message']
    
    if message == "yes":
        print("User send Yes")
        cfg.yes_event.set()
    elif message == "no":
        print("User send No")
        cfg.no_event.set()
    else:
        print("User send Cancel")
        cfg.feed_event.set()
        feed = data['feed']
        cfg.event_data["feed"]=feed
    
@socketio.on('stop_generation')
def handle_stop_message():
    logger.say_text("Stopped")
    cfg.stop_event.set()
    return "Task stopped"

###############################################################################
################################################################################
# Function to handle incoming message and add it to the task queue
# Function to handle incoming message and add it to the task queue
def add_message_task(message):
    print(f"[DEBUG] Received message: {message}")
    add_task(1, start_autosession_task, message)
    print("[DEBUG] Task added to queue")

def add_rag_task(message,tag):
    print(f"[DEBUG] Received message: {tag} / {message}")
    add_task(1, start_rag_task, message,tag)
    print("[DEBUG] Task added to queue")
    
@socketio.on('send_message')
def handle_message(data):
    global base64_string
    cfg.stop_event.clear()  # Réinitialiser pour une nouvelle génération
    message = data['message']
    tag=data['tag']
    if tag =="":
        tag="default"
    prompt=f"{message}"

    print("))))))))))))))))))))))))))))))))=",cfg.actual_engine)
    # Traitement du message ici, par exemple en utilisant votre fonction llm
    # Ensuite, envoyez les réponses au client caractère par caractère
    if cfg.actual_engine == "llm":
        cfg.session_message_history.append({"role": "user", "content": message})
        ret=""
        for response_text in llm.llmchatgenerator(cfg.session_message_history, temperature=0,stream=True):
            ret+=response_text
            socketio.emit('response_token', {'token': response_text})
            if cfg.stop_event.is_set():  # Vérifiez si l'événement a été déclenché
                break
        cfg.session_message_history.append({"role": "assistant", "content": ret})
        
    elif cfg.actual_engine == "image":
        
        if base64_string == "":
            logger.send_popup("Please upload image first !")
            return 
        for response_text in llm.llimgenerator(prompt, temperature=0,stream=False, raw=False, image=base64_string):
            socketio.emit('response_token', {'token': response_text})
            if cfg.stop_event.is_set():  # Vérifiez si l'événement a été déclenché
                break
    elif cfg.actual_engine == "rag":

        message = data['message']
        tag = data['tag']
        if tag =="":
            tag="default"
        print(f"[DEBUG]  engine rag Received message tag : {tag} / {message}")  # Log de diagnostic
        add_rag_task(message,tag)        
        
    else:
        message = data['message']
        print(f"[DEBUG] Received message: {message}")  # Log de diagnostic
        add_message_task(message)
        

# Endpoint of the second Flask app performing inference
INFERENCE_API_URL = 'http://localhost:8889/transcribe'



def handle_webm_audio(webm_data):
    # Charger les données audio WebM dans un objet AudioSegment
    audio_segment = AudioSegment.from_file(io.BytesIO(webm_data), format="webm")
    # Rééchantillonner l'audio à 16000 Hz et le convertir en mono
    resampled_audio = audio_segment.set_frame_rate(16000).set_channels(1)
    # Convertir en WAV avec une profondeur de bit spécifique
    wav_bytes_io = io.BytesIO()
    # Spécifier la profondeur de bit à 16 bits lors de l'exportation
    resampled_audio.export(wav_bytes_io, format="wav", parameters=["-acodec", "pcm_s16le"])
    wav_bytes = wav_bytes_io.getvalue()
    return wav_bytes


def wav_bytes_to_np_array(wav_bytes):
    # Utiliser scipy pour lire les bytes WAV dans un tableau NumPy
    sample_rate, audio_data = wavfile.read(io.BytesIO(wav_bytes))
    # S'assurer que audio_data est un tableau NumPy (ndarray est le type de tableau NumPy)
    np_audio_data = np.array(audio_data,dtype=np.int16) 
    print("np_audio_data shape", np_audio_data.shape)
    return sample_rate, np_audio_data

@socketio.on('startrecord')
def handle_startrecord():
    global audio_available
    if not audio_available:
        socketio.emit('error', {'message': 'Audio not available, please install ffmpeg first ! '})
        
    
@socketio.on('audio')
def handle_audio(data):
    global audio_available
    if not audio_available:
        return
    print("/audio", type(data))
    # Process or save the chunk as needed
    wav_bytes = handle_webm_audio(data)
    sample_rate, audio_data = wav_bytes_to_np_array(wav_bytes)
    print(f"sample rate {sample_rate}  l={len(audio_data)} {type(audio_data)} === ")

    # Convertir le tableau NumPy en bytes pour l'envoi
    audio_bytes = audio_data.tobytes()
    # Envoyer les données audio à l'API pour transcription via une requête POST
    
    response = transcribe_audio(audio_bytes)
    
    # Vérifier la réponse de l'API
    if 'result' in response:
        
        print("Réponse de l'API:", response)
        socketio.emit('audio_token', {'token': response['result'][0]})
    else:
        print("Erreur lors de l'envoi des données audio à l'API:")
        socketio.emit('error', {'Audio Module error'})


@socketio.on('imagequestion')
def handle_imagequestion(data):
    global base64_string
    if base64_string == "":
        send_popup("Please upload image first !")
        return 
    #print(base64_string)
    prompt = data['message']
    # print("/image", prompt, "base64=",base64_string)
    # print("=============== uplodaed file", base64_string)
    for response_text in llimgenerator(prompt, temperature=0,stream=False, raw=False, image=base64_string):
        socketio.emit('response_token', {'token': response_text})
    socketio.emit('response_token', {'token': "<br>End<br>"})
        
# Ensure there's a folder for the uploads

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Function to check for allowed image files
def allowed_image_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in {'jpg', 'jpeg', 'png'}

# Function to check for allowed text or PDF files
def allowed_text_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in {'txt', 'pdf'}
    

uploaded_file=""

base64_string=""

@app.route('/iupload', methods=['POST'])
def upload_file_and_convert():
    global base64_string
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'})
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'})

    # Convert file stream directly to base64
    base64_string = base64.b64encode(file.read()).decode('utf-8')
    #print("loaded base64_string",base64_string)
    # Reset the file pointer to the beginning of the file
    file.seek(0)

    if file and allowed_image_file(file.filename):
        filename = secure_filename(file.filename)
        save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(save_path)
        
        # You might also want to send the base64 string back to the client
        # Or use it however you see fit within your application logic
        return jsonify({'success': 'Image uploaded successfully', 'filename': filename, 'base64': base64_string})
    else:
        return jsonify({'error': 'File not allowed'})

save_path=""
@app.route('/fupload', methods=['POST'])
def upload_file():
    global save_path
    global uploaded_file
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'})
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'})

    if file and allowed_text_file(file.filename):
        filename = secure_filename(file.filename)
        save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(save_path)
        uploaded_file=save_path
        # start_process_in_thread(save_path)
        socketio.emit('get_tag')
        return jsonify({'success': 'File uploaded successfully', 'filename': filename})
    else:
        return jsonify({'error': 'File not allowed'})

@socketio.on('response_tag')
def handle_response_tag(data):
    # Recevoir la réponse du client
    global save_path
    tag = data['tag']
    print(f"Tag reçu: {tag}")
    if tag=="":
        tag="default"
    
    # Continuer le traitement ici
    start_process_in_thread(save_path,tag)

def start_process_in_thread(file_path,tag):
    add_task(2, start_digest_doc_task, file_path,tag)
    print("[DEBUG] Task digest doc added to queue")   

def background_thread():
    """Exemple de thread qui envoie un message aux clients toutes les minutes."""
    count = 0
    print("thread OK")
    while True:
        time.sleep(60)  # Attendre 60 secondes

def check_ollama_installed():
    try:
        # Exemple de commande pour vérifier si Ollama est installé
        # result = os.system("ollama -v > /dev/null 2>&1")
        result,ret = ex.execute_command("ollama -v")
        # Capture du code de retour et de la sortie
        return result,ret
    except FileNotFoundError:
        # Si la commande n'est pas trouvée, retourner False
        return result,ret
    
def open_browser():
    time.sleep(2)  # Attendre une seconde pour s'assurer que le serveur est démarré
    webbrowser.open('http://localhost:5000')

def main():
    # Lancer le thread en arrière-plan pour le gestionnaire de tâches
    t = threading.Thread(target=background_thread)
    t.daemon = True  # Permet au thread de s'arrêter avec le programme
    t.start()

    # Démarrer le gestionnaire de tâches
    socketio.start_background_task(thread_manager)

    # Lancer l'application Flask dans un thread
    flask_thread = threading.Thread(target=lambda: socketio.run(app, host='0.0.0.0', debug=False))
    flask_thread.start()

    open_browser()

if __name__ == '__main__':
    main()
   
