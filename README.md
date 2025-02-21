# English Learning Assistant

An application to help with English learning through AI translation and text-to-speech.

## Introduction

When using Xiaolai Li's [1000h](https://www.1000h.org) or Enjoy app, I wanted to utilize my commute time to practice English, as I have at least 2.5 hours of commute every working day. However, I encountered an issue: the Enjoy app's mobile version is not very user-friendly for long-commute drivers. When practicing, I generally want to repeat the same sentence multiple times. On the Enjoy app, I need to manually select the section of the text I want to practice, which is not feasible while driving.

To solve this, I created an app with two main functions:

1. Text to Speech: This feature segments the full audio of a paragraph into individual sentences. While driving, I can simply open the audio file and keep repeating the same sentence. To switch sentences, I just need to swipe to the next track. This part includes:
   - Allow you to input what you want to say in text format
   - Translate the Chinese text into English text
   - Generate audio from the English text
   - Split the full audio into small sentence segments
   - Allow users to download the audio files for future practice

2. YouTube Processing: This feature helps learn from YouTube videos by:
   - Download audio from YouTube videos
   - Extract specific segments you want to practice
   - Transcribe the audio to text
   - Split the audio into sentence segments
   - Optionally regenerate the audio using AI voices for clearer pronunciation
   - Package everything for easy practice during commute

## Installation

1. Clone this repository
2. Create the conda environment:
```bash
conda env create -f environment.yml
```

3. Activate the environment:
```bash
conda activate english_learning
```

4. Copy the .env.example to .env and add your OpenAI API key:
```bash
OPENAI_API_KEY=your_api_key_here
```

5. Install `ffmpeg` with `libmp3lame` encoder:
   - Download the `ffmpeg` package from [FFmpeg official website](https://ffmpeg.org/download.html). We will need the `ffmpeg` with LAME support. For Windows, you can get it from [Binary Builds from gyan](https://www.gyan.dev/ffmpeg/builds/)
   - Ensure that the `ffmpeg` binary is accessible in your system's PATH.

6. Run the application:
```bash
streamlit run app.py
```

## Function Description

### Tab 1: Text to Speech
This tab helps convert Chinese text to English audio with sentence-by-sentence segmentation.

UI Elements:
- Text Area: Input box for Chinese text
- Voice Selection: Dropdown menu to select from various TTS voices
  - Available voices: nova, shimmer, echo, onyx, fable, alloy, ash, sage, coral
  - Each voice has its own unique characteristics and tone
- "Translate and Generate Speech" Button: Initiates the processing workflow
  1. Translates Chinese text to English
  2. Generates audio using selected voice
  3. Splits audio into sentence segments
  4. Creates downloadable ZIP file

### Tab 2: YouTube Audio Processor
This tab processes YouTube video audio for language learning practice.

UI Elements:
- YouTube URL Input: Enter the URL of the YouTube video
- Clear Button: Resets the tab and clears downloaded files
- Audio Player: Plays the downloaded YouTube audio
- Time Selection:
  - Start Time (MM:SS): Specify where to start the audio segment
  - End Time (MM:SS): Specify where to end the audio segment
- Processing Method Selection:
  - "Use Original Audio": Splits the extracted audio segment into sentences
  - "Generate New Audio with TTS": Creates new audio using selected voice
- Voice Selection (appears only when TTS is selected):
  - Same voice options as Tab 1
  - Only shown when "Generate New Audio with TTS" is selected
- "Extract and Process Segment" Button: Initiates the processing workflow
  1. Extracts specified segment from YouTube audio
  2. Transcribes the audio to text
  3. Either splits original audio or generates new TTS audio
  4. Creates downloadable ZIP file

## Output

### Tab 1: Text to Speech Output
The application generates a ZIP file containing:
- English translation of the Chinese text (`.txt`)
- Full audio of the translated text (`.mp3`)
- Individual audio files for each sentence (`.mp3`)

### Tab 2: YouTube Processing Output
The application generates a ZIP file containing:
- Transcription of the extracted audio segment (`.txt`)
- Full extracted audio segment (`.mp3`)
- Individual sentence audio files (`.mp3`), either:
  - Split from original audio, or
  - Generated using TTS based on transcription

## Future Idea

- Provide an audio input for the text you want to say
- Provide other language's support on the input and output
- Provide different options for the translation style, like professional presentation, casual communication, office daily communication, etc.
- Fix the bug where the last word of a sentence is assigned to the next sentence in some segmentations
- Improve the user interface for better usability during commutes
- Add functionality to adjust the speed of the generated audio
- Implement a feature to bookmark and replay specific sentences
- Integrate with cloud storage services for easier access to audio files

## References

- [Xiaolai Li's 1000h](https://www.1000h.org)
