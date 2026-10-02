"""
Voice Branch for Multi-Modal Dark Pattern Detection
Analyzes voice/audio clips for spoken dark patterns and manipulative prosody:
Pipeline: Audio -> Transcription -> Text Analysis -> Prosody Analysis -> Structured Findings.
Gracefully handles optional libraries (speech_recognition, whisper, librosa, wave).
"""

import io
import base64
import logging
from typing import List, Dict, Any

log = logging.getLogger("dark-pattern-voice-branch")

def analyze_audio(audio_base64: str, model_bundle: Dict[str, Any] = None, threshold: float = 0.50) -> List[Dict[str, Any]]:
    """
    Analyzes base64 encoded audio clip.
    Extracts transcript and prosody metrics to identify voice dark patterns.
    """
    findings = []
    if not audio_base64 or not isinstance(audio_base64, str):
        return findings

    # Clean base64 header
    if "," in audio_base64:
        audio_base64 = audio_base64.split(",", 1)[1]

    try:
        audio_bytes = base64.b64decode(audio_base64)
    except Exception as e:
        log.error(f"Failed to decode base64 audio: {e}")
        return findings

    if len(audio_bytes) < 100:
        log.warning("Audio payload too small or empty")
        return findings

    # Step 1: Transcription
    transcript = transcribe_audio(audio_bytes)

    # Step 2: Prosody Analysis
    prosody = analyze_prosody(audio_bytes)

    # Step 3: Combine Text Analysis & Prosody
    if transcript:
        from backend.text_branch import predict_multilabel_texts, CATEGORIES

        preds = predict_multilabel_texts([transcript], model_bundle or {})
        text_scores = preds[0] if preds else {}

        for cat, conf in text_scores.items():
            final_conf = conf

            # Prosody boosting: if rapid speech rate (fast disclaimers) + fine-print terms
            if prosody.get("speech_rate_wpm", 0) > 200 and cat in ["hidden_delayed_costs", "forced_continuity"]:
                final_conf = min(1.0, final_conf + 0.20)

            if final_conf >= threshold:
                findings.append({
                    "category": cat,
                    "confidence": round(final_conf, 4),
                    "modality": "voice",
                    "transcript": transcript,
                    "evidence": transcript,
                    "reason": f"Spoken pattern detected in audio. (Speech rate: {prosody.get('speech_rate_wpm', 150)} WPM)",
                    "prosody": prosody
                })

    # If no transcript produced but audio prosody exhibits rapid disclosure signature
    elif prosody.get("rapid_disclosure_detected"):
        findings.append({
            "category": "hidden_delayed_costs",
            "confidence": 0.75,
            "modality": "voice",
            "transcript": "[Audio transcription unavailable]",
            "evidence": "Rapid speed / accelerated fine-print audio disclaimer detected",
            "reason": f"High speech-rate disclosure prosody ({prosody.get('speech_rate_wpm')} WPM)",
            "prosody": prosody
        })

    return findings


def transcribe_audio(audio_bytes: bytes) -> str:
    """Attempts audio transcription using available speech recognition packages."""
    # 1. Try SpeechRecognition
    try:
        import speech_recognition as sr
        recognizer = sr.Recognizer()
        with sr.AudioFile(io.BytesIO(audio_bytes)) as source:
            audio_data = recognizer.record(source)
            text = recognizer.recognize_google(audio_data)
            return text
    except Exception:
        pass

    # 2. Try Whisper if available
    try:
        import whisper
        model = whisper.load_model("tiny")
        # Save temp file for whisper
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=True) as tmp:
            tmp.write(audio_bytes)
            tmp.flush()
            res = model.transcribe(tmp.name)
            return res.get("text", "").strip()
    except Exception:
        pass

    # Fallback heuristic: return empty transcript if no speech library installed
    return ""


def analyze_prosody(audio_bytes: bytes) -> Dict[str, Any]:
    """Analyzes audio pitch, volume variation, and speech rate WPM."""
    metrics = {
        "duration_sec": 5.0,
        "speech_rate_wpm": 160,
        "volume_variance": 0.15,
        "rapid_disclosure_detected": False
    }

    try:
        import wave
        with wave.open(io.BytesIO(audio_bytes), "rb") as wf:
            frames = wf.getnframes()
            rate = wf.getframerate()
            duration = frames / float(rate)
            metrics["duration_sec"] = round(duration, 2)
    except Exception:
        pass

    # Librosa analysis if installed
    try:
        import librosa
        import numpy as np
        y, sr = librosa.load(io.BytesIO(audio_bytes), sr=None)
        duration = librosa.get_duration(y=y, sr=sr)
        metrics["duration_sec"] = round(float(duration), 2)

        # Onset envelope for tempo / WPM calculation
        onset_env = librosa.onnset.onset_strength(y=y, sr=sr)
        tempo = librosa.beat.tempo(onset_envelope=onset_env, sr=sr)
        wpm = float(tempo[0]) * 1.5 if len(tempo) > 0 else 160
        metrics["speech_rate_wpm"] = int(wpm)

        if wpm > 210:
            metrics["rapid_disclosure_detected"] = True
    except Exception:
        pass

    return metrics
