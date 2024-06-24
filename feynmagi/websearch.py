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


def google_urls_search(req,pages=1):
    # Initialize the WebDriver
    print(f"=================== google_urls_search  {req}")
    logger.say_text(f"Opening Chrome for {req}")
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    driver = webdriver.Chrome(options=chrome_options)
    driver.get("https://www.google.com/search?q="+req)
   
    # Accept the cookies if necessary
    logger.debug("Accpting cookies")
    try:
        driver.find_element(By.ID, 'L2AGLb').click()
    except Exception as e:
        logger.debug(f"Exception when clicking cookies button: {e}")

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

def google_home_search(req,pages=1):
    # Initialize the WebDriver
    print(f"=================== google home search  {req}")
    # Initialize the WebDriver
    print(f"=================== google home search  {req}")
    #say_text(f"Opening Chrome for {req}")
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    print("Opening Chrome for google Search")
    driver = webdriver.Chrome(options=chrome_options)
    driver.get("https://www.google.com/search?q="+req)

    # Accept the cookies if necessary
    print("Accpting cookies")
    try:
        driver.find_element(By.ID, 'L2AGLb').click()
    except Exception as e:
        print(f" !!!!! Exception when clicking cookies button: {e}")

    pageSource = driver.page_source
    htmlc=copy.copy(pageSource)
    driver.save_screenshot('screen_goole.png')
    # Close the browser
    print("Closing Chrome")
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


    
def scrape_website( url: str , objective: str ):
    # response = requests.post(post_url, headers=headers, data=data_json)
    print("")
    print("")
    print(f" >>>>>>>>>>>>>>>>>>>>>>>>>< scap {url} {objective}")
    print("")
    print("")
    chrome_options = Options()
    chrome_options.add_argument("--headless")
  
    driver = webdriver.Chrome(options=chrome_options)
    #driver = webdriver.Chrome()
    
    # Navigate to Google Search
    text=""
    try:
        driver.get(url)
        time.sleep(2.0)  # adjust time as needed
        pageSource = driver.page_source
        soup = BeautifulSoup(pageSource, "html.parser")
    
        for script in soup(["script", "style"]):
            script.decompose()
        text = soup.get_text()
        #print("CONTENTTTTTT:", text)
    except:
        print(f"url expetion {url}")
        
    print("Closing Chrome")
    driver.quit()
    
    output = summary_one_page(objective, text)
    len_output=len(output)
    lprint(f"returing output len={len_output}")
    return output

def summary_pages(query, list_contents):
    print("============== summary_pages  44  ", query)
    
    logger.debug(f"summary_pages query={query} ")
    prompt="""Giving following list of links and informations from the web extract and summarize a response to this question : {query}.
removes redundancies. Do not repeat contradictory information. Give a precise and concise answer as much as possible. Think step by step.
Informations are given in this format:

#Info : "informations"

#link : "the link to the web page"

"""
    prompt=prompt.replace("{query}",query)
    new_line="""
    #info : "{info}"

    #link : "{url}"
    """
    for cc in list_contents:
        line=new_line.replace("{info}",cc['info'])
        line=line.replace("{url}",cc['url'])
        prompt+=line
    prompt+="""Please use only the informations above from the web, if you dont find the answer for the question just say can not find information"""
   

    
   
    ret=""
    for t in llmsapis.llmchatgenerator({'role':'user','content':prompt}):
        ret+=t
   
    print("====================> ")
    print(prompt)
    print("==================")
    return ret


def summary_one_page_d(query, cont): 
    print("====== summary_one_page")
    
    
    prompt="""Act as a real time web agent researcher, Giving following web page text just extracted from the web, find related information or answer this query : "{query}".

"{cont}"

Give only answer for the query "{query}" nothong else, if yuo dont find answer output : can not find information using this query try an other search query.
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
    print("====== Deep search ")
    global gurls

    # got urls 
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
    
def start_search(query,pages):
   
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(search, (query, pages))

        # Pour arrêter la tâche
        # stop_event.set()

        # Vérifiez si le calcul est terminé
        if future.done():
            resultat = future.result()
            print("Le calcul est terminé.")
        else:
            print("Le calcul est toujours en cours...")


def quick_search(query: str, pages=4) -> str:
    logger.say_text(f"quick_search on google home page for :  {query}")
    ret = google_home_search(query)
    output=summary_one_page_d(query,ret)
    logger.say_text(f"quick_search  google returning:  {output}")
    return output

def start_quick_search(query,pages=1):
    
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(quick_search, (query, pages))

        # Pour arrêter la tâche
        # stop_event.set()

        # Vérifiez si le calcul est terminé
        if future.done():
            resultat = future.result()
            print("Le calcul est terminé.")
        else:
            printt("Le calcul est toujours en cours...")


