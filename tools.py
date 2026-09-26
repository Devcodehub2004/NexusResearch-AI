from langchain_core.tools import tool
import requests
from bs4 import BeautifulSoup
from tavily import TavilyClient
import os 
from dotenv import load_dotenv
from rich import print
load_dotenv()

def _get_tavily_key():
    key = os.getenv("TAVILY_API_KEY")
    if not key:
        try:
            import streamlit as st
            key = st.secrets.get("TAVILY_API_KEY")
        except Exception:
            pass
    return key or ""

tavily = TavilyClient(api_key=_get_tavily_key())
@tool
def web_search(query:str) -> str:
    """Search the web for recent and reliable information on a topic,Return Titles,URLs and snipp"""
    results=tavily.search(query=query,max_results=5)
    out=[]
    for r in results['results']:
        out.append(
            f"Title:{r['title']}\nURL:{r['url']}\nSnippet:{r['content'][:300]}\r"

        )
    return "\n----\n".join(out)


@tool
def scrape_url(url:str)->str:
    """Scrape and return clean text content from a given URL for deeper reading"""
    try:
        resp = requests.get(url, timeout=(3, 5), headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
        soup = BeautifulSoup(resp.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
            tag.decompose()
        text = soup.get_text(separator=" ", strip=True)
        return text[:2500] if text else "Page content was empty or protected."
    except Exception as e:
        return f"Could not Scrape URL: {str(e)}"





