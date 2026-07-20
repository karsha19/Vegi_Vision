import io
import streamlit as st
from translations import t

try:
    from streamlit_mic_recorder import mic_recorder
    MIC_COMPONENT_AVAILABLE = True
except ImportError:
    MIC_COMPONENT_AVAILABLE = False

try:
    import speech_recognition as sr
    SPEECH_RECOGNITION_AVAILABLE = True
except ImportError:
    SPEECH_RECOGNITION_AVAILABLE = False


VOICE_FEATURE_AVAILABLE = MIC_COMPONENT_AVAILABLE and SPEECH_RECOGNITION_AVAILABLE

KNOWN_VEGETABLES = [
    "potato", "spinach", "tomato", "carrot", "broccoli", "cauliflower",
    "bell pepper", "capsicum", "zucchini", "eggplant", "brinjal", "onion",
    "mushroom", "peas", "pumpkin", "okra", "cabbage", "garlic", "ginger",
    "cucumber", "beetroot", "corn", "kale", "lettuce", "sweet potato",
    "green beans", "asparagus", "leek", "radish", "turnip",
]


def _extract_known_vegetables(text: str) -> list:
    """Best-effort extraction of vegetable names mentioned in free speech."""
    lowered = text.lower()
    found = []
    for veg in KNOWN_VEGETABLES:
        if veg in lowered and veg.title() not in found:
            found.append(veg.title())
    return found


def transcribe_wav_bytes(wav_bytes: bytes):
    """Transcribe a WAV audio clip to text.

    Returns (text, error_code). error_code is one of:
      None            -> success, `text` holds the transcript
      "no_audio"      -> the clip was empty / unreadable / silent
      "unclear"       -> speech was detected but not understood
      "service_error" -> the recognition backend could not be reached
      "unknown"       -> any other unexpected failure
    """
    if not SPEECH_RECOGNITION_AVAILABLE:
        return None, "no_audio"

    recognizer = sr.Recognizer()
    try:
        with sr.AudioFile(io.BytesIO(wav_bytes)) as source:
            audio_data = recognizer.record(source)
    except Exception:
        return None, "no_audio"

    try:
        text = recognizer.recognize_google(audio_data)
        if not text or not text.strip():
            return None, "no_audio"
        return text.strip(), None
    except sr.UnknownValueError:
        return None, "unclear"
    except sr.RequestError:
        return None, "service_error"
    except Exception:
        return None, "unknown"


_ERROR_KEY_MAP = {
    "no_audio": "err_no_audio",
    "unclear": "err_unclear",
    "service_error": "err_voice_service",
    "unknown": "err_unclear",
}


def _init_voice_session():
    defaults = {
        "voice_status": "idle",       # idle ,processing , done , error
        "voice_error": None,
        "voice_raw_text": "",         # full recognized sentence, for context
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def _status_badge():
    status = st.session_state.get("voice_status", "idle")
    label_key = {
        "idle": "status_idle",
        "processing": "status_processing",
        "done": "status_done",
        "error": "err_unclear",
    }.get(status, "status_idle")
    st.markdown(
        f'<div class="voice-status voice-status-{status}">'
        f'<span class="status-dot"></span>{t(label_key)}</div>',
        unsafe_allow_html=True,
    )


def reset_voice_state():
    """Called after a recipe is saved/discarded so stale voice context
    (e.g. "healthy", "quick") doesn't leak into a future, unrelated
    generation."""
    st.session_state.voice_raw_text = ""
    st.session_state.voice_status = "idle"
    st.session_state.voice_error = None


def render_voice_input():
    """Renders the mic recorder + status badge + editable recognized-text
    field. Writes results into st.session_state.detected_veg — the same
    field the "Type / Select" tab uses — so voice and typed input flow
    through one identical, already-tested generation pipeline. The full
    sentence is additionally kept in st.session_state.voice_raw_text so
    Gemini can pick up on style/dietary cues ("healthy", "quick", "spicy")
    that aren't literally vegetable names.
    """
    _init_voice_session()

    st.markdown(
        f'<div style="color:var(--text-secondary); font-size:0.85rem; margin-bottom:0.7rem;">'
        f'{t("voice_instructions")}</div>',
        unsafe_allow_html=True,
    )

    if not VOICE_FEATURE_AVAILABLE:
        st.warning(t("err_no_speech_lib"))
        return

    audio = mic_recorder(
        start_prompt=f"🎙️ {t('mic_start_prompt')}",
        stop_prompt=f"⏹️ {t('mic_stop_prompt')}",
        just_once=True,
        use_container_width=True,
        format="wav",
        key="voice_recorder",
    )

    if audio and audio.get("bytes"):
        st.session_state.voice_status = "processing"
        with st.spinner(t("status_processing")):
            text, error = transcribe_wav_bytes(audio["bytes"])

        if error:
            st.session_state.voice_status = "error"
            st.session_state.voice_error = t(_ERROR_KEY_MAP.get(error, "err_unclear"))
        else:
            st.session_state.voice_status = "done"
            st.session_state.voice_error = None
            st.session_state.voice_raw_text = text
            matched = _extract_known_vegetables(text)
            st.session_state.detected_veg = ", ".join(matched) if matched else text

    _status_badge()

    if st.session_state.voice_status == "error" and st.session_state.voice_error:
        st.error(st.session_state.voice_error)
    elif st.session_state.voice_status == "done" and st.session_state.voice_raw_text:
        st.markdown(
            f'<div style="color:var(--text-muted); font-size:0.8rem; margin-top:0.5rem;">🎧 "{st.session_state.voice_raw_text}"</div>',
            unsafe_allow_html=True,
        )

    edited = st.text_input(
        t("label_recognized_text"),
        value=st.session_state.get("detected_veg", ""),
        key="voice_text_edit",
    )
    if edited != st.session_state.get("detected_veg", ""):
        st.session_state.detected_veg = edited
