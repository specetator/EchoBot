# EchoBot Fork Patch Package

This package contains the local changes made on top of `KdaiP/EchoBot` to:

- fix Python 3.11 startup compatibility for Live2D asset URLs;
- connect a local Shinku GPT-SoVITS voice through EchoBot's OpenAI-compatible TTS provider;
- make the WebUI prefer the server configured TTS provider over stale browser localStorage;
- make TTS read only the Japanese original text when replies include both Japanese and Chinese.

No `.env` file or API key is included.

## Files

Copy these files into the same paths in your fork:

```text
echobot/app/services/web_console/live2d/catalog.py
echobot/app/web/features/tts/options.js
echobot/app/web/features/tts/text.js
shinku_tts_adapter.py
run-echobot.cmd
run-shinku-tts-adapter.cmd
stop-echobot-local.cmd
```

Optional role prompt example:

```text
examples/default-ja-zh-role.md
```

You can copy it to:

```text
.echobot/roles/default.md
```

## Environment Example

Add or update these lines in your local `.env`.

```env
ECHOBOT_TTS_PROVIDER=openai-compatible
ECHOBOT_TTS_OPENAI_API_KEY=EMPTY
ECHOBOT_TTS_OPENAI_MODEL=shinku_gpt_sovits
ECHOBOT_TTS_OPENAI_BASE_URL=http://127.0.0.1:8091/v1
ECHOBOT_TTS_OPENAI_TIMEOUT=120
ECHOBOT_TTS_OPENAI_DEFAULT_VOICE=shinku
ECHOBOT_TTS_OPENAI_RESPONSE_FORMAT=wav
ECHOBOT_TTS_OPENAI_VOICES=shinku
```

Do not commit `.env`.

## Runtime Chain

```text
EchoBot WebUI
  -> EchoBot FastAPI :8000
  -> shinku_tts_adapter FastAPI :8091 /v1/audio/speech
  -> GPT-SoVITS FastAPI :9880 /tts
  -> Shinku GPT-SoVITS model
```

The adapter exists because EchoBot already supports OpenAI-compatible Speech API, while GPT-SoVITS exposes its own `/tts` request format.

## Startup Order

Start your GPT-SoVITS Shinku API first, for example:

```bat
F:\AI_audio\GPT-SOVITS\GPT-SoVITS-v2pro-20250604\start_shinku_api.bat
```

Then start the adapter:

```bat
run-shinku-tts-adapter.cmd
```

Then start EchoBot:

```bat
run-echobot.cmd
```

Stop EchoBot and the adapter:

```bat
stop-echobot-local.cmd
```

## Shinku Adapter Defaults

`shinku_tts_adapter.py` defaults to:

```text
GPT-SoVITS URL: http://127.0.0.1:9880/tts
Voice name: shinku
Text language: ja
Response format: wav
```

The default reference audio is:

```text
F:\AI_audio\shinku_selected_10mb\output\deliverables\reference_shinku_00003390.wav
```

Override these with environment variables before starting the adapter:

```env
SHINKU_GPT_SOVITS_TTS_URL=http://127.0.0.1:9880/tts
SHINKU_REF_AUDIO_PATH=...
SHINKU_PROMPT_TEXT=...
SHINKU_PROMPT_LANG=ja
SHINKU_TEXT_LANG=ja
SHINKU_TEXT_SPLIT_METHOD=cut5
SHINKU_TTS_TIMEOUT=120
```

## Bilingual Reply Format

The optional role prompt asks the assistant to reply like this:

```text
原文（日语）：
今日はいい天気ですね。お手伝いできて嬉しいにゃ。

翻译（中文）：
今天天气真好。能帮上忙我很开心喵。
```

`echobot/app/web/features/tts/text.js` extracts only the Japanese original block for speech synthesis, so the Chinese translation is displayed but not read aloud.

## Validation Checklist

After starting all services:

```text
http://127.0.0.1:9880/docs
http://127.0.0.1:8091/v1/audio/voices
http://127.0.0.1:8000/api/web/config
http://127.0.0.1:8000/web
```

Expected EchoBot config:

```text
TTS provider: openai-compatible
Voice: shinku
Provider state: ready
```
