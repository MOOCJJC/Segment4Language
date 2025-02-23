import streamlit as st
import os
import io
import time
import tempfile
import zipfile
import yt_dlp
from pydub import AudioSegment
from .utils import (
    generate_speech,
    save_audio,
    transcribe_audio,
    split_audio_file  # Only import what we need
)

def download_youtube_audio(url):
    temp_dir = "temp_downloads"
    os.makedirs(temp_dir, exist_ok=True)
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': os.path.join(temp_dir, 'temp_%(id)s.%(ext)s')
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        audio_file = os.path.join(temp_dir, f"temp_{info['id']}.mp3")
        return audio_file, info['title']

def extract_audio_segment(audio_file, start_time, end_time):
    audio = AudioSegment.from_mp3(audio_file)
    start_ms = sum(x * int(t) for x, t in zip([60000, 1000], start_time.split(":")))
    end_ms = sum(x * int(t) for x, t in zip([60000, 1000], end_time.split(":")))
    segment = audio[start_ms:end_ms]
    
    temp_segment = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
    segment.export(temp_segment.name, format="mp3")
    return temp_segment.name

def render_youtube_processor_tab():
    st.header("YouTube Audio Processor")
    
    if st.button("Clear", key="clear_button"):
        if 'audio_file' in st.session_state and os.path.exists(st.session_state.audio_file):
            try:
                os.remove(st.session_state.audio_file)
            except:
                pass
        st.session_state.clear()
        st.rerun()
    
    youtube_url = st.text_input("Enter YouTube URL:")
    process_youtube_url(youtube_url)

def process_youtube_url(youtube_url):
    if not youtube_url:
        return

    if 'audio_file' not in st.session_state or not os.path.exists(st.session_state.audio_file):
        with st.spinner("Downloading audio..."):
            try:
                audio_file, video_title = download_youtube_audio(youtube_url)
                st.session_state.audio_file = audio_file
                st.session_state.video_title = video_title
                st.success(f"Downloaded: {video_title}")
            except Exception as e:
                st.error(f"Error downloading video: {str(e)}")
                return

    if 'audio_file' in st.session_state and os.path.exists(st.session_state.audio_file):
        render_audio_processor()

def render_audio_processor():
    with open(st.session_state.audio_file, 'rb') as f:
        st.audio(f.read(), format='audio/mp3')
    
    col1, col2 = st.columns(2)
    with col1:
        start_time = st.text_input("Start Time (MM:SS)", "00:00")
    with col2:
        end_time = st.text_input("End Time (MM:SS)", "00:30")
    
    process_method = st.selectbox(
        "Select Processing Method:",
        ["Use Original Audio", "Generate New Audio with TTS"],
        help="Choose whether to use the original extracted audio or generate new audio using text-to-speech",
        key="process_method_select"
    )
    
    if process_method == "Generate New Audio with TTS":
        voice = st.selectbox(
            "Select Voice:",
            ["nova", "shimmer", "echo", "onyx", "fable", "alloy", "ash", "sage", "coral"],
            key="voice_select_yt"
        )

    if st.button("Extract and Process Segment"):
        process_audio_segment(start_time, end_time, process_method, voice if process_method == "Generate New Audio with TTS" else None)

def process_audio_segment(start_time, end_time, process_method, voice=None):
    with st.spinner("Processing audio segment..."):
        segment_file = extract_audio_segment(st.session_state.audio_file, start_time, end_time)
        transcription = transcribe_audio(segment_file)
        
        if process_method == "Generate New Audio with TTS":
            # Generate new audio file with TTS
            tts_file = generate_speech(transcription, voice)
            # Split the TTS audio
            segments = split_audio_file(tts_file, transcription)
            # Clean up TTS file
            os.remove(tts_file)
        else:
            # Use original audio
            segments = split_audio_file(segment_file, transcription)
        
        st.subheader("Transcription:")
        st.write(transcription)
        
        create_output_files(segment_file, transcription, segments)

def create_output_files(segment_file, transcription, segments):
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    zip_path = f"downloads/youtube_segment_{timestamp}.zip"
    os.makedirs("downloads", exist_ok=True)
    
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        # Add transcription
        text_path = f"downloads/transcription_{timestamp}.txt"
        with open(text_path, 'w', encoding='utf-8') as f:
            f.write(transcription)
        zipf.write(text_path, f"transcription_{timestamp}.txt")
        os.remove(text_path)
        
        # Add extracted segment
        zipf.write(segment_file, f"extracted_segment_{timestamp}.mp3")
        
        # Add segmented audio files
        for i, (sentence, segment_bytes) in enumerate(segments):
            segment_path = f"downloads/segment_{timestamp}_{i}.mp3"
            save_audio(segment_bytes, segment_path)
            zipf.write(segment_path, f"segment_{timestamp}_{i}.mp3")
            os.remove(segment_path)
    
    os.remove(segment_file)
    
    with open(zip_path, 'rb') as f:
        st.download_button(
            label="Download Processed Files (ZIP)",
            data=f,
            file_name=f"youtube_segment_{timestamp}.zip",
            mime="application/zip",
            key=f"zip_{timestamp}"
        )
