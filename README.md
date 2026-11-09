# The Invisible Guardian — Online AI-to-AI Audio Whisperer

An online AI-powered audio steganography system. It hides a secret voice message inside
an everyday cover sound (rain, traffic, music, environmental noise) by **training a tiny
neural network on the secret's spectrogram**, then embedding that trained network inside
the cover audio using LSB steganography. Anyone who doesn't know to look will just hear
rain.

## Setup

**Windows — easiest way:** double-click **`start_guardian.bat`**. First run installs
packages automatically (a minute or two); it then opens the app in your browser. Every
run after that starts fast. Keep the black server window open while you use the app.

**Mac / Linux — easiest way:** double-click **`start_guardian.sh`** (or run
`./start_guardian.sh` in a terminal).

**Manual way (any OS):**

```bash
pip install -r requirements.txt
python run.py
```

Visit `http://127.0.0.1:5000`. A default admin account is created automatically:
- username: `admin`
- password: `Admin@123`

> **Note:** this launcher installs packages directly (no virtual environment) to avoid
> a real issue we hit during testing — a venv activated in one terminal and packages
> installed in a different (non-venv) terminal caused a confusing
> `ModuleNotFoundError: No module named 'flask'` even though install had "succeeded".
> If you prefer an isolated venv, create and activate it yourself **in the same
> terminal window** you'll run `python run.py` from, then run the manual steps above.

## How it actually works (no shortcuts, no lookup tables)

**Encode**
1. Secret voice is resampled and converted to a log-magnitude STFT spectrogram.
2. A small encoder-decoder network (`app/ai/stego_engine.py :: TinyAutoencoder`) is
   **trained from scratch, per message**, with real backpropagation + Adam (1500 steps),
   to reconstruct that specific spectrogram.
3. The trained decoder's weights and every frame's latent code are quantised to 8-bit
   and packed into a small binary payload (typically ~10KB for a 4-second message).
4. That payload is hidden in the cover audio's 16-bit PCM samples via least-significant-
   bit embedding. If the cover is too short to hold the payload, encoding is rejected
   with a clear error instead of silently corrupting audio.

**Decode**
1. The payload is extracted from the stego file's LSBs.
2. The tiny decoder network is rebuilt from the transmitted weights.
3. Each frame's latent code is decoded back into a spectrogram frame.
4. Griffin-Lim (60 iterations) estimates the missing phase and reconstructs a
   listenable waveform.

Tested end-to-end as **two independent devices**: one session encodes and downloads the
stego `.wav`, a second, unrelated session (no shared login, just the file) uploads that
`.wav` and successfully decodes a real reconstructed voice back out — with real spoken
audio (synthesised via `espeak-ng` for repeatable testing), not just a smooth test tone.

## Features

- Registration / login (hashed passwords via Werkzeug)
- Encode page — upload cover + secret, optional passphrase lock, live metrics (SNR, MSE,
  spectrogram similarity, training loss, payload size vs. capacity, timing)
- Decode page — upload any stego `.wav`/`.flac`/`.ogg`/`.aiff` **or** pick from your own
  saved files / files shared with you
- **One-time share link** — from the dashboard or the encode-result page, generate a
  link that works without any login on the friend's side. They open it, hear the cover
  audio, click reveal, get the hidden voice back — then the link is permanently
  consumed (also expires after 24h either way).
- **Offline / same-network access** — the dashboard shows your machine's LAN IP and
  port (e.g. `http://192.168.1.23:5000`). Anyone on the same WiFi or your phone's
  hotspot can type that address into their own browser — no internet required.
- Dashboard — your stego files, download, share-with-username (registered users), get a
  one-time link (anyone), delete
- History — past encode jobs and decode attempts
- Automatic file expiry (configurable, default 72h)
- Admin monitoring dashboard (`/admin`) — user list, job list, decode success rate,
  average fidelity metrics
- Upload limit raised to 300MB (covers plenty of headroom for uncompressed WAV files)

## Testing it yourself

**Option 1 — one-time link (no second account needed):**
1. Register/login, go to **Encode**, upload a cover + secret voice, submit.
2. Click **"Get one-time link for this file"** (shown right on the result page, or from
   the Dashboard).
3. Copy the URL from the confirmation banner, send it to a friend any way you like.
4. They open it — no account — see the cover audio and a "Reveal" button.
5. They click it, get the reconstructed voice. Opening the link again shows
   "no longer available".

**Option 2 — same WiFi / hotspot, no internet:**
1. Run the app. Dashboard shows something like `http://192.168.1.23:5000`.
2. Anyone on the same WiFi/hotspot types that into their browser directly.

**Option 3 — two registered accounts:**
1. Account A encodes, downloads the stego `.wav`, sends the file to Account B by any
   means.
2. Account B uploads it on the Decode page directly.

## Project layout

```
app/
  ai/stego_engine.py   # the AI steganography core (train / pack / embed / extract / rebuild)
  models.py             # SQLAlchemy models: User, StegoJob, FileShare, ShareLink, DecodeLog
  routes/               # auth, main (dashboard/history/sharing), stego (encode/decode), share, admin
  templates/             # server-rendered HTML, dark "signal/waveform" theme
  static/css/style.css
run.py                   # entry point
docs/PROJECT_REPORT.md   # full academic write-up for submission / viva
```

## Honest limitations for the viva

- Secret length is capped (~4 seconds) to keep the trained payload small enough for
  LSB capacity in short covers.
- Only magnitude is transmitted; phase is estimated with Griffin-Lim on decode, so
  reconstructed voice is intelligible but not hi-fi audio (telephone-ish quality).
- LSB embedding is robust to file copying but not to lossy re-encoding (e.g. converting
  the stego file to MP3 and back would destroy the payload) — inherent to LSB
  steganography generally, not specific to this implementation.

## Two real bugs found and fixed during development (documented on purpose)

**1. Training collapse on real speech.** Real speech spectrograms are ~85-90% near-silent
bins (pauses, quiet consonants) with energy concentrated in relatively few loud bins.
Training with plain MSE let the network minimise loss by predicting near-zero almost
everywhere — technically low error, but it destroyed the actual voice (this produced
static/noise-like output on real recordings, even though a smooth synthetic test tone
reconstructed fine, which is what initially masked the bug). Fixed by weighting each
bin's squared error by `(1 + α·target)`, forcing the network to prioritise the loud,
speech-carrying bins. `α=30` chosen empirically.

**2. Griffin-Lim not converging.** The phase-estimation loop was re-truncating/padding
the waveform to the target length on *every* iteration, which reset STFT frame
boundaries each time and prevented the algorithm from converging on a stable phase
estimate. Fixed by only trimming the waveform once, after the loop finishes.

Both were caught by testing with real synthesised speech (`espeak-ng`) rather than only
a synthetic tone, and by visually comparing before/after spectrograms rather than
trusting a single aggregate metric. Spectrogram similarity on real speech went from
≈0.34-0.47 (audibly noise-like) to ≈0.96 (clearly recognisable as speech) after both
fixes — verified via a real HTTP round trip between two separate accounts.
