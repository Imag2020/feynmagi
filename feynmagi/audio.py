###########################################################################################
#
# FeynmAGI V0.1
# Imed MAGROUNE
# 2024-06
#
#########################################################################################

import numpy as np
# from faster_whisper import WhisperModel
import librosa
import soundfile as sf
from transformers import WhisperProcessor, WhisperForConditionalGeneration
import torch

# Initialize your model here (adjust according to your specific setup)
# load model and processor
device = "cuda" if torch.cuda.is_available() else "cpu"

if device =='cuda':
    model_path="openai/whisper-large-v3"
else:
    model_path="openai/whisper-small"


processor = WhisperProcessor.from_pretrained(model_path)
model = WhisperForConditionalGeneration.from_pretrained(model_path)
model.config.forced_decoder_ids = None
model.to(device)


def resample_audio(input_path, output_path, new_sample_rate=16000):
    # Charger l'audio avec le taux d'échantillonnage d'origine
    audio, sr = librosa.load(input_path, sr=None)

    # Rééchantillonner l'audio au nouveau taux d'échantillonnage
    audio_resampled = librosa.resample(audio, orig_sr=sr, target_sr=new_sample_rate)

    # Sauvegarder l'audio rééchantillonné dans un nouveau fichier
    # sf.write(output_path, audio_resampled, new_sample_rate)
    return audio_resampled

def inference(sample):
    # Réduction de la consommation de mémoire en évitant le calcul du gradient
    global device
    with torch.no_grad():
        input_features = processor(sample, sampling_rate=16000, return_tensors="pt").input_features
        input_features = input_features.to(device)
        predicted_ids = model.generate(input_features)
        # Déplacer les prédictions en mémoire CPU
        predicted_ids = predicted_ids.cpu()

    # Conversion des IDs prédits en texte
    transcription = processor.batch_decode(predicted_ids, skip_special_tokens=True)
    return {'result': transcription}

def transcribe_audio(data):
    if data:
        # Decode the audio file
        audio_data = np.frombuffer(data, dtype=np.int16)
        # Perform inference
        transcription = inference(audio_data)
        print("===========> inference OK",transcription)
        # Return the transcription result
        return transcription
    else:
        return {"error": "No audio data received."}
