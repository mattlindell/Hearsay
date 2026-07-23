"""Application constants and model configuration."""

APP_NAME = "Hearsay"
APP_VERSION = "1.1.5"
APP_AUTHOR = "Hearsay"

# Audio settings
SAMPLE_RATE = 16000  # Whisper expects 16kHz
CHANNELS = 1  # Whisper expects mono
CHUNK_DURATION_S = 30  # Whisper's native context window
OVERLAP_DURATION_S = 1  # Overlap between chunks to prevent word splitting
AUDIO_DTYPE = "float32"

# Model table: name -> (parameters, vram_gb, english_only)
MODEL_TABLE = {
    "tiny": ("39M", 1, False),
    "tiny.en": ("39M", 1, True),
    "base": ("74M", 1, False),
    "base.en": ("74M", 1, True),
    "small": ("244M", 2, False),
    "small.en": ("244M", 2, True),
    "medium": ("769M", 5, False),
    "medium.en": ("769M", 5, True),
    "large-v3": ("1550M", 10, False),
    "turbo": ("809M", 6, False),
}

# Default model recommendations
DEFAULT_GPU_MODEL = "turbo"
DEFAULT_CPU_MODEL = "small.en"
DEFAULT_GPU_COMPUTE = "float16"
DEFAULT_CPU_COMPUTE = "int8"

# Audio source options
AUDIO_SOURCE_SYSTEM = "system"
AUDIO_SOURCE_MIC = "microphone"
AUDIO_SOURCE_BOTH = "both"

# Labels used in transcripts / live view for each source
SOURCE_LABELS = {
    AUDIO_SOURCE_SYSTEM: "Remote",
    AUDIO_SOURCE_MIC: "Local",
}

# Windows quieter than this RMS are treated as silence and not transcribed
SILENCE_RMS_FLOOR = 1e-4

# Silent-capture watchdog: if a session captures no audio (device muted,
# unplugged, blocked, or wedged) for this long, warn the user loudly but keep
# recording so it recovers if the device comes back. Re-warn periodically while
# still silent. A live microphone in a quiet room reads well above
# SILENCE_RMS_FLOOR, so these fire on genuinely dead capture, not normal pauses.
SILENCE_ALERT_S = 60      # seconds of no captured audio before the first alert
SILENCE_REALERT_S = 120   # re-alert interval while capture stays silent

# Tray icon colors (RGB)
ICON_COLOR_IDLE = (100, 100, 100)       # Gray
ICON_COLOR_RECORDING = (220, 50, 50)    # Red
ICON_COLOR_PROCESSING = (50, 150, 220)  # Blue

# Transcript formatting
PARAGRAPH_GAP_S = 2.0  # Silence gap (seconds) that triggers a paragraph break

# LLM summarization (OpenAI-compatible chat completions endpoint)
DEFAULT_SUMMARIZE_TEMPERATURE = 0.3
DEFAULT_SUMMARIZE_MAX_TOKENS = 2048
DEFAULT_SUMMARIZE_TIMEOUT_S = 300  # local models on big transcripts can be slow
DEFAULT_SUMMARIZE_PROMPT = (
    "You are an expert meeting-notes assistant. You are given the raw transcript "
    "of a recorded meeting or conversation produced by automatic speech "
    "recognition, so it may contain transcription errors, filler words, and no "
    "speaker labels. Produce clear, well-structured Markdown notes with these "
    "sections, omitting any that do not apply:\n\n"
    "## Summary\nA concise 2-4 sentence overview of what was discussed.\n\n"
    "## Key Points\nThe most important points as a bulleted list.\n\n"
    "## Decisions\nAny decisions that were made.\n\n"
    "## Action Items\nConcrete next steps as a checklist (`- [ ]`), with the "
    "responsible person in **bold** when it can be inferred.\n\n"
    "## Open Questions\nUnresolved questions or follow-ups.\n\n"
    "Be faithful to the transcript. Do not invent details. If something is "
    "unclear, say so rather than guessing."
)

# UI
LIVE_VIEW_POLL_MS = 250  # Poll transcript queue every 250ms
