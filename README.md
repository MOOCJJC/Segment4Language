# English Learning Assistant

An application to help with English learning through AI translation and text-to-speech.

## Introduction

When using Xiaolai Li's [1000h](https://www.1000h.org) or Enjoy app, I wanted to utilize my commute time to practice English, as I have at least 2.5 hours of commute every working day. However, I encountered an issue: the Enjoy app's mobile version is not very user-friendly for long-commute drivers. When practicing, I generally want to repeat the same sentence multiple times. On the Enjoy app, I need to manually select the section of the text I want to practice, which is not feasible while driving.

To solve this, I created an app that segments the full audio of a paragraph into individual sentences. This way, while driving, I can simply open the audio file and keep repeating the same sentence. To switch sentences, I just need to swipe to the next track. This app includes the basic functions of the Enjoy app:

- Allow you to input what you want to say in text format
- Translate the Chinese text into English text
- Generate audio from the English text
- Split the full audio into small sentence segments
- Allow users to download the audio files for future practice

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
   - Download the `ffmpeg` package from [FFmpeg official website](https://ffmpeg.org/download.html) or use a package manager like `conda` or `brew`.
   - Ensure that the `ffmpeg` binary is accessible in your system's PATH.

6. Run the application:
```bash
streamlit run app.py
```

## Output

The application generates a zip file containing:
- The English translation of the input Chinese text in a `.txt` file.
- The full audio of the translated text in a `.mp3` file.
- Segmented audio files for each sentence in the translated text, each in a `.mp3` file.

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
