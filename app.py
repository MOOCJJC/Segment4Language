import streamlit as st
import openai
import os
import io
import nltk
import time
import ffmpeg
import zipfile
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Specify the NLTK data path
nltk.data.path.append('C:/Users/write/AppData/Roaming/nltk_data')

# Download required NLTK data
nltk.download('punkt')
nltk.download('punkt_tab')

# Initialize OpenAI client
client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

def translate_text(chinese_text):
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

def generate_speech(text):
    response = client.audio.speech.create(
        model="tts-1",
        voice="onyx",
        input=text
    )
    
    # Save the full audio temporarily
    audio_bytes = io.BytesIO(response.content)
    return audio_bytes

def split_text_and_audio(text, audio_bytes):
    # Split text into sentences
    sentences = nltk.sent_tokenize(text)
    
    # Track temporary files
    temp_files = []

    try:
        # Save the full audio to a temporary file
        with open("temp_full_audio.mp3", "wb") as f:
            f.write(audio_bytes.read())
        temp_files.append("temp_full_audio.mp3")

        # Get the duration of the full audio
        probe = ffmpeg.probe("temp_full_audio.mp3")
        duration = float(probe['format']['duration'])
        
        # Estimate duration per character (seconds)
        char_duration = duration / len(text)
        
        audio_segments = []
        start_pos = 0
        
        for sentence in sentences:
            # Estimate the duration of this sentence
            duration = len(sentence) * char_duration
            end_pos = start_pos + duration
            
            # Debug prints
            print(f"Processing segment: {sentence}")
            print(f"Start position: {start_pos}")
            print(f"End position: {end_pos}")
            print(f"Duration: {duration}")
            
            # Extract the segment using ffmpeg
            segment_path = f"temp_segment_{start_pos:.2f}_{end_pos:.2f}.mp3"
            temp_files.append(segment_path)

            ffmpeg.input("temp_full_audio.mp3", ss=start_pos, t=duration).output(
                segment_path,
                format='mp3',
                acodec='libmp3lame',
                audio_bitrate='192k'
            ).run()
            
            with open(segment_path, "rb") as f:
                segment_bytes = f.read()
            
            audio_segments.append((sentence, segment_bytes))
            start_pos = end_pos
        
        return audio_segments
    
    finally:
        # Clean up temporary files
        for temp_file in temp_files:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            except Exception as e:
                print(f"Error deleting temporary file {temp_file}: {e}")

def save_audio(audio_bytes, filename):
    with open(filename, 'wb') as f:
        f.write(audio_bytes)
    return filename

st.title("English Learning Assistant")

# Text input
chinese_text = st.text_area("Enter Chinese text:", height=150)

if 'translation_done' not in st.session_state:
    st.session_state.translation_done = False

# Clear session state when new text is entered
if chinese_text and st.session_state.get('last_input') != chinese_text:
    st.session_state.clear()
    st.session_state.last_input = chinese_text

if st.button("Translate and Generate Speech"):
    if chinese_text:
        with st.spinner("Processing..."):
            # Store results in session state
            if 'translation_done' not in st.session_state:
                # Translate text
                english_text = translate_text(chinese_text)
                
                # Generate speech for full text
                audio_bytes = generate_speech(english_text)
                
                # Split into segments
                segments = split_text_and_audio(english_text, audio_bytes)
                
                # Create downloads directory if it doesn't exist
                os.makedirs("downloads", exist_ok=True)
                
                # Save full audio
                timestamp = time.strftime("%Y%m%d-%H%M%S")
                
                # Store results in session state
                st.session_state.timestamp = timestamp
                st.session_state.english_text = english_text
                st.session_state.audio_bytes = audio_bytes
                st.session_state.segments = segments
                st.session_state.translation_done = True


            # Use stored results for display and downloads
            timestamp = st.session_state.timestamp
            audio_bytes = st.session_state.audio_bytes
            segments = st.session_state.segments
            english_text = st.session_state.english_text

            # Display the translation
            st.write("English translation:")
            st.write(english_text)

            # Create a zip file containing all outputs
            zip_path = f"downloads/english_learning_{timestamp}.zip"
            with zipfile.ZipFile(zip_path, 'w') as zipf:
                # Save and add English text file
                text_path = f"downloads/english_text_{timestamp}.txt"
                with open(text_path, 'w', encoding='utf-8') as f:
                    f.write(english_text)
                zipf.write(text_path, f"english_text_{timestamp}.txt")
                os.remove(text_path)  # Clean up text file

                # Add full audio
                full_audio_path = f"downloads/full_audio_{timestamp}.mp3"
                with open(full_audio_path, 'wb') as f:
                    audio_bytes.seek(0)
                    f.write(audio_bytes.read())
                zipf.write(full_audio_path, f"full_audio_{timestamp}.mp3")
                os.remove(full_audio_path)  # Clean up full audio

                # Add segment files
                for i, (sentence, segment_bytes) in enumerate(segments):
                    segment_path = f"downloads/segment_{timestamp}_{i}.mp3"
                    save_audio(segment_bytes, segment_path)
                    zipf.write(segment_path, f"segment_{timestamp}_{i}.mp3")
                    os.remove(segment_path)  # Clean up segment file

            # Provide download button for zip file
            with open(zip_path, 'rb') as f:
                st.download_button(
                    label="Download All Files (ZIP)",
                    data=f,
                    file_name=f"english_learning_{timestamp}.zip",
                    mime="application/zip",
                    key=f"zip_{timestamp}"
                )