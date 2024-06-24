###########################################################################################
#
# FeynmAGI V0.1
# Imed MAGROUNE
# 2024-06
#
#########################################################################################
from .config import *
# import fitz  # PyMuPDF
from pdfminer.high_level import extract_text
import threading
from selenium.webdriver.common.by import By
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait 
from selenium.webdriver.support import expected_conditions as EC
import copy
from bs4 import BeautifulSoup
from selenium.webdriver.chrome.options import Options
from urllib.parse import urlparse
import time
import re 


from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time
from urllib.parse import urlparse
import pkg_resources



def split_text_into_chunks(text, chunk_size=1024):
    """Split text into chunks of approximately `chunk_size` words without breaking sentences."""
    import re
    sentences = re.split(r'(?<=[.!?]) +', text)
    chunks = []
    current_chunk = []
    current_chunk_size = 0

    for sentence in sentences:
        sentence_words = sentence.split()
        sentence_word_count = len(sentence_words)

        if current_chunk_size + sentence_word_count <= chunk_size:
            current_chunk.append(sentence)
            current_chunk_size += sentence_word_count
        else:
            if current_chunk:
                chunks.append(' '.join(current_chunk))
            current_chunk = [sentence]
            current_chunk_size = sentence_word_count

    if current_chunk:
        chunks.append(' '.join(current_chunk))

    return chunks

def process_webpage(url, domain, visited,tag):
    print("Processing",url)
    # Initialize the WebDriver
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    print("Opening Chrome for processing URL")
    driver = webdriver.Chrome(options=chrome_options)
    driver.get(url)
    
    # Allow some time for the page to load
    time.sleep(5)  # Adjust based on your needs

    # Extract text while excluding navigation menus and links
    xpath_query = """
        //div[not(ancestor::nav or ancestor::header or ancestor::footer or ancestor::aside)] |
        //p[not(ancestor::nav or ancestor::header or ancestor::footer or ancestor::aside)] |
        //article[not(ancestor::nav or ancestor::header or ancestor::footer or ancestor::aside)] |
        //section[not(ancestor::nav or ancestor::header or ancestor::footer or ancestor::aside)]
    """
    elements = driver.find_elements(By.XPATH, xpath_query)
    text = ' '.join([element.text for element in elements if element.text.strip() != ''])

    # Extract all links from the webpage
    links = [element.get_attribute('href') for element in driver.find_elements(By.TAG_NAME, 'a') if element.get_attribute('href')]

    # Process and store the text
    chunks = split_text_into_chunks(text, 1024)
    for chunk in chunks:
        ragdb.add_data(chunk, url,tag)  # Assume ragdb is an instance of RagDB

    # Close the browser
    driver.quit()

    # Filter links, follow only internal links and avoid already visited
    internal_links = set()
    for link in links:
        if urlparse(link).netloc == domain and link not in visited:
            internal_links.add(link)

    return internal_links

def scrab_webpages(start_url, scrabbing=False, tag="default"):
    domain = urlparse(start_url).netloc
    visited = set()
    to_visit = {start_url}

    print("Digesting ===>", start_url)
    while to_visit:
        current_url = to_visit.pop()
        if current_url not in visited:
            visited.add(current_url)
            print(f"Processing {current_url}")
            new_links = process_webpage(current_url, domain, visited,tag)
            to_visit.update(new_links)
            print(f"Found {len(new_links)} new internal links to process.")
        if not scrabbing:
            print("No scrabbing, exit now")
            break


def file_type(filename):
    """Determine the file type based on its extension."""
    if '.' in filename:
        return filename.rsplit('.', 1)[1].lower()
    return None  # This could be an exception if you prefer strict handling


def read_file(file_path):
    """Read the content of a file and return it as a string."""
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()

def file_type(filename):
    if '.' in filename:
        return filename.rsplit('.', 1)[1].lower()
    return None  # or raise an error if you prefer


def pdf_to_text(pdf_path):
    """Extract text from a PDF file."""
    # doc = fitz.open(pdf_path)  # Open the PDF file
    doc = extract_text(pdf_path)
    return doc

def process_text_file(file_path,tag="default"):
    print("embedding ",file_path)
    """Process the text or PDF file: divide into chunks, embed each chunk, and add to the vectors database."""
    filetype = file_type(file_path)
    text = ""
    
    if filetype == 'pdf':
        # Extract text from PDF
        text = pdf_to_text(file_path)
    elif filetype == 'txt':
        # Read text directly from a text file
        text = read_file(file_path)
    else:
        raise ValueError("Unsupported file type")

    chunks = split_text_into_chunks(text, 1024)
    
    for chunk in chunks:
        # Updated to pass the file path as a reference along with the chunk
        if chunk != "" and chunk != None:
            print("add chunk to rag",chunk)
            ragdb.add_data(chunk, file_path,tag)  # Assuming add_data now also takes the file path as an argument


