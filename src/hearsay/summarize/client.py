"""Minimal OpenAI-compatible chat-completions client for summarization.

Uses only the standard library (urllib) so there's no extra runtime dependency
and nothing special to bundle. Works against any server that implements the
OpenAI ``/chat/completions`` API -- vLLM, llama.cpp, Ollama (OpenAI mode),
LM Studio, text-generation-webui, etc.
"""

from __future__ import annotations

import json
import logging
import urllib.error
import urllib.request
from dataclasses import dataclass

log = logging.getLogger(__name__)


class SummarizeError(RuntimeError):
    """Raised when summarization fails (connection, HTTP, or response error)."""


@dataclass
class LLMSummarizer:
    """Calls an OpenAI-compatible chat-completions endpoint.

    Args:
        base_url: API base, e.g. ``http://192.168.1.50:8000/v1``. A trailing
            ``/chat/completions`` is appended automatically.
        model: Model name the server expects.
        api_key: Bearer token. Sent only if non-empty (local servers often
            don't need one).
        prompt: System prompt that instructs how to summarize.
        temperature: Sampling temperature.
        max_tokens: Maximum tokens to generate for the summary.
        timeout_s: Per-request timeout in seconds.
    """

    base_url: str
    model: str
    api_key: str = ""
    prompt: str = ""
    temperature: float = 0.3
    max_tokens: int = 2048
    timeout_s: int = 300

    def _endpoint(self) -> str:
        base = self.base_url.strip().rstrip("/")
        if not base:
            raise SummarizeError("No summarization base URL configured.")
        if base.endswith("/chat/completions"):
            return base
        return f"{base}/chat/completions"

    def _post(self, messages: list[dict], max_tokens: int) -> str:
        """POST a chat-completion request and return the assistant message text."""
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": max_tokens,
            "stream": False,
        }
        data = json.dumps(payload).encode("utf-8")

        headers = {"Content-Type": "application/json"}
        if self.api_key.strip():
            headers["Authorization"] = f"Bearer {self.api_key.strip()}"

        req = urllib.request.Request(
            self._endpoint(), data=data, headers=headers, method="POST"
        )

        try:
            with urllib.request.urlopen(req, timeout=self.timeout_s) as resp:
                body = resp.read().decode("utf-8")
        except urllib.error.HTTPError as e:
            detail = ""
            try:
                detail = e.read().decode("utf-8", errors="replace")[:500]
            except Exception:
                pass
            raise SummarizeError(
                f"Server returned HTTP {e.code}: {e.reason}. {detail}".strip()
            ) from e
        except urllib.error.URLError as e:
            raise SummarizeError(f"Could not reach server: {e.reason}") from e
        except (TimeoutError, OSError) as e:
            raise SummarizeError(f"Request failed: {e}") from e

        try:
            parsed = json.loads(body)
            content = parsed["choices"][0]["message"]["content"]
        except (json.JSONDecodeError, KeyError, IndexError, TypeError) as e:
            raise SummarizeError(
                f"Unexpected response format from server: {body[:500]}"
            ) from e

        if not isinstance(content, str) or not content.strip():
            raise SummarizeError("Server returned an empty summary.")
        return content.strip()

    def summarize(self, transcript: str) -> str:
        """Summarize a transcript and return Markdown.

        Raises:
            SummarizeError: on any connection, HTTP, or response problem.
        """
        transcript = transcript.strip()
        if not transcript:
            raise SummarizeError("Transcript is empty; nothing to summarize.")

        log.info(
            "Summarizing transcript (%d chars) via %s [model=%s]",
            len(transcript),
            self.base_url,
            self.model,
        )
        messages = [
            {"role": "system", "content": self.prompt},
            {"role": "user", "content": transcript},
        ]
        summary = self._post(messages, max_tokens=self.max_tokens)
        log.info("Summary generated (%d chars)", len(summary))
        return summary

    def test_connection(self) -> tuple[bool, str]:
        """Send a tiny request to verify the endpoint, model, and auth.

        Returns:
            (ok, message) -- ``message`` is a short human-readable result.
        """
        try:
            reply = self._post(
                [{"role": "user", "content": "Reply with the single word: ok"}],
                max_tokens=16,
            )
        except SummarizeError as e:
            return False, str(e)
        return True, f"Connected. Model replied: {reply[:80]}"
