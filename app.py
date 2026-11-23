"""
galaxyteam51 — 24/7 Cloud Burmese Edge-TTS Server (Hugging Face Spaces)
Provides unlimited free Burmese AI Voices (my-MM-NilarNeural & my-MM-ThihaNeural)
with Speed, Pitch, and full CORS support for mobile & web apps.
"""

import io
import re
from fastapi import FastAPI, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
import edge_tts

app = FastAPI(title="galaxyteam51 Burmese Edge-TTS Cloud Server")

# Allow requests from Netlify, Gemini Preview, mobile browsers, and localhost
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


def parse_signed_int(raw_val: str, min_v: int, max_v: int) -> int:
    """Extract an integer from strings like '12', '+12%', '-18Hz', etc. and clamp it."""
    match = re.search(r"-?\d+", str(raw_val or "0"))
    val = int(match.group(0)) if match else 0
    return max(min_v, min(max_v, val))


@app.get("/")
@app.get("/health")
async def health_check():
    """Health check endpoint used by galaxyteam51 to verify Online status."""
    return {
        "status": "ok",
        "service": "galaxyteam51-cloud-edge-tts",
        "voices": ["my-MM-NilarNeural", "my-MM-ThihaNeural"],
        "features": ["tts"],
    }


@app.post("/tts")
async def generate_tts(
    text: str = Form(...),
    voice: str = Form("my-MM-NilarNeural"),
    speed: str = Form("0"),
    pitch: str = Form("0"),
):
    """Synthesize Burmese speech via Microsoft Edge-TTS and stream MP3 bytes."""
    cleaned_text = (text or "").strip()
    if not cleaned_text:
        raise HTTPException(status_code=400, detail="Text cannot be empty")

    # Normalize voice, rate (+X% / -X%), and pitch (+XHz / -XHz)
    selected_voice = (voice or "my-MM-NilarNeural").strip()
    spd = parse_signed_int(speed, -50, 100)
    pit = parse_signed_int(pitch, -50, 50)

    rate_str = f"+{spd}%" if spd >= 0 else f"{spd}%"
    pitch_str = f"+{pit}Hz" if pit >= 0 else f"{pit}Hz"

    try:
        communicate = edge_tts.Communicate(
            text=cleaned_text,
            voice=selected_voice,
            rate=rate_str,
            pitch=pitch_str,
        )
        audio_buffer = io.BytesIO()
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_buffer.write(chunk["data"])

        mp3_bytes = audio_buffer.getvalue()
        if not mp3_bytes:
            raise HTTPException(status_code=502, detail="Edge-TTS returned empty audio")

        return Response(
            content=mp3_bytes,
            media_type="audio/mpeg",
            headers={"Cache-Control": "no-store"},
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"TTS synthesis failed: {exc}")
