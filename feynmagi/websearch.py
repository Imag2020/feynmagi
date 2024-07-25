import threading
from selenium.webdriver.common.by import By
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait 
from selenium.webdriver.support import expected_conditions as EC
import copy
from bs4 import BeautifulSoup
from selenium.webdriver.chrome.options import Options

from datetime import datetime
import re
import time

import concurrent.futures

from . import llmsapis 

from .config import stop_event,logger
from .helper import *
from . import logger 

import pdfplumber
import os
import hashlib



def search(query: str, pages=4) -> str:
    logger.say_text(f"quick_search on google home page for :  {query}")
    ret = google_home_search(query)
    output=summary_one_page_d(query,ret)
    logger.say_text(f"quick_search  google returning:  {output}")
    return output

def google_home_search(req,pages=1):
    
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    driver = webdriver.Chrome(options=chrome_options)
    driver.get("https://www.google.com/search?q="+req)

    # Accept the cookies if necessary
    try:
        driver.find_element(By.ID, 'L2AGLb').click()
    except Exception as e:
        print(f" !!!!! Exception when clicking cookies button: {e}")

    pageSource = driver.page_source
    htmlc=copy.copy(pageSource)
    driver.save_screenshot('screen_google.png')
    # Close the browser
    driver.quit()

    soup = BeautifulSoup(pageSource, 'html.parser')
    for script in soup(["script", "style"]):
            script.decompose()
    #text = soup.get_text()
    text = soup.get_text(separator=' ', strip=True)
    # Expression régulière pour matcher les URLs
    url_pattern = r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+|www\.(?:[-\w.]|(?:%[\da-fA-F]{2}))+'
    # Enlever les URLs du texte
    clean_text = re.sub(url_pattern, '', text)
    return clean_text


def summary_one_page_d(query, cont): 
    prompt="""Giving following html content from a web search, please find related information to or try to answer this query : "{query}".

Page content :

"{cont}"

"""
    prompt=prompt.replace("{query}",query)
    prompt=prompt.replace("{cont}",cont)
    #prompt=format_prompt(message=prompt)
    logger.write_log("555 =========================================================================================================")
    logger.write_log(prompt)
    logger.write_log("666 =========================================================================================================")
    ret=""
    for t in llmsapis.llmchatgenerator([{"role":"user", "content": prompt}]):
        ret+=t
    #ret=remove_suffix_if_present(ret,"<|end_of_turn|>"
    if ret =="":
        ret="Can not find what are you asking for LLM returned empty response"
    print("________________________________________ ",ret)
    logger.write_log(ret)
    logger.write_log("777 =========================================================================================================")
    return ret


def weblinks (query: str, nb_pages=1, nb_urls=10) -> str:
    ret = google_urls_search(query,nb_pages)

    for url in ret:
        print(url)
        
    nb=min(nb_urls,len(ret))
    if stop_event.is_set():
        print("Search Stopped ! ")
        return "[stopped]"
    print("urls founds")
    output=''
    for url in ret[:nb]:
        print(url)
        output+=f"{url}\n"
     
        
    return output

def google_urls_search(req,pages=1):
    # Initialize the WebDriver
   
    logger.say_text(f"Opening Chrome for {req}")
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    driver = webdriver.Chrome(options=chrome_options)
    driver.get("https://www.google.com/search?q="+req)
   
    # Accept the cookies if necessary
    
    try:
        driver.find_element(By.ID, 'L2AGLb').click()
    except Exception as e:
        print(f"Exception when clicking cookies button: {e}")

    #scroll
    time.sleep(1.0) 
    last_height = driver.execute_script("return document.body.scrollHeight")

    for i in range(pages):
        # Scroll down to the bottom of the page
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

        time.sleep(1.0)  # adjust time as needed

        # Calculate new scroll height and compare with the last scroll height
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
    #gather data
    content_list = []
    # htmlcontent=driver.find_elements(By.XPATH, "//*")
    pageSource = driver.page_source
    htmlc=copy.copy(pageSource)

    # Close the browser
  
    driver.quit()

    soup = BeautifulSoup(htmlc, 'html.parser')
 
    urls = []
    for url in soup.find_all('a'):
        url=url.get('href')
        if url and not url.startswith(("/","#","https://www.google", 
                                       "https://www.youtube.com",
                                       "https://translate.google",
                                       "https://support.google.com/websearch",
                                       "https://accounts.google",
                                       "https://maps.google",
                                       "https://support.google",
                                       "https://policies.google.com")): 
            # print(url)
            urls.append(url)
    nb_urls=len(urls)
   
    return urls


    
def extract_text_from_pdf(pdf_path, output_dir, base_name):
    text = ""
    page_texts = []
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages):
            page_text = page.extract_text()
            page_texts.append(page_text)
            text += page_text
            with open(os.path.join(output_dir, f"{i}.txt"), 'w', encoding='utf-8') as f:
                f.write(page_text or "")
    with open(os.path.join(output_dir, f"{base_name}.pdf"), 'wb') as f:
        f.write(open(pdf_path, 'rb').read())
    return text, page_texts
    
def url_to_basename(url):
    # Remplacer les caractères non désirés par des underscores
    safe_chars = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_")
    clean_url = ''.join(char if char in safe_chars else '_' for char in url)
    
    # Limiter la longueur du nom pour éviter les problèmes de système de fichiers
    return clean_url[:255]

    
def scrap(url: str):
    base_name = url_to_basename(url)
    output_dir = os.path.join(os.getcwd(), base_name)
    os.makedirs(output_dir, exist_ok=True)
    
    response = requests.head(url)
    content_type = response.headers.get('Content-Type', '')

    if 'application/pdf' in content_type:
        pdf_response = requests.get(url)
        pdf_path = os.path.join(output_dir, f"{base_name}.pdf")
        with open(pdf_path, "wb") as f:
            f.write(pdf_response.content)
        
        text, page_texts = extract_text_from_pdf(pdf_path, output_dir, base_name)
        os.remove(pdf_path)  # Optional: Remove the temporary PDF file if no longer needed
        return "PDF file downloaded,"+str(len(page_texts))+" pages\nfile_path="+pdf_path+"\ncontent summary:\n"+text[:2000]  # Returning a summary of the text
    else:
        # Traitement pour les pages HTML
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        driver = webdriver.Chrome(options=chrome_options)
        text = ""
        try:
            driver.get(url)
            time.sleep(2.0)
            page_source = driver.page_source
            soup = BeautifulSoup(page_source, "html.parser")
    
            for script in soup(["script", "style"]):
                script.decompose()
            text = soup.get_text()
            with open(os.path.join(output_dir, f"{base_name}.txt"), 'w', encoding='utf-8') as f:
                f.write(text)
        except Exception as e:
            print(f"url exception {url}: {str(e)}")
        
        print("Closing Chrome")
        driver.quit()
        return "HTML file downloaded\nfile_path="+os.path.join(output_dir, f"{base_name}.txt")+"\ncontent summary:\n"+text[:2000]  # Returning a summary of the text
        
def segment_text_semantically(text, approx_max_word_count):
    # Utilisez la ponctuation pour trouver les fins de phrases possibles.
    sentence_endings = re.compile(r'[.!?]\s')
    sentences = sentence_endings.split(text)

    current_segment = ""
    current_word_count = 0
    segments = []

    for sentence in sentences:
        # Comptez le nombre de mots dans la phrase.
        word_count = len(sentence.split())

        # Si ajouter cette phrase dépasse la limite de mots, enregistrez le segment actuel.
        if current_word_count + word_count > approx_max_word_count:
            if current_segment:
                segments.append(current_segment.strip())
            current_segment = sentence
            current_word_count = word_count
        else:
            # Ajoutez l'espace perdu en splittant le texte, sauf si c'est la première phrase du segment.
            if current_segment:
                current_segment += " "
            current_segment += sentence
            current_word_count += word_count

    # Ajoutez le dernier segment restant s'il contient du texte.
    if current_segment.strip():
        segments.append(current_segment.strip())

    return segments


    



