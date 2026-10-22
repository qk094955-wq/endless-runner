# endless-runner# 🏃 SPEED RUNNER — Endless Adventure

A polished, browser-based endless runner built with **Python + Streamlit**. Run, jump over obstacles, slide under overhead gates, collect coins and chase your best score. All graphics and sounds are generated in code — no image or audio files needed.

## Features

- Neon dark-themed dashboard with animated background and glowing buttons
- Main menu with Play, How to Play, sound toggle, best score and Easy / Normal / Hard difficulty
- Animated player: runs, jumps (no double jumps), slides, returns to running automatically
- Five obstacle types: wooden crates, rocks, traffic cones, tall barriers, overhead gates (slide under them)
- Animated, collectable coins (spinning, glowing, floating) that can only be collected once
- Live HUD: score, coins, distance, speed, level, best score
- Gradual speed and difficulty increase, with sensible speed caps
- Parallax environment: animated sky, sun, clouds, mountains, buildings, trees, scrolling road
- Pause, resume, restart and game-over screens (fresh run without reloading the page)
- Sound effects (jump, slide, coin, crash) generated with the browser's Web Audio API
- Best score saved in the browser (`localStorage`)
- Responsive layout for laptop and mobile (touch controls included)

## Technologies Used

- Python 3.9+
- Streamlit (page, settings, layout, embedding)
- HTML5 Canvas, CSS and JavaScript embedded inside `app.py` (game loop uses `requestAnimationFrame` with delta-time)

## Project Structure

```
speed-runner/
├── app.py
├── requirements.txt
└── README.md
```

## Installation

1. Create a folder (for example `speed-runner`) and save the three files in it.
2. (Optional) Create a virtual environment:
   ```
   python -m venv venv
   venv\Scripts\activate        # Windows
   source venv/bin/activate     # macOS / Linux
   ```
3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

## Run Locally

```
streamlit run app.py
```

Your browser opens at `http://localhost:8501`. **Click inside the game area once** so it receives keyboard input, then press **Play Game** or **Enter**.

## Controls

| Key | Action |
|---|---|
| Space / ↑ | Jump |
| ↓ | Slide |
| P | Pause / resume |
| R | Restart current run |
| M | Toggle sound |
| Enter | Start / play again (resumes when paused) |
| Mouse / Touch | Use on-screen buttons. On touch screens: tap = jump, swipe down = slide |

## Upload to GitHub

1. Create a new empty repository on [github.com](https://github.com) (for example `speed-runner`).
2. In your project folder run:
   ```
   git init
   git add app.py requirements.txt README.md
   git commit -m "Add Speed Runner game"
   git branch -M main
   git remote add origin https://github.com/<your-username>/speed-runner.git
   git push -u origin main
   ```

## Deploy on Streamlit Community Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub.
2. Click **Create app** → choose your repository, branch `main`, and main file path `app.py`.
3. Click **Deploy**. Streamlit installs `requirements.txt` automatically and gives you a public URL.

## Known Limitations

- Best score is stored per browser (`localStorage`). There is no global leaderboard, because that would need a database.
- Changing the difficulty or sound setting in the Streamlit controls reloads the game area and resets the current run (the in-game menu also has difficulty and sound buttons that don't reload).
- Browsers block audio until you interact with the page; sound starts after your first click or key press.
- The game auto-pauses when the game area loses focus (for example if you click elsewhere on the page).

## Troubleshooting

- **Keys do nothing:** click inside the game area first to give it focus.
- **No sound:** check the sound toggle (press **M**), your device volume, and that the browser tab isn't muted.
- **Best score resets:** private/incognito mode or blocked site storage prevents saving; the game still works.
- **`streamlit` not found:** run `pip install -r requirements.txt` again, or use `python -m streamlit run app.py`.
- **Page looks cut off on a phone:** rotate to landscape for the best view.
