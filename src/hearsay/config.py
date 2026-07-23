"""Application configuration: dataclass + JSON persistence."""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass, field
from pathlib import Path

from hearsay.constants import (
    AUDIO_SOURCE_SYSTEM,
    DEFAULT_CPU_COMPUTE,
    DEFAULT_CPU_MODEL,
    DEFAULT_SUMMARIZE_MAX_TOKENS,
    DEFAULT_SUMMARIZE_PROMPT,
    DEFAULT_SUMMARIZE_TEMPERATURE,
    DEFAULT_SUMMARIZE_TIMEOUT_S,
)
from hearsay.utils.paths import get_config_path, get_default_output_dir

log = logging.getLogger(__name__)


@dataclass
class AppConfig:
    """Persistent application settings."""

    # First-run flag
    setup_complete: bool = False

    # Audio
    audio_source: str = AUDIO_SOURCE_SYSTEM
    loopback_device_name: str = ""
    mic_device_name: str = ""

    # Transcription
    model_name: str = DEFAULT_CPU_MODEL
    compute_type: str = DEFAULT_CPU_COMPUTE
    device: str = "cpu"
    language: str = "en"
    vad_filter: bool = True

    # Output
    output_dir: str = field(default_factory=lambda: str(get_default_output_dir()))

    # LLM summarization (OpenAI-compatible endpoint, e.g. a local qwen server)
    summarize_enabled: bool = False
    summarize_base_url: str = ""  # e.g. http://192.168.1.50:8000/v1
    summarize_api_key: str = ""  # often unused for local servers
    summarize_model: str = ""  # e.g. qwen2.5-instruct
    summarize_prompt: str = DEFAULT_SUMMARIZE_PROMPT
    summarize_temperature: float = DEFAULT_SUMMARIZE_TEMPERATURE
    summarize_max_tokens: int = DEFAULT_SUMMARIZE_MAX_TOKENS
    summarize_timeout_s: int = DEFAULT_SUMMARIZE_TIMEOUT_S

    # UI
    show_live_view_on_start: bool = False


class ConfigManager:
    """Load and save AppConfig to JSON in %APPDATA%\\Hearsay."""

    def __init__(self, path: Path | None = None):
        self.path = path or get_config_path()
        self.config = self._load()

    def _load(self) -> AppConfig:
        if self.path.exists():
            try:
                data = json.loads(self.path.read_text(encoding="utf-8"))
                return AppConfig(**{
                    k: v for k, v in data.items()
                    if k in AppConfig.__dataclass_fields__
                })
            except Exception:
                log.warning("Failed to load config, using defaults", exc_info=True)
        return AppConfig()

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(asdict(self.config), indent=2),
            encoding="utf-8",
        )
        log.debug("Config saved to %s", self.path)

    def reset(self) -> None:
        self.config = AppConfig()
        self.save()
