import requests
from bs4 import BeautifulSoup

def download_latest_arxiv_paper(query):
    """Downloads the latest arXiv paper matching the given query.

    Args:
        query (str): The search query for arXiv.

    Returns:
        str: The content of the latest paper as HTML, or None if no papers are found.
    """
    url = f"https://arxiv.org/search/?query={query}&searchtype=all&source=header"  # Construct the arXiv search URL
    response = requests.get(url)  # Send a GET request to the URL

    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')  # Parse the HTML content
        paper_links = soup.find_all('a', class_='list-title'})  # Find all paper links on the page

        if paper_links:
            latest_paper_link = paper_links[0]['href']  # Get the link to the latest paper
            return requests.get(latest_paper_link).text  # Download and return the paper content as text
        else:
            print("No papers found for the query.")
            return None
    else:
        print(f"Request failed with status code {response.status_code}")
        return None

# Example usage:
paper_content = download_latest_arxiv_paper("LLM AI SOTA")  # Download the latest paper on "LLM AI SOTA"
if paper_content:
    print(paper_content)  # Print the downloaded paper content