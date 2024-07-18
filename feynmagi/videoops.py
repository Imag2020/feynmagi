from transformers import AutoProcessor, AutoModelForCausalLM  
from PIL import Image
import requests
import copy
import torch
import gc
from io import BytesIO
import base64

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

#model_id = 'microsoft/Florence-2-large'
model_id = 'microsoft/Florence-2-base'
model = AutoModelForCausalLM.from_pretrained(model_id, trust_remote_code=True).eval().cuda()
'''
if device =='cuda':
    model.cuda()
'''   
processor = AutoProcessor.from_pretrained(model_id, trust_remote_code=True)

def run_example(image, task_prompt, text_input=None):
    if text_input is None:
        prompt = task_prompt
    else:
        prompt = task_prompt + text_input

    inputs = processor(text=prompt, images=image, return_tensors="pt")
    inputs = {key: value.cuda() for key, value in inputs.items()}
    
    model.eval()  # Assurez-vous que le modèle est en mode d'évaluation
    with torch.no_grad():  # Désactive la construction du graphe de calcul
        generated_ids = model.generate(
            input_ids=inputs["input_ids"],
            pixel_values=inputs["pixel_values"],
            max_new_tokens=1024,
            early_stopping=False,
            do_sample=False,
            num_beams=3,
        )
        generated_text = processor.batch_decode(generated_ids, skip_special_tokens=False)[0]
        parsed_answer = processor.post_process_generation(
            generated_text, 
            task=task_prompt, 
            image_size=(image.width, image.height)
        )

    # Libérer explicitement la mémoire GPU
    del inputs
    del generated_ids
    del image
    torch.cuda.empty_cache()
    gc.collect()

    return parsed_answer

def caption_image(frame):
    task_prompt = '<CAPTION>'
    image = Image.fromarray(frame)
    cap = run_example(image, task_prompt)
    
    return cap

def od_image(frame):
    task_prompt = '<OD>'
    image = Image.fromarray(frame)
    od = run_example(image, task_prompt)
    
    return od

def ask_image(prompt,base64_image):
    task_prompt = '<MORE_DETAILED_CAPTION>'
    image_data = base64.b64decode(base64_image)
    image_stream = BytesIO(image_data)
    image = Image.open(image_stream)

    od = run_example(image, task_prompt,prompt)
    
    return od['<MORE_DETAILED_CAPTION>']
    