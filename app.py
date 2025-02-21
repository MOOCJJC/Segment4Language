import streamlit as st
import openai
import os
import io
import nltk
import time
import ffmpeg
import zipfile
from dotenv import load_dotenv
import yt_dlp
from pydub import AudioSegment
import tempfile

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

def generate_speech(text, voice):
    response = client.audio.speech.create(
        model="tts-1",
        voice=voice,
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

def download_youtube_audio(url):
    # Create a temporary directory for downloads if it doesn't exist
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
    # Convert time in MM:SS format to milliseconds
    start_ms = sum(x * int(t) for x, t in zip([60000, 1000], start_time.split(":")))
    end_ms = sum(x * int(t) for x, t in zip([60000, 1000], end_time.split(":")))
    segment = audio[start_ms:end_ms]
    
    # Export segment to a temporary file
    temp_segment = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
    segment.export(temp_segment.name, format="mp3")
    return temp_segment.name

def transcribe_audio(audio_file):
    with open(audio_file, "rb") as f:
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=f
        )
    return transcript.text

def split_audio_file(audio_file, transcription):
    """Split an audio file into segments based on transcription sentences"""
    # Split text into sentences
    sentences = nltk.sent_tokenize(transcription)
    
    # Load the audio file
    audio = AudioSegment.from_mp3(audio_file)
    total_duration = len(audio)
    
    # Estimate duration per character
    char_duration = total_duration / len(transcription)
    
    audio_segments = []
    start_pos = 0
    
    for sentence in sentences:
        # Estimate the duration of this sentence
        duration = len(sentence) * char_duration
        end_pos = min(start_pos + duration, total_duration)
        
        # Extract segment
        segment = audio[start_pos:end_pos]
        
        # Convert segment to bytes
        segment_byte_io = io.BytesIO()
        segment.export(segment_byte_io, format='mp3')
        segment_bytes = segment_byte_io.getvalue()
        
        audio_segments.append((sentence, segment_bytes))
        start_pos = end_pos
        
        if start_pos >= total_duration:
            break
    
    return audio_segments

# Main app interface
st.title("English Learning Assistant")

# Create tabs
tab1, tab2 = st.tabs(["Text to Speech", "YouTube Processing"])

with tab1:
    # Original app functionality
    chinese_text = st.text_area("Enter Chinese text:", height=150)
    
    voice = st.selectbox(
        "Select Voice:",
        ["nova", "shimmer", "echo", "onyx", "fable", "alloy", "ash", "sage", "coral"]
    )

    if st.button("Translate and Generate Speech"):
        # Clear session state when new text is entered
        if chinese_text and st.session_state.get('last_input') != chinese_text:
            st.session_state.clear()
            st.session_state.translation_done = False
            st.session_state.last_input = chinese_text

        if chinese_text:
            with st.spinner("Processing..."):
                # Store results in session state
                if st.session_state.translation_done == False:
                    # Translate text
                    english_text = translate_text(chinese_text)
                    
                    # Generate speech for full text
                    audio_bytes = generate_speech(english_text, voice)
                    
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

with tab2:
    st.header("YouTube Audio Processor")
    
    # Add a clear button
    if st.button("Clear"):
        # Clean up files
        if 'audio_file' in st.session_state and os.path.exists(st.session_state.audio_file):
            try:
                os.remove(st.session_state.audio_file)
            except:
                pass
        # Clear session state
        st.session_state.clear()
        st.rerun()  # Updated from experimental_rerun() to rerun()
    
    # YouTube URL input
    youtube_url = st.text_input("Enter YouTube URL:")
    
    if youtube_url:
        if 'audio_file' not in st.session_state or not os.path.exists(st.session_state.audio_file):
            with st.spinner("Downloading audio..."):
                try:
                    audio_file, video_title = download_youtube_audio(youtube_url)
                    st.session_state.audio_file = audio_file
                    st.session_state.video_title = video_title
                    st.success(f"Downloaded: {video_title}")
                except Exception as e:
                    st.error(f"Error downloading video: {str(e)}")
        
        if 'audio_file' in st.session_state and os.path.exists(st.session_state.audio_file):
            # Audio player
            with open(st.session_state.audio_file, 'rb') as f:
                st.audio(f.read(), format='audio/mp3')
            
            # Time selection
            col1, col2 = st.columns(2)
            with col1:
                start_time = st.text_input("Start Time (MM:SS)", "00:00")
            with col2:
                end_time = st.text_input("End Time (MM:SS)", "00:30")
            
            # Add audio processing method selection
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
                with st.spinner("Processing audio segment..."):
                    # Extract segment
                    segment_file = extract_audio_segment(st.session_state.audio_file, start_time, end_time)
                    
                    # Transcribe
                    transcription = transcribe_audio(segment_file)
                    
                    if process_method == "Generate New Audio with TTS":
                        # Generate new audio with TTS
                        audio_bytes = generate_speech(transcription, voice)
                        segments = split_text_and_audio(transcription, audio_bytes)
                    else:
                        # Use original audio
                        segments = split_audio_file(segment_file, transcription)
                    
                    # Display results
                    st.subheader("Transcription:")
                    st.write(transcription)
                    
                    # Create download zip
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
                        
                        # Add extracted full segment
                        zipf.write(segment_file, f"extracted_segment_{timestamp}.mp3")
                        
                        # Add segmented audio files
                        for i, (sentence, segment_bytes) in enumerate(segments):
                            segment_path = f"downloads/segment_{timestamp}_{i}.mp3"
                            save_audio(segment_bytes, segment_path)
                            zipf.write(segment_path, f"segment_{timestamp}_{i}.mp3")
                            os.remove(segment_path)
                    
                    # Cleanup
                    os.remove(segment_file)
                    
                    # Provide download button
                    with open(zip_path, 'rb') as f:
                        st.download_button(
                            label="Download Processed Files (ZIP)",
                            data=f,
                            file_name=f"youtube_segment_{timestamp}.zip",
                            mime="application/zip",
                            key=f"zip_{timestamp}"
                        )

# Cleanup on session end - moved to a more controlled location
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
