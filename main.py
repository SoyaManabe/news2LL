# news_feed_app.py
import streamlit as st
import requests
from gtts import gTTS
from io import BytesIO
from bs4 import BeautifulSoup
from openai import OpenAI
from langchain_nvidia_ai_endpoints import ChatNVIDIA
import os

from test import pht_text_to_speech
import asyncio



# Set News API
NEWS_API_KEY = "995323a219c249e2bfbc4f56e72347e6"
NEWS_API_URL = "https://newsapi.org/v2/top-headlines"

VOICE_ID = "0OEhkCv5ieBPIxdqV4GP"

ELEVENLABS_API_KEY = "sk_8fd23bae73e3895c1fbc11069fbfc3ee991b9c06ee01d383"
ELEVENLABS_API_URL = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}/stream"

NEMO_API_KEY = "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"
NEMO_API_URL = "https://integrate.api.nvidia.com/v1"

os.environ["PLAY_HT_USER_ID"] = "wYNfoMQ8WJSabFEVtP0bQzzn6E13"
os.environ["PLAY_HT_API_KEY"] = "ea3c42b8bd6a489bb1098931e0df05e1"


no_article_msg = "Couldn't find article."

def fetch_news(counrty="us", category=None, sources=None):
    params = {
        "apiKey": NEWS_API_KEY,
        #"country": country,
        #"category": category,
        "pageSize": 10,
        "sources": sources
    }
    response = requests.get(NEWS_API_URL, params=params)
    if not sources:
        st.warning("Please input news resouce.")
        return []
    else:
        if response.status_code == 200:
            return response.json().get("articles", [])
        else:
            st.error("Couldn't get news headline")
            return []

def el_text_to_speech(text):
    headers = {
        "Content-Type": "application/json",
        "xi-api-key": ELEVENLABS_API_KEY,
    }
    data = {
        "text": text,
        "voice_settings": {
            "stability": 1.0,
            "similarity_boost": 1.0,
        },
    }
    
    response = requests.post(ELEVENLABS_API_URL, headers=headers, json=data)
    if response.status_code == 200:
        audio = BytesIO(response.content)
        return audio
    else:
        st.error("Can't create the voice")
        return None

def text_to_speech(text):
    tts = gTTS(text=text, lang="en")  # 日本語の場合は "ja" を指定
    audio = BytesIO()
    tts.write_to_fp(audio)
    audio.seek(0)
    return audio
    

def get_article_text(url):
    try:
        # acuire html from url
        response = requests.get(url)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')

        article = soup.find('article')
        if not article:
            article = soup.find('div', class_='content')

        if article:
            paragraphs = article.find_all('p')
            content = "¥n".join([p.get_text() for p in paragraphs])
            return content
        else:
            return no_article_msg
    except requests.exceptions.RequestException as e:
        return f"Error occured: {e}"

def get_summarized_article(article):
    os.environ["NVIDIA_API_KEY"] = NEMO_API_KEY
    llm = ChatNVIDIA(model="mistralai/mixtral-8x7b-instruct-v0.1")
    result = llm.invoke(f"Please summarize following article by extracting key sentences and connect them naturally around 50 words:{article}")
    return result

def check_domain_accessibility(domain):
    try:
        response = requests.get(domain, timeout=5)

        if response.status_code == 200:
            return "Success"
        else:
            return f"Can't access to {domain}. Status code: {response.status_code}."
    except requests.ConnectionError:
        return f"Can't connect to {domain}."

    except requests.Timeout:
        return f"Time out error to {domain}."
    
    except requests.RequestException as e:
        return f"Error occured while connecting to {domain}: {e}"

def get_source_dict():
    source_dict = {}
    sources_url = f'https://newsapi.org/v2/top-headlines/sources?apiKey={NEWS_API_KEY}'
    response = requests.get(sources_url)
    sources_data = response.json()
    for source in sources_data['sources']:
        source_dict[source['id']] = source['name']
    return source_dict

def main():
    # Streamlit UI
    st.title("news2LL")

    col1, col2 = st.columns([1,2])

    selected_data = None
    source_dict = get_source_dict()

    with col1:
        sources = []
        if 'sources' not in st.session_state:
            st.session_state.sources = []

        # 利用可能なソースを表示
        new_publisher = st.selectbox(f"Select News Publisher", source_dict)
        if new_publisher and st.button("Add to source list"):
            st.session_state.sources.append(new_publisher)
            st.success(f"Successed to add {new_publisher}", icon="✅")
        for source in st.session_state.sources:
            st.write(source)
            if st.button("Delete", key=f"{source}"):
                st.session_state.sources.remove(source)

        st.write("Headline:")
        #articles = fetch_news(country, category, sources)
        articles = fetch_news("en", None, st.session_state.sources)

        for article in articles:
            
            st.subheader(article["title"])
            st.write(article["description"])

            if article["url"]:
                st.write(f"[for the detail...]({article['url']})")
            
            if st.button("Pick This News", key=article["title"]):
                selected_data = article
            st.write("---")


    with col2:
        if selected_data:
            st.title(selected_data["title"])
            article = get_article_text(selected_data["url"])
            if article == no_article_msg:
                st.error("Couldn't get the content. Please select different news to study.")
            else:
                summarize = get_summarized_article(article)
                # translate contentn into speech
                #audio_data = el_text_to_speech(summarize.content)
                #audio_data = text_to_speech(summarize.content)
                audio_data = pht_text_to_speech(summarize.content)
                st.audio(audio_data, format="audio/mp3")
                st.write(summarize.content)
        else:
            st.write("Please pick a news from the timeline")

if __name__ == "__main__":
    main()