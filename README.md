# Hearsay

**Windows desktop app that records system audio and/or microphone input and transcribes it in real-time using OpenAI's open-source Whisper model running locally.**

No API calls, no cloud services -- everything runs on your machine.

---

## Features

- **System audio capture** -- record what your speakers play (YouTube, Teams, podcasts, etc.) via WASAPI loopback
- **Microphone capture** -- record from your mic, or mix both sources together
- **Real-time transcription** -- text appears in a live view window as you record
- **Local AI** -- uses [faster-whisper](https://github.com/SYSTRAN/faster-whisper) (CTranslate2), no internet required after model download
- **GPU + CPU** -- auto-detects NVIDIA GPU (via CTranslate2 + `nvidia-smi`, no PyTorch); works on CPU with INT8 quantization
- **LLM summarization** -- optionally hand the finished transcript to any OpenAI-compatible endpoint (a local qwen/llama server, vLLM, Ollama, LM Studio, etc.) for meeting notes
- **Markdown output** -- timestamped `.md` transcripts saved to your chosen directory
- **System tray app** -- runs quietly in the tray, right-click to start/stop recording
- **First-run wizard** -- detects hardware, downloads the right model, configures everything
- **Windows installer** -- appears in Add/Remove Programs, Start Menu shortcut, clean uninstall

## Quick Start

### From source

```bash
# Clone the repo
git clone https://github.com/parkscloud/Hearsay.git
cd hearsay

# Install the package (CPU works out of the box). The editable install puts
# the `hearsay` package on your path so `python -m hearsay` works anywhere.
pip install -e .

# Run
python -m hearsay
```

**For NVIDIA GPU acceleration**, install with the `gpu` extra to also pull in
the CUDA libraries (no PyTorch needed):

```bash
pip install -e ".[gpu]"
```

This pulls in CUDA 12 cuBLAS + cuDNN 9 wheels. You just need a recent NVIDIA
driver (`nvidia-smi` must work). Hearsay detects the GPU at startup and, if the
CUDA libraries are missing at load time, falls back to CPU automatically instead
of failing.

On first launch, the setup wizard walks you through:
1. Hardware detection (GPU vs CPU)
2. Audio source selection
3. Output directory
4. Model download

After setup, Hearsay lives in your system tray. Right-click the icon to start recording.

### Installed version

Download the latest installer from the [Releases](https://github.com/parkscloud/Hearsay/releases) page and run `HearsaySetup.exe`. The app appears in your Start Menu and Add/Remove Programs.

### Silent install (RMM / SCCM / Intune)

```bash
HearsaySetup.exe /VERYSILENT /SUPPRESSMSGBOXES /NORESTART
```

Installs to `C:\Program Files\Hearsay` for all users. Hearsay starts automatically at login. To skip auto-start:

```bash
HearsaySetup.exe /VERYSILENT /SUPPRESSMSGBOXES /NORESTART /TASKS=""
```

Uninstall silently:

```bash
"C:\Program Files\Hearsay\unins000.exe" /VERYSILENT
```

## Usage

1. **Right-click** the tray icon
2. Choose **Start Recording** > **System Audio**, **Microphone**, or **Both**
3. Audio is transcribed in real-time -- open **Live Transcript** to watch
4. **Stop Recording** when done -- a timestamped `.md` file is saved to your output directory

## LLM Summarization

After a recording is transcribed and cleaned, Hearsay can send the transcript to
an OpenAI-compatible chat-completions endpoint and prepend a structured **Summary**
section (overview, key points, decisions, action items, open questions) above the
full transcript. This works with any server that speaks the OpenAI API -- a local
**qwen**/llama server, **vLLM**, **llama.cpp**, **Ollama** (OpenAI mode),
**LM Studio**, etc. Nothing leaves your network if your endpoint is local.

Configure it under **Settings → LLM Summarization**:

| Field | Example | Notes |
|-------|---------|-------|
| Base URL | `http://192.168.1.50:8000/v1` | The API base; `/chat/completions` is appended automatically |
| Model | `qwen2.5-instruct` | Whatever name your server expects |
| API Key | *(blank)* | Usually unused for local servers; sent as a Bearer token if set |
| Summary Prompt | *(editable default)* | The system prompt that shapes the notes |

Use **Test Connection** to verify the endpoint, model, and auth before recording.
Summarization runs on a background thread after the transcript is saved -- if it
fails (server down, wrong model), the transcript is never lost; the error is shown
in the live view and logged. Because the full transcript is sent in one request,
point Hearsay at a model with a large enough context window for long meetings.

## Hardware Requirements

| Setup | Recommended Model | Speed |
|-------|-------------------|-------|
| NVIDIA GPU (6+ GB VRAM) | `turbo` (float16) | ~8x real-time |
| NVIDIA GPU (2–5 GB VRAM) | `small.en` (float16) | ~4x real-time |
| NVIDIA GPU (<2 GB VRAM) | `tiny.en` (float16) | ~6x real-time |
| CPU only | `small.en` (int8) | ~1x real-time |

The setup wizard auto-selects the recommended model from detected VRAM; you can override it any time in **Settings**.

A 1-hour recording transcribes in ~7 min on GPU or ~60 min on CPU.

## Project Structure

```text
src/hearsay/
├── __init__.py              # Version string
├── __main__.py              # Entry point
├── app.py                   # Application orchestrator
├── config.py                # AppConfig + ConfigManager (JSON in %APPDATA%)
├── constants.py             # App name, model table, defaults
├── audio/
│   ├── devices.py           # Enumerate loopback + mic devices
│   ├── recorder.py          # AudioRecorder thread
│   ├── mixer.py             # Mix two audio streams
│   └── resampler.py         # Resample to 16kHz mono float32
├── transcription/
│   ├── gpu_detect.py        # Detect CUDA via CTranslate2 + nvidia-smi (no torch)
│   ├── model_manager.py     # Download and cache Whisper models
│   ├── engine.py            # TranscriptionEngine (faster-whisper, CPU fallback)
│   └── pipeline.py          # TranscriptionPipeline thread
├── summarize/
│   └── client.py            # LLMSummarizer (OpenAI-compatible endpoint)
├── output/
│   ├── formatter.py         # Timestamp formatting
│   └── markdown_writer.py   # Write .md transcripts + summary section
├── ui/
│   ├── tray.py              # System tray icon (pystray)
│   ├── wizard.py            # First-run setup wizard
│   ├── live_view.py         # Live transcript window
│   ├── about_window.py      # About dialog
│   ├── settings_window.py   # Settings editor
│   ├── icons.py             # Programmatic icon generation
│   └── theme.py             # customtkinter theme
└── utils/
    ├── paths.py             # %APPDATA%\Hearsay directories
    ├── logging_setup.py     # File + console logging
    └── threading_utils.py   # StoppableThread, safe_after
```

## Building

### Prerequisites

1. **Python 3.11+**
2. **Project dependencies:** `pip install -r requirements.txt`
3. **PyInstaller:** `pip install pyinstaller`
4. **Inno Setup 6+:** `winget install JRSoftware.InnoSetup`

### Build steps

```bash
# 1. Bundle the app with PyInstaller (output in dist\Hearsay\)
build.bat

# 2. Compile the Windows installer
iscc installer.iss
```

The installer is written to `installer_output\HearsaySetup.exe`.

### Releasing

See [RELEASING.md](RELEASING.md) for instructions on creating GitHub releases with the installer attached. This is a reference for the author and LLM when updating the application.

## Tech Stack

- **Python 3.11+**
- **faster-whisper** -- CTranslate2-based Whisper inference
- **PyAudioWPatch** -- WASAPI loopback recording
- **sounddevice** -- Microphone capture
- **customtkinter** -- Modern UI
- **pystray + Pillow** -- System tray
- **PyInstaller + Inno Setup** -- Build and install

## Contact

Robert Parks<br>
[raparks.com](https://raparks.com/)

## License

MIT -- free to use, modify, and distribute for any purpose (personal or commercial). See [LICENSE](LICENSE) for full text.
