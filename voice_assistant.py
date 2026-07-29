import hashlib
import io
import os
import tempfile
import streamlit as st
import streamlit.components.v1 as components
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



_LIVE_MIC_HTML = r"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8" />
<style>
  :root { color-scheme: light dark; }
  * { box-sizing: border-box; }
  body {
    margin: 0;
    font-family: 'Manrope', -apple-system, BlinkMacSystemFont, sans-serif;
    background: transparent;
  }
  .wrap { display: flex; flex-direction: column; gap: 8px; padding: 2px 0; }
  .mic-btn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    padding: 10px 18px;
    border-radius: 14px;
    border: none;
    cursor: pointer;
    font-weight: 700;
    font-size: 14px;
    background: #4d6b3d;
    color: #ffffff;
    transition: transform 0.15s ease, box-shadow 0.15s ease, background 0.15s ease;
    box-shadow: 0 6px 16px rgba(77, 107, 61, 0.25);
  }
  .mic-btn:hover { transform: translateY(-1px); background: #3a5230; }
  .mic-btn:disabled { opacity: 0.5; cursor: not-allowed; transform: none; }
  .mic-btn.recording {
    background: #b3402f;
    animation: mic-pulse 1.1s ease-in-out infinite;
  }
  @keyframes mic-pulse {
    0%   { box-shadow: 0 0 0 0 rgba(179, 64, 47, 0.5); }
    70%  { box-shadow: 0 0 0 12px rgba(179, 64, 47, 0); }
    100% { box-shadow: 0 0 0 0 rgba(179, 64, 47, 0); }
  }
  .transcript-box {
    width: 100%;
    padding: 11px 14px;
    border-radius: 12px;
    border: 1px solid #cdc2a3;
    font-size: 14px;
    font-family: inherit;
    background: #ffffff;
    color: #23281f;
  }
  .transcript-box:focus { outline: 2px solid #4d6b3d; outline-offset: 1px; }
  .hint {
    font-size: 12px;
    color: #6b6a5e;
    min-height: 14px;
  }
  .dot {
    width: 7px; height: 7px; border-radius: 50%;
    background: currentColor; display: inline-block;
  }
</style>
</head>
<body>
  <div class="wrap">
    <button id="micBtn" class="mic-btn" type="button">
      <span class="dot" id="micDot"></span>
      <span id="micLabel">Start Speaking</span>
    </button>
    <input id="transcriptBox" class="transcript-box" type="text" autocomplete="off" />
    <div class="hint" id="hint"></div>
  </div>

<script>
(function () {
  var micBtn = document.getElementById('micBtn');
  var micLabel = document.getElementById('micLabel');
  var box = document.getElementById('transcriptBox');
  var hint = document.getElementById('hint');

  var recognizing = false;
  var recognition = null;
  var finalTranscript = "";
  var initialized = false;
  var labels = {};

  function sendValue(value) {
    window.parent.postMessage({
      isStreamlitMessage: true,
      type: "streamlit:setComponentValue",
      value: value,
      dataType: "json"
    }, "*");
  }

  function setFrameHeight() {
    var height = document.documentElement.scrollHeight;
    window.parent.postMessage({
      isStreamlitMessage: true,
      type: "streamlit:setFrameHeight",
      height: height
    }, "*");
  }

  function onMessage(event) {
    var data = event.data;
    if (!data || !data.isStreamlitMessage) return;
    if (data.type !== "streamlit:render") return;

    var args = data.args || {};
    labels = args.labels || {};

    if (!initialized) {
      box.value = args.value || "";
      box.placeholder = args.placeholder || "";
      applyLabels();
      initialized = true;
    }
    setFrameHeight();
  }

  function applyLabels() {
    micLabel.textContent = recognizing
      ? (labels.listening || "Listening... (tap to stop)")
      : (labels.start || "Start Speaking");
  }

  window.addEventListener("message", onMessage);
  window.parent.postMessage({ isStreamlitMessage: true, type: "streamlit:componentReady", apiVersion: 1 }, "*");
  setFrameHeight();

  var SpeechRecognitionImpl = window.SpeechRecognition || window.webkitSpeechRecognition;

  if (!SpeechRecognitionImpl) {
    micBtn.disabled = true;
    hint.textContent = (labels.unsupported ||
      "Live voice typing needs Chrome or Edge on this device. You can still type here directly.");
  } else {
    recognition = new SpeechRecognitionImpl();
    recognition.continuous = true;
    recognition.interimResults = true;

    recognition.onstart = function () {
      recognizing = true;
      micBtn.classList.add("recording");
      applyLabels();
      hint.textContent = labels.listening_hint || "Listening — speak now.";
    };

    recognition.onerror = function (e) {
      hint.textContent = (labels.error_prefix || "Mic error:") + " " + e.error;
    };

    recognition.onend = function () {
      recognizing = false;
      micBtn.classList.remove("recording");
      applyLabels();
      hint.textContent = "";
      sendValue(box.value);
    };

    recognition.onresult = function (event) {
      var interim = "";
      for (var i = event.resultIndex; i < event.results.length; i++) {
        var piece = event.results[i][0].transcript;
        if (event.results[i].isFinal) {
          finalTranscript += piece + " ";
        } else {
          interim += piece;
        }
      }
      box.value = (finalTranscript + interim).trim();
      setFrameHeight();
      if (finalTranscript) {
        sendValue(box.value);
      }
    };

    micBtn.addEventListener("click", function () {
      if (recognizing) {
        recognition.stop();
      } else {
        finalTranscript = box.value ? box.value + " " : "";
        try {
          recognition.start();
        } catch (e) {
          hint.textContent = (labels.error_prefix || "Mic error:") + " " + e.message;
        }
      }
    });
  }

  box.addEventListener("change", function () {
    finalTranscript = box.value;
    sendValue(box.value);
  });
  box.addEventListener("input", function () {
    setFrameHeight();
  });
})();
</script>
</body>
</html>
"""


def _materialized_component_dir() -> str:
    """Writes _LIVE_MIC_HTML out to a stable temp path and returns the
    directory, creating/refreshing it only if the content actually
    changed. This is the one bit of on-disk state the live component
    needs (Streamlit's component loader requires a real file to serve) —
    everything a developer touches still lives in this .py module."""
    content_hash = hashlib.sha256(_LIVE_MIC_HTML.encode("utf-8")).hexdigest()[:12]
    component_dir = os.path.join(tempfile.gettempdir(), f"vegivision_live_mic_{content_hash}")
    index_path = os.path.join(component_dir, "index.html")
    if not os.path.exists(index_path):
        os.makedirs(component_dir, exist_ok=True)
        with open(index_path, "w", encoding="utf-8") as f:
            f.write(_LIVE_MIC_HTML)
    return component_dir


_live_mic_component = components.declare_component("live_mic", path=_materialized_component_dir())


def live_mic_input(value: str = "", placeholder: str = "", labels: dict = None, key: str = None) -> str:
    """Renders the live speech-to-text box. Returns the current transcript
    (updated as speech is recognized, or when the user edits it by hand)."""
    result = _live_mic_component(
        value=value,
        placeholder=placeholder,
        labels=labels or {},
        key=key,
        default=value,
    )
    return result if result is not None else value


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
        "voice_status": "idle",       # idle | processing | done | error
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
    """Renders the voice input UI. Two modes, both writing into
    st.session_state.detected_veg — the same field the "Type / Select" tab
    uses — so voice and typed input flow through one identical, already-
    tested generation pipeline:

      1. Live typing (default): the browser's own speech recognition
         (Chrome/Edge) transcribes continuously and types straight into an
         editable box as the user talks — no "stop and wait" step.
      2. Record & Transcribe (fallback): works in any browser. Record a
         clip, then it's sent to a server-side speech-to-text call once
         you stop. Used automatically as the visible option when the live
         mode's browser support is unavailable, and always selectable.

    The full recognized sentence is additionally kept in
    st.session_state.voice_raw_text so Gemini can pick up on style/dietary
    cues ("healthy", "quick", "spicy") that aren't literally vegetable
    names.
    """
    _init_voice_session()

    st.markdown(
        f'<div style="color:var(--text-secondary); font-size:0.85rem; margin-bottom:0.7rem;">'
        f'{t("voice_instructions")}</div>',
        unsafe_allow_html=True,
    )

    mode = st.radio(
        t("voice_mode_label"),
        options=["live", "record"],
        format_func=lambda m: t("voice_mode_live") if m == "live" else t("voice_mode_record"),
        horizontal=True,
        key="voice_mode",
        label_visibility="collapsed",
    )

    if mode == "live":
        _render_live_mode()
    else:
        _render_record_mode()

    
    edited = st.text_input(
        t("label_recognized_text"),
        value=st.session_state.get("detected_veg", ""),
    )
    if edited != st.session_state.get("detected_veg", ""):
        st.session_state.detected_veg = edited
        st.session_state.voice_raw_text = edited


def _render_live_mode():
    """Type-as-you-speak using the browser's native SpeechRecognition."""
    transcript = live_mic_input(
        value=st.session_state.get("detected_veg", ""),
        placeholder=t("placeholder_manual_veg"),
        labels={
            "start": t("mic_start_prompt"),
            "listening": t("status_listening_live"),
            "listening_hint": t("voice_listening_hint"),
            "unsupported": t("err_live_unsupported"),
            "error_prefix": t("err_mic_prefix"),
        },
        key="live_mic",
    )
    if transcript != st.session_state.get("detected_veg", ""):
        st.session_state.detected_veg = transcript
        st.session_state.voice_raw_text = transcript
        st.session_state.voice_status = "done" if transcript else "idle"


def _render_record_mode():
    """Record a clip, then transcribe it once recording stops (works in
    any browser, including ones without live SpeechRecognition support)."""
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
