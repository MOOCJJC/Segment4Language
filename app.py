import streamlit as st
import nltk
import os
from src.text_to_speech import render_text_to_speech_tab
from src.youtube_processor import render_youtube_processor_tab

# Specify the NLTK data path
nltk.data.path.append('C:/Users/write/AppData/Roaming/nltk_data')

# Download required NLTK data
nltk.download('punkt')
nltk.download('punkt_tab')

# Main app interface
st.title("English Learning Assistant")

# Create tabs
tab1, tab2 = st.tabs(["Text to Speech", "YouTube Processing"])

with tab1:
    render_text_to_speech_tab()

with tab2:
    render_youtube_processor_tab()

# Cleanup on session end
def cleanup_temp_files():
    temp_dir = "temp_downloads"
    if os.path.exists(temp_dir):
        for file in os.listdir(temp_dir):
            try:
                os.remove(os.path.join(temp_dir, file))
            except:
                pass
        try:
            os.rmdir(temp_dir)
        except:
            pass

# Register cleanup function
import atexit
atexit.register(cleanup_temp_files)
