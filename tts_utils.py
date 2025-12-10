from gtts import gTTS
import io
import streamlit as st

@st.cache_data(show_spinner=False)
def text_to_audio(text):
    """
    Converts text to audio bytes using gTTS.
    Cached to prevent re-generation on every rerun.
    """
    try:
        if not text:
            return None
            
        tts = gTTS(text=text, lang='en')
        # Save to memory buffer
        audio_bytes = io.BytesIO()
        tts.write_to_fp(audio_bytes)
        audio_bytes.seek(0)
        return audio_bytes
    except Exception as e:
        print(f"TTS Error: {e}")
        return None

def autoplay_audio(audio_bytes):
    """
    Helper to create an audio player in Streamlit.
    """
    if audio_bytes:
        st.audio(audio_bytes, format="audio/mp3")
