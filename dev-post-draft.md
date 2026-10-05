# My Best Friend Revises by Re-Reading His Notes. So I Built Him a Quiz Partner That Runs on His Laptop.

## What I built 🤝

**StudyBuddy** — a practice-partner quiz app for my best friend Emmanuel Amoani ("E. Amoani"),
who studies BED Management at the University of Cape Coast.

His revision method is re-reading his course notes the night before a quiz. Passive, lonely —
and it collapses whenever the hostel Wi-Fi dies, which on campus is *often*. StudyBuddy
changes the loop: **paste in your course notes → get a real quiz (multiple-choice + short
answer) → get graded with explanations.** A patient practice partner, on demand.

## Demo 🌐

![StudyBuddy notes screen](SCREENSHOT_1_URL)
*Paste your notes — or load the sample set. (Upload `screenshots/1-notes.png` in the DEV editor and paste its URL here.)*

![StudyBuddy generated quiz](SCREENSHOT_2_URL)
*Five questions, written from the notes by the local model. (`screenshots/2-quiz.png`)*

![StudyBuddy graded results](SCREENSHOT_3_URL)
*Graded with explanations — 4/5 on the demo run, with feedback on the miss. (`screenshots/3-results.png`)*

There is no hosted demo link — that is the point. It runs entirely on your machine:
clone the repo, start the model server, `python app.py`.

## How I built it 🛠️

- **Frontend:** one self-contained HTML page. No CDNs, no trackers, no build step —
  the offline story stays honest.
- **Backend:** Flask with two endpoints — `POST /api/quiz` (notes → questions) and
  `POST /api/grade` (answers → verdicts with feedback).
- **AI core:** **Gemma 3** (Google's open-weight model), running **locally via llama.cpp**.
  The model writes every quiz question as strict JSON and judges every short answer.
  Small models fumble: so there is one retry plus defensive JSON parsing on generation,
  per-question grading calls (tiny schemas fail less), and MCQs are checked
  deterministically in code instead of by the model. All on-device.

## Why open innovation matters 🌍

The challenge asked exactly the right questions, so here are my answers:

- **Does it run on a laptop with no internet?** Yes. After downloading the model file once,
  everything happens on-device. A closed API would make this app a brick half the week —
  campus Wi-Fi is not something you can rely on.
- **Does it cost nothing to run?** Yes. A student budget has no room for per-token billing.
  Open weights mean the marginal cost of one more quiz is zero.
- **Does it keep someone's data off a server they don't control?** His course notes never
  leave his laptop. No account, no signup, no data pipeline to a third party.
- **Can you swap models or change behavior?** Point the server at any GGUF file.
  Want it to quiz in Fante? It is a prompt edit away. The open pieces are what make this
  project work — it is not a wrapper around a black box.

A closed approach would have been "easier" — one API key and done. It also would have been
worse in every way that matters to Emmanuel: dead without Wi-Fi, metered by the token,
and shipping his notes to someone else's server.

## What Emmanuel said 💬

[Show him the app and write his real reaction here — a sentence or two in his own words is worth more than a paragraph of mine.]

## Prize categories 🏆

- Overall — Hacktoberfest Weekend Challenge: Build for a Friend
- Best Use of Gemma (featured): Gemma 3 runs the entire quiz loop locally

## Code 💻

[REPO_URL_HERE — paste the https://github.com/rokeita/studybuddy-amoani link once the repo is created and the code is pushed] — MIT licensed. Built 4–5 October 2026, inside the challenge window.

---
*Tags: #devchallenge #weekendchallenge #hf26challenge*
