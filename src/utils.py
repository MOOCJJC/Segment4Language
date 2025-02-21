import os
import io
import nltk
import ffmpeg
import openai
import spacy
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def get_openai_client():
    return openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

def generate_speech(text, voice):
    client = get_openai_client()
    response = client.audio.speech.create(
        model="tts-1",
        voice=voice,
        input=text
    )
    
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
        
        # Estimate duration per character
        char_duration = duration / len(text)
        
        audio_segments = []
        start_pos = 0
        
        for sentence in sentences:
            # Estimate the duration of this sentence
            duration = len(sentence) * char_duration
            end_pos = start_pos + duration
            
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

def process_transcription(text):
    """Add proper punctuation to transcribed text using spaCy"""
    try:
        nlp = spacy.load("en_core_web_sm")
    except OSError:
        # Download the model if not present
        spacy.cli.download("en_core_web_sm")
        nlp = spacy.load("en_core_web_sm")
    
    doc = nlp(text)
    
    # Process the text and add periods
    processed_text = ""
    for sent in doc.sents:
        # Clean up the sentence
        sentence = sent.text.strip()
        # Add period if sentence doesn't end with punctuation
        if not sentence[-1] in {'.', '!', '?'}:
            sentence += '.'
        processed_text += sentence + ' '
    
    return processed_text.strip()

def transcribe_audio(audio_file):
    client = get_openai_client()
    with open(audio_file, "rb") as f:
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=f
        )
    # Process the transcription to add proper punctuation
    return process_transcription(transcript.text)
