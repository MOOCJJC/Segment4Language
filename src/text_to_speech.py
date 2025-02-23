import streamlit as st
import os
import time
import zipfile
from .utils import generate_speech, split_audio_file, save_audio, get_openai_client

def translate_text(chinese_text):
    client = get_openai_client()
    instruction_prompt = "Translate the Chinese text into natural, speaking English suitable for youtube vlog. " \
        + "English is not my first language, so please don't use complex grammar."
    
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": instruction_prompt},
            {"role": "user", "content": chinese_text}
        ]
    )
    return response.choices[0].message.content

def render_text_to_speech_tab():
    chinese_text = st.text_area("Enter Chinese text:", height=150)
    
    voice = st.selectbox(
        "Select Voice:",
        ["nova", "shimmer", "echo", "onyx", "fable", "alloy", "ash", "sage", "coral"]
    )

    if st.button("Translate and Generate Speech"):
        if chinese_text and st.session_state.get('last_input') != chinese_text:
            st.session_state.clear()
            st.session_state.translation_done = False
            st.session_state.last_input = chinese_text

        if chinese_text:
            process_text_to_speech(chinese_text, voice)

def process_text_to_speech(chinese_text, voice):
    with st.spinner("Processing..."):
        if not st.session_state.get('translation_done', False):
            # Translate text
            english_text = translate_text(chinese_text)
            
            # Generate speech for full text
            audio_file = generate_speech(english_text, voice)
            
            # Split into segments
            segments = split_audio_file(audio_file, english_text)
            
            # Create downloads directory if it doesn't exist
            os.makedirs("downloads", exist_ok=True)
            
            # Save full audio
            timestamp = time.strftime("%Y%m%d-%H%M%S")
            
            # Store results in session state
            st.session_state.timestamp = timestamp
            st.session_state.english_text = english_text
            st.session_state.audio_file = audio_file
            st.session_state.segments = segments
            st.session_state.translation_done = True

        create_output_files()

def create_output_files():
    timestamp = st.session_state.timestamp
    audio_file = st.session_state.audio_file
    segments = st.session_state.segments
    english_text = st.session_state.english_text

    # Display the translation
    st.write("English translation:")
    st.write(english_text)

    # Create zip file with outputs
    zip_path = f"downloads/english_learning_{timestamp}.zip"
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        # Save and add English text file
        text_path = f"downloads/english_text_{timestamp}.txt"
        with open(text_path, 'w', encoding='utf-8') as f:
            f.write(english_text)
        zipf.write(text_path, f"english_text_{timestamp}.txt")
        os.remove(text_path)

        # Add full audio
        zipf.write(audio_file, f"full_audio_{timestamp}.mp3")

        # Add segment files
        for i, (sentence, segment_bytes) in enumerate(segments):
            segment_path = f"downloads/segment_{timestamp}_{i}.mp3"
            save_audio(segment_bytes, segment_path)
            zipf.write(segment_path, f"segment_{timestamp}_{i}.mp3")
            os.remove(segment_path)

    # Cleanup
    os.remove(audio_file)

    # Provide download button
    with open(zip_path, 'rb') as f:
        st.download_button(
            label="Download All Files (ZIP)",
            data=f,
            file_name=f"english_learning_{timestamp}.zip",
            mime="application/zip",
            key=f"zip_{timestamp}"
        )
