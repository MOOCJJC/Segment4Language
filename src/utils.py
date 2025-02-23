import os
import io
import nltk
import ffmpeg
import openai
import spacy
import json
import tempfile
from pydub import AudioSegment
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def get_openai_client():
    return openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

def generate_speech(text, voice):
    """Generate speech in MP3 format and return as a temporary file path"""
    client = get_openai_client()
    response = client.audio.speech.create(
        model="tts-1",
        voice=voice,
        input=text,
        response_format="mp3"
    )
    
    # Save to temporary file
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
    temp_file.write(response.content)
    temp_file.close()
    return temp_file.name

def transcribe_audio_with_timestamps(audio_file):
    """Get transcription with segments from Whisper API"""
    client = get_openai_client()
    
    try:
        with open(audio_file, "rb") as f:
            response = client.audio.transcriptions.create(
                model="whisper-1",
                file=f,
                language="en",
                response_format="verbose_json"
            )
        
        # Debug prints
        print("\n=== Processing Segments ===")
        for segment in response.segments:
            print(f"Segment: {segment.text}")
            print(f"Time: {segment.start:.2f}s - {segment.end:.2f}s")
            print("---")
        
        return response
        
    except Exception as e:
        print(f"\nTranscription error: {str(e)}")
        print(f"Error type: {type(e)}")
        return None

def split_audio_file(audio_file, transcription=None):
    """Split audio file into segments based on Whisper API segments, combining into complete sentences"""
    # Get transcription with timestamps if not provided
    result = transcribe_audio_with_timestamps(audio_file)
    if not result:
        return []
    
    print("\n=== Building Sentence Segments ===")
    print("Combining segments into complete sentences...")
    
    # Load the audio file
    audio = AudioSegment.from_mp3(audio_file)
    audio_segments = []
    
    # Temporary storage for building complete sentences
    current_text = ""
    current_start_ms = None
    current_end_ms = None
    
    # Process each segment
    for i, segment in enumerate(result.segments):
        try:
            text = segment.text.strip()
            if not text:
                continue
                
            start_ms = int(float(segment.start) * 1000)
            end_ms = int(float(segment.end) * 1000)
            
            print(f"\nProcessing segment {i+1}:")
            print(f"Text: {text}")
            print(f"Time: {segment.start:.2f}s - {segment.end:.2f}s")
            
            # Initialize start time for new sentence
            if current_start_ms is None:
                current_start_ms = start_ms
                print("Starting new sentence...")
            
            # Add current segment text
            if current_text:
                current_text += " "
            current_text += text
            current_end_ms = end_ms
            print(f"Current accumulated text: {current_text}")
            
            # Check if we have a complete sentence
            if text.rstrip().endswith(('.', '!', '?')):
                # Add padding to segment boundaries
                seg_start = max(0, current_start_ms - 100)
                seg_end = min(len(audio), current_end_ms + 100)
                
                print("\n=== Complete Sentence Found ===")
                print(f"Full sentence: {current_text}")
                print(f"Time range: {seg_start/1000:.2f}s - {seg_end/1000:.2f}s")
                print(f"Duration: {(seg_end - seg_start)/1000:.2f}s")
                
                # Extract and process the segment
                audio_segment = audio[seg_start:seg_end]
                audio_segment = audio_segment.fade_in(50).fade_out(50)
                
                # Convert to bytes
                segment_byte_io = io.BytesIO()
                audio_segment.export(segment_byte_io, format='mp3')
                segment_bytes = segment_byte_io.getvalue()
                
                # Add to segments list
                audio_segments.append((current_text, segment_bytes))
                print("Segment created and added to output")
                print("---")
                
                # Reset for next sentence
                current_text = ""
                current_start_ms = None
                current_end_ms = None
            
        except Exception as e:
            print(f"Error processing segment: {str(e)}")
            continue
    
    # Handle any remaining text as final segment
    if current_text and current_start_ms is not None and current_end_ms is not None:
        try:
            print("\n=== Processing Final Segment ===")
            # Add final period if needed
            if not current_text.rstrip().endswith(('.', '!', '?')):
                current_text += "."
                print("Added ending period to final segment")
            
            # Process final segment
            seg_start = max(0, current_start_ms - 100)
            seg_end = min(len(audio), current_end_ms + 100)
            print(f"Final segment: {current_text}")
            print(f"Time range: {seg_start/1000:.2f}s - {seg_end/1000:.2f}s")
            print(f"Duration: {(seg_end - seg_start)/1000:.2f}s")
            
            audio_segment = audio[seg_start:seg_end]
            audio_segment = audio_segment.fade_in(50).fade_out(50)
            
            segment_byte_io = io.BytesIO()
            audio_segment.export(segment_byte_io, format='mp3')
            segment_bytes = segment_byte_io.getvalue()
            
            audio_segments.append((current_text, segment_bytes))
            print("Final segment created and added to output")
            print("---")
            
        except Exception as e:
            print(f"Error processing final segment: {str(e)}")
    
    print(f"\nTotal segments created: {len(audio_segments)}")
    return audio_segments

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
    """Transcribe audio and process the text"""
    client = get_openai_client()
    
    with open(audio_file, "rb") as f:
        response = client.audio.transcriptions.create(
            model="whisper-1",
            file=f,
            response_format="text"  # Just get plain text
        )
    
    # Process the transcription text
    return process_transcription(response)
