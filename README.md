# 📚 StudyBuddy — a practice partner built for E. Amoani

**Hacktoberfest 2026 DEV Weekend Challenge: "Build for a Friend" submission.**

My best friend Emmanuel Amoani studies BED Management at the University of Cape Coast.
His revision routine is re-reading his course notes the night before a quiz — passive,
lonely, and it collapses the moment hostel Wi-Fi dies. So I built him a practice partner:
paste in course notes, get a real quiz (multiple-choice + short answers), get graded
with explanations. 

**Open-source AI at its core:** every question and every grade is produced by
**Gemma 3** (Google's open-weight model), running **locally via llama.cpp**.
No API keys. No internet needed after the model file is downloaded. His notes never leave his machine.

> Built on 4 October 2026, inside the challenge window (Oct 2–5, 2026).

## How it works

```
[ browser ] → Flask app (app.py) → llama.cpp server (localhost:8000) → Gemma 3 (open weights)
   1. POST /api/quiz   — notes → model writes N questions as strict JSON
   2. you answer in the page
   3. POST /api/grade  — model judges short answers, MCQs checked, explanations shown
```

The frontend is a single self-contained page — no CDNs, no trackers, works offline.

## Run it

1. Get `llama-server` (open-source, llama.cpp): download `llama-b11400-bin-ubuntu-x64.tar.gz`
   from the [llama.cpp releases](https://github.com/ggml-org/llama.cpp/releases) and extract it.
2. Download the model file (once, ~800 MB), e.g.
   [`google_gemma-3-1b-it-Q4_K_M.gguf`](https://huggingface.co/bartowski/google_gemma-3-1b-it-GGUF).
3. Start the model server:
   ```
   ./llama-server -m google_gemma-3-1b-q4km.gguf -c 2048 --port 8000
   ```
4. Install and run the app:
   ```
   pip install -r requirements.txt
   python app.py
   ```
5. Open http://localhost:5000 — paste notes (or hit **Load sample notes**), generate, answer, get graded.

Swap in a bigger Gemma any time — just point `llama-server` at a larger GGUF.

## Screenshots

Demo screenshots (notes → quiz → graded results) are in the DEV challenge submission post — the repo's GitHub App upload path mangles binary files, so they live with the write-up instead of here.

## Why open innovation matters here

- **Runs on a laptop with no internet.** Campus Wi-Fi is unreliable; after downloading the
  model file once, everything happens on-device. A closed API would make this app a brick half the week.
- **Costs nothing to run.** A student budget in cedis has no room for per-token billing.
  Open weights mean the marginal cost of one more quiz is zero.
- **Keeps his data off servers he doesn't control.** Course notes stay on his laptop —
  no account, no signup, no data pipeline to a third party.
- **Swappable and hackable.** Don't like this Gemma? Point llama-server at any GGUF.
  Want it in Fante? Change the prompt. The open pieces are what make the project work —
  not a wrapper around a black box.

## Prize categories entered

- Overall — Hacktoberfest Weekend Challenge: Build for a Friend
- Best Use of Gemma (featured): Gemma 3 runs the entire quiz loop locally

## License

MIT — see [LICENSE](LICENSE).
