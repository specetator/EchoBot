from __future__ import annotations

import os
import re
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field


GPT_SOVITS_TTS_URL = os.environ.get(
    "SHINKU_GPT_SOVITS_TTS_URL",
    "http://127.0.0.1:9880/tts",
)
REF_AUDIO_PATH = os.environ.get(
    "SHINKU_REF_AUDIO_PATH",
    r"F:\AI_audio\shinku_selected_10mb\output\deliverables\reference_shinku_00003390.wav",
)
PROMPT_TEXT = os.environ.get(
    "SHINKU_PROMPT_TEXT",
    "以前は毎日のように見る夢の光景を探して 幽魔はいろいろな世界へ行っていたじゃないか",
)
PROMPT_LANG = os.environ.get("SHINKU_PROMPT_LANG", "ja")
DEFAULT_TEXT_LANG = os.environ.get("SHINKU_TEXT_LANG", "ja")
TEXT_SPLIT_METHOD = os.environ.get("SHINKU_TEXT_SPLIT_METHOD", "cut5")
TIMEOUT_SECONDS = float(os.environ.get("SHINKU_TTS_TIMEOUT", "120"))


app = FastAPI(title="Shinku GPT-SoVITS OpenAI TTS Adapter")


class SpeechRequest(BaseModel):
    model: str = "shinku_gpt_sovits"
    input: str
    voice: str = "shinku"
    response_format: str = "wav"
    speed: float | None = None
    extra_body: dict[str, Any] | None = Field(default=None)


@app.get("/v1/audio/voices")
async def list_voices() -> dict[str, list[dict[str, str]]]:
    return {
        "voices": [
            {
                "id": "shinku",
                "name": "shinku",
                "short_name": "shinku",
                "display_name": "Shinku GPT-SoVITS",
                "language": "ja",
            },
        ],
    }


@app.post("/v1/audio/speech")
async def create_speech(request: SpeechRequest) -> Response:
    text = request.input.strip()
    if not text:
        raise HTTPException(status_code=400, detail="input must not be empty")

    response_format = _normalize_response_format(request.response_format)
    payload: dict[str, Any] = {
        "text": text,
        "text_lang": _text_lang(text, request.extra_body),
        "ref_audio_path": _extra_text(request.extra_body, "ref_audio_path", REF_AUDIO_PATH),
        "prompt_text": _extra_text(request.extra_body, "prompt_text", PROMPT_TEXT),
        "prompt_lang": _extra_text(request.extra_body, "prompt_lang", PROMPT_LANG),
        "text_split_method": _extra_text(request.extra_body, "text_split_method", TEXT_SPLIT_METHOD),
        "batch_size": int(_extra_number(request.extra_body, "batch_size", 1)),
        "media_type": response_format,
        "streaming_mode": False,
    }

    if request.speed is not None:
        payload["speed_factor"] = max(0.5, min(float(request.speed), 2.0))

    for key in (
        "top_k",
        "top_p",
        "temperature",
        "batch_threshold",
        "split_bucket",
        "fragment_interval",
        "seed",
        "parallel_infer",
        "repetition_penalty",
        "sample_steps",
        "super_sampling",
    ):
        if request.extra_body and key in request.extra_body:
            payload[key] = request.extra_body[key]

    try:
        async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS) as client:
            upstream = await client.post(GPT_SOVITS_TTS_URL, json=payload)
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"GPT-SoVITS TTS request failed: {exc}",
        ) from exc

    if upstream.status_code >= 400:
        raise HTTPException(
            status_code=upstream.status_code,
            detail=upstream.text,
        )

    content_type = _content_type(response_format)
    return Response(content=upstream.content, media_type=content_type)


def _normalize_response_format(value: str) -> str:
    normalized = str(value or "wav").strip().lower()
    if normalized in {"wav", "ogg", "aac"}:
        return normalized
    return "wav"


def _content_type(response_format: str) -> str:
    return {
        "wav": "audio/wav",
        "ogg": "audio/ogg",
        "aac": "audio/aac",
    }.get(response_format, "audio/wav")


def _text_lang(text: str, extra_body: dict[str, Any] | None) -> str:
    configured = _extra_text(extra_body, "text_lang", DEFAULT_TEXT_LANG).lower()
    if configured and configured != "auto":
        return configured
    if re.search(r"[\u3040-\u30ff]", text):
        return "ja"
    if re.search(r"[\u4e00-\u9fff]", text):
        return "zh"
    return "en"


def _extra_text(extra_body: dict[str, Any] | None, key: str, default: str) -> str:
    if extra_body and key in extra_body:
        value = str(extra_body[key]).strip()
        if value:
            return value
    return default


def _extra_number(extra_body: dict[str, Any] | None, key: str, default: float) -> float:
    if not extra_body or key not in extra_body:
        return default
    try:
        return float(extra_body[key])
    except (TypeError, ValueError):
        return default
