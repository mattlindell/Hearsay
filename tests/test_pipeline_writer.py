"""Fast logic tests for the transcription pipeline and markdown writer.

Runs against a stub engine — no audio hardware, no Whisper model, finishes
in seconds:

    python tests/test_pipeline_writer.py

Covers: per-source overlap dedup, fuzzy echo guard, segment merge/sort,
source-label placement (switches, single-source, gap paragraphs),
post-process label preservation, and empty-session output.
"""
import queue
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import numpy as np

from hearsay.audio.devices import AudioDevice, match_device_by_name
from hearsay.audio.recorder import AudioChunk, _SilenceMonitor, _SourceBuffer
from hearsay.constants import AUDIO_SOURCE_MIC, AUDIO_SOURCE_SYSTEM
from hearsay.output.markdown_writer import MarkdownWriter
from hearsay.transcription.engine import TranscriptionResult
from hearsay.transcription.pipeline import TranscriptionPipeline

OUT = Path(tempfile.mkdtemp(prefix="hearsay_test_"))

FAILURES = []


def check(cond, msg):
    tag = "PASS" if cond else "FAIL"
    print(f"  [{tag}] {msg}")
    if not cond:
        FAILURES.append(msg)


class FakeEngine:
    """Returns canned results keyed by id() of the audio array."""

    def __init__(self):
        self.responses = {}

    def register(self, arr, text, segments):
        self.responses[id(arr)] = (text, segments)
        return arr

    def transcribe(self, audio, chunk_index=0):
        text, segments = self.responses[id(audio)]
        return TranscriptionResult(
            text=text,
            segments=[dict(s) for s in segments],
            language="en",
            language_probability=0.99,
            chunk_index=chunk_index,
        )


_counter = 0


def new_arr():
    """Distinct dummy audio array (identity is what matters, not content)."""
    global _counter
    _counter += 1
    return np.random.default_rng(_counter).random(16000).astype(np.float32)


def run_windows(engine, windows):
    """Feed AudioChunks through a pipeline synchronously, return results."""
    aq, tq = queue.Queue(), queue.Queue()
    pipe = TranscriptionPipeline(audio_queue=aq, transcript_queue=tq, engine=engine)
    for w in windows:
        pipe._process_window(w)
    results = []
    while not tq.empty():
        results.append(tq.get_nowait())
    return results


print("== _SourceBuffer overlap/tail behavior ==")
buf = _SourceBuffer("system", overlap_samples=16000)
buf.append(np.ones(32000, dtype=np.float32))
cut1 = buf.cut()
check(len(cut1) == 32000, f"first cut returns all audio ({len(cut1)})")
buf.append(np.ones(16000, dtype=np.float32) * 0.5)
cut2 = buf.cut()
check(len(cut2) == 32000, f"second cut = 1s tail + 1s new ({len(cut2)})")
check(cut2[0] == 1.0 and cut2[-1] == 0.5, "tail precedes new audio")
cut3 = buf.cut()
check(len(cut3) == 0, "cut with no new audio returns empty (no tail re-emit)")

print("== Both-mode conversation ==")
eng = FakeEngine()
w0_sys = eng.register(new_arr(), "Hello this is the remote speaker talking now.",
                      [{"start": 0.5, "end": 3.0, "text": "Hello this is the remote speaker talking now."}])
w0_mic = eng.register(new_arr(), "Hi there this is the local person.",
                      [{"start": 3.5, "end": 6.0, "text": "Hi there this is the local person."}])
w1_sys = eng.register(new_arr(), "talking now. And here is more remote speech.",
                      [{"start": 0.2, "end": 1.0, "text": "talking now."},
                       {"start": 1.2, "end": 4.0, "text": "And here is more remote speech."}])
w1_mic = eng.register(new_arr(), "And here is more remote speech. Yes I agree completely with that.",
                      [{"start": 1.3, "end": 4.1, "text": "And here is more remote speech."},
                       {"start": 5.0, "end": 8.0, "text": "Yes I agree completely with that."}])
w2_mic = eng.register(new_arr(), "Now some more local talk after a pause.",
                      [{"start": 5.0, "end": 8.0, "text": "Now some more local talk after a pause."}])
w3_sys = eng.register(new_arr(), "Remote is back um talking again.",
                      [{"start": 1.0, "end": 3.0, "text": "Remote is back um talking again."}])
w4_sys = eng.register(new_arr(), "The quick brown fox jumps over the lazy dog today.",
                      [{"start": 0.5, "end": 4.0, "text": "The quick brown fox jumps over the lazy dog today."}])
w4_mic = eng.register(new_arr(), "The quick brown box jumps over the lazy dog today. Should I restart it now or wait?",
                      [{"start": 0.9, "end": 4.4, "text": "The quick brown box jumps over the lazy dog today."},
                       {"start": 6.0, "end": 8.0, "text": "Should I restart it now or wait?"}])

windows = [
    AudioChunk(0, 0.0, {AUDIO_SOURCE_SYSTEM: w0_sys, AUDIO_SOURCE_MIC: w0_mic}),
    AudioChunk(1, 30.0, {AUDIO_SOURCE_SYSTEM: w1_sys, AUDIO_SOURCE_MIC: w1_mic}),
    AudioChunk(2, 60.0, {AUDIO_SOURCE_MIC: w2_mic}),
    AudioChunk(3, 90.0, {AUDIO_SOURCE_SYSTEM: w3_sys}),
    AudioChunk(4, 120.0, {AUDIO_SOURCE_SYSTEM: w4_sys, AUDIO_SOURCE_MIC: w4_mic}),
]
results = run_windows(eng, windows)
check(len(results) == 5, f"5 results emitted ({len(results)})")

r1 = results[1]
sys_texts = [s["text"] for s in r1.segments if s["source"] == AUDIO_SOURCE_SYSTEM]
mic_texts = [s["text"] for s in r1.segments if s["source"] == AUDIO_SOURCE_MIC]
check(sys_texts == ["And here is more remote speech."],
      f"window1 system deduped overlap ({sys_texts})")
check(mic_texts == ["Yes I agree completely with that."],
      f"window1 mic echo dropped, genuine reply kept ({mic_texts})")
check(r1.window_start == 30.0, "window_start propagated")
starts = [s["start"] for s in r1.segments]
check(starts == sorted(starts), "segments time-sorted")

r4 = results[4]
mic4 = [s["text"] for s in r4.segments if s["source"] == AUDIO_SOURCE_MIC]
check(mic4 == ["Should I restart it now or wait?"],
      f"fuzzy echo (box/fox) dropped, dissimilar reply kept ({mic4})")

print("== Writer: labels, gaps, post-process ==")
writer = MarkdownWriter(OUT, title="Test Both")
for r in results:
    writer.append(r)
writer.finalize(total_duration=125)
writer.post_process()
content = writer.file_path.read_text(encoding="utf-8")
print("---- transcript ----")
print(content)
print("--------------------")
check(content.count("**Remote [") == 3, f"3 Remote labels ({content.count('**Remote [')})")
check(content.count("**Local [") == 3, f"3 Local labels ({content.count('**Local [')})")
check("**Remote [0:00]:** Hello" in content, "first label at top with timestamp")
check("**Local [0:35]:**" in content, "local label timestamped from window offset (30+5.0)")
check("**Remote [1:31]:**" in content, "remote return label at 90+1.0")
check("\n\nNow some more local talk" in content,
      "same-source long gap gets paragraph break without new label")
check(" um " not in content, "post-process still strips fillers")
check("Recording duration: 2m 5s" in content, "footer duration present")
check("No speech was captured" not in content, "no empty-session note for real session")

print("== Writer: single source -> one label ==")
eng2 = FakeEngine()
s0 = eng2.register(new_arr(), "Only remote speech here.",
                   [{"start": 0.0, "end": 2.0, "text": "Only remote speech here."}])
s1 = eng2.register(new_arr(), "Continuing without switching.",
                   [{"start": 0.5, "end": 2.5, "text": "Continuing without switching."}])
results2 = run_windows(eng2, [
    AudioChunk(0, 0.0, {AUDIO_SOURCE_SYSTEM: s0}),
    AudioChunk(1, 30.0, {AUDIO_SOURCE_SYSTEM: s1}),
])
writer2 = MarkdownWriter(OUT, title="Test Single")
for r in results2:
    writer2.append(r)
writer2.finalize(total_duration=61)
writer2.post_process()
content2 = writer2.file_path.read_text(encoding="utf-8")
check(content2.count("**Remote [") == 1, f"exactly one label ({content2.count('**Remote [')})")
check(content2.count("**Local [") == 0, "no Local label")

print("== Writer: empty session ==")
writer3 = MarkdownWriter(OUT, title="Test Empty")
writer3.finalize(total_duration=3566)
writer3.post_process()
content3 = writer3.file_path.read_text(encoding="utf-8")
check("No speech was captured during this session." in content3, "empty-session note present")
check(not writer3.body_written, "body_written False for empty session")

print("== Silent-capture watchdog (_SilenceMonitor) ==")
mon = _SilenceMonitor(alert_s=60, repeat_s=120)
mon.start(1000.0)
check(mon.should_alert(1030.0) is False, "no alert before 60s of silence")
check(mon.should_alert(1060.0) is True, "alert fires at 60s of silence")
check(mon.should_alert(1090.0) is False, "no re-alert before the repeat interval")
check(mon.should_alert(1180.0) is True, "re-alert after the 120s repeat interval")
mon.note_audio(1200.0)
check(mon.should_alert(1230.0) is False, "audio re-arms the monitor (quiet <60s)")
check(mon.should_alert(1260.0) is True, "alert fires 60s after audio stops again")

mon2 = _SilenceMonitor(alert_s=60, repeat_s=120)
mon2.start(0.0)
alerted = False
for t in range(0, 600, 10):  # non-silent audio every 10s
    mon2.note_audio(float(t))
    if mon2.should_alert(float(t)):
        alerted = True
check(not alerted, "healthy capture (audio every 10s) never alerts")

print("== Device name matching (match_device_by_name) ==")
def _dev(name):
    return AudioDevice(index=0, name=name, channels=1, sample_rate=48000, is_loopback=False)
_devs = [_dev("Microphone (HD Pro Webcam C920)"), _dev("Headset (Poly)"), _dev("Stereo Mix")]
check(match_device_by_name("", _devs) is None, "empty name -> None (fall back to default)")
check(match_device_by_name("Nonexistent Mic", _devs) is None, "no match -> None")
check(match_device_by_name("Headset (Poly)", _devs).name == "Headset (Poly)", "exact match")
check(match_device_by_name("Stereo", _devs).name == "Stereo Mix", "prefix match (stored name shorter)")
check(
    match_device_by_name("Microphone (HD Pro Webcam C920) 2- ", _devs) is not None,
    "tolerant match survives library-to-library name drift",
)

print()
if FAILURES:
    print(f"{len(FAILURES)} FAILURE(S):")
    for f in FAILURES:
        print(" -", f)
    sys.exit(1)
print("ALL CHECKS PASSED")
