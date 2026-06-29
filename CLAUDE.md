# Hearsay

Windows desktop app that records system audio and/or microphone input and
transcribes it in real-time using a local Whisper model (faster-whisper /
CTranslate2), with optional LLM summarization via any OpenAI-compatible endpoint.
See `README.md` for the full overview and `src/hearsay/` for the package.

## Agent skills

### Issue tracker

Issues and PRDs live in **Linear** (team Photon Ventures, project Tool Chest),
accessed via the Linear MCP server. Every issue gets the `hearsay` label. See
`docs/agents/issue-tracker.md`.

### Triage labels

The five canonical triage roles map 1:1 to Linear labels under the "Agentic State
Machine" parent label. See `docs/agents/triage-labels.md`.

### Domain docs

Single-context: `CONTEXT.md` + `docs/adr/` at the repo root (created lazily by
`/domain-modeling`). See `docs/agents/domain.md`.
