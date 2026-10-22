"""SPEED RUNNER - Endless Adventure.

A browser-based endless runner built with Streamlit. Streamlit provides the
page, settings and difficulty profiles; the real-time game (canvas, physics,
collisions, audio) runs in JavaScript inside an embedded component so it never
depends on Streamlit reruns for animation frames.
"""

import json

import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Speed Runner", page_icon="🏃", layout="wide")

# ---------------------------------------------------------------------------
# Difficulty profiles (single source of truth, passed to the game as JSON)
#   v0/vmax: start / max speed (px per second)   acc: speed gain per second
#   gap: seconds between obstacles (min, max)    over: overhead obstacle chance
#   cluster: chance of a double obstacle
# ---------------------------------------------------------------------------
PROFILES = {
    "easy": {"v0": 300, "vmax": 520, "acc": 6, "gap": [1.4, 2.4], "over": 0.08, "cluster": 0.0},
    "normal": {"v0": 380, "vmax": 680, "acc": 8, "gap": [1.1, 2.0], "over": 0.18, "cluster": 0.12},
    "hard": {"v0": 460, "vmax": 820, "acc": 10, "gap": [0.9, 1.6], "over": 0.28, "cluster": 0.25},
}
FREQUENCY = {"easy": "Low", "normal": "Medium", "hard": "High"}

PAGE_CSS = """
<style>
.stApp {background: radial-gradient(circle at 20% 0%, #1a0b2e 0%, #0b0b1a 55%, #06121f 100%);}
#MainMenu, footer {visibility: hidden;}
.sr-title {text-align:center; font-size:clamp(34px,6vw,60px); font-weight:900; letter-spacing:4px;
  margin:0; background:linear-gradient(90deg,#00d4ff,#a855f7,#39ff14); -webkit-background-clip:text;
  -webkit-text-fill-color:transparent; filter:drop-shadow(0 0 12px rgba(0,212,255,.55));}
.sr-sub {text-align:center; color:#9fb4d6; margin:0 0 14px 0; letter-spacing:2px;}
[data-testid="stMetricValue"] {color:#39ff14;}
</style>
"""

GAME_HTML = r"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>
:root{--b:#00d4ff;--p:#a855f7;--g:#39ff14}
*{box-sizing:border-box}
html,body{margin:0;height:100%;font-family:'Segoe UI',system-ui,sans-serif;color:#e8e8ff;overflow:hidden}
body{background:linear-gradient(135deg,#0b0b1a,#1a0b2e,#0b1a2e,#0b0b1a);background-size:400% 400%;animation:bg 14s ease infinite}
@keyframes bg{0%{background-position:0 50%}50%{background-position:100% 50%}100%{background-position:0 50%}}
@keyframes fade{from{opacity:0;transform:scale(.97)}to{opacity:1;transform:none}}
@keyframes glow{0%,100%{filter:drop-shadow(0 0 8px var(--b))}50%{filter:drop-shadow(0 0 20px var(--p))}}
#app{max-width:900px;margin:0 auto;padding:6px}
#hud{display:grid;grid-template-columns:repeat(auto-fit,minmax(88px,1fr));gap:6px;margin-bottom:6px}
.s{background:rgba(255,255,255,.06);border:1px solid rgba(0,212,255,.35);border-radius:10px;padding:4px 8px;text-align:center;box-shadow:0 0 10px rgba(0,212,255,.15)}
.s small{display:block;font-size:10px;letter-spacing:1.5px;color:#9bb;text-transform:uppercase}
.s b{font-size:18px;color:var(--g);text-shadow:0 0 8px var(--g)}
#stage{position:relative;border-radius:14px;overflow:hidden;border:2px solid var(--p);box-shadow:0 0 24px rgba(168,85,247,.55),0 0 50px rgba(0,212,255,.2)}
canvas{display:block;width:100%;height:auto;touch-action:none;background:#000;outline:none}
#ov{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;background:rgba(8,6,24,.74);backdrop-filter:blur(3px);overflow:auto;text-align:center;padding:10px;animation:fade .3s}
.panel{max-width:460px;margin:auto}
.logo{font-size:clamp(30px,7vw,54px);font-weight:900;letter-spacing:3px;color:#fff;animation:glow 2.4s infinite}
.logo span{background:linear-gradient(90deg,var(--b),var(--p),var(--g));-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.sub{color:#9fb4d6;letter-spacing:3px;font-size:12px;margin-bottom:8px}
.best{font-size:16px;margin:6px 0;color:#ffd60a;text-shadow:0 0 8px #ffd60a}
.btn{cursor:pointer;border:0;border-radius:30px;padding:10px 26px;margin:4px;font-weight:700;font-size:16px;color:#fff;background:linear-gradient(90deg,var(--b),var(--p));box-shadow:0 0 14px var(--b);transition:.2s;font-family:inherit}
.btn:hover{transform:translateY(-2px) scale(1.04);box-shadow:0 0 24px var(--p)}
.btn.sm{padding:6px 16px;font-size:13px}
.btn.ghost{background:rgba(255,255,255,.05);border:2px solid var(--b);box-shadow:none}
.btn.on{background:linear-gradient(90deg,var(--g),var(--b));color:#02150a;border:0;box-shadow:0 0 14px var(--g)}
.how{font-size:12px;color:#b8c6e6;line-height:1.6;margin-top:8px;background:rgba(255,255,255,.05);border-radius:10px;padding:8px}
h2{margin:0 0 8px;font-size:clamp(26px,5vw,40px);color:#ff4d6d;text-shadow:0 0 14px #ff4d6d;letter-spacing:3px}
h2.p{color:var(--b);text-shadow:0 0 14px var(--b)}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin:8px 0}
.grid div{background:rgba(255,255,255,.07);border-radius:10px;padding:6px}
.grid small{display:block;font-size:10px;color:#9bb;letter-spacing:1px;text-transform:uppercase}
.grid b{font-size:20px;color:var(--g)}
#bar{text-align:center;margin-top:6px}
#hint{font-size:11px;color:#8fa2c8;text-align:center;margin-top:2px}
</style></head>
<body><div id="app">
<div id="hud">
<div class="s"><small>Score</small><b id="hs">0</b></div>
<div class="s"><small>Coins</small><b id="hc">0</b></div>
<div class="s"><small>Distance</small><b id="hd">0 m</b></div>
<div class="s"><small>Speed</small><b id="hv">0</b></div>
<div class="s"><small>Level</small><b id="hl">1</b></div>
<div class="s"><small>Best</small><b id="hb">0</b></div>
</div>
<div id="stage"><canvas id="c" width="800" height="400" tabindex="0"></canvas><div id="ov"></div></div>
<div id="bar">
<button class="btn sm ghost" data-a="pause">⏸ Pause / Resume</button>
<button class="btn sm ghost" data-a="restart">↻ Restart</button>
<button class="btn sm ghost" id="sbtn" data-a="sound">🔊 Sound</button>
</div>
<div id="hint">Space/↑ jump · ↓ slide · P pause · R restart · M sound · Enter start &nbsp;|&nbsp; Touch: tap = jump, swipe down = slide</div>
</div>
<script>
(() => {
"use strict";
const CFG = __CONFIG__;
const PR = CFG.profiles;
const W = 800, H = 400, GY = 330, PX = 100, GRAV = 2400, JUMPV = 820;
const cv = document.getElementById("c"), ctx = cv.getContext("2d");
const ov = document.getElementById("ov");

const TYPES = [
  {k: "crate", w: 44, h: 44, y: 0}, {k: "rock", w: 48, h: 32, y: 0},
  {k: "cone", w: 30, h: 42, y: 0}, {k: "barrier", w: 34, h: 84, y: 0},
  {k: "overhead", w: 80, h: 40, y: 45}
];
const BH = [90, 130, 70, 150, 100, 120, 80, 140], TH = [50, 70, 60, 80, 55];

let diff = CFG.difficulty, sound = CFG.sound, state = "menu";
let best = 0, newBest = false, bgOff = 0, bgT = 0, g = null;
try { best = +localStorage.getItem("sr_best") || 0; } catch (e) {}
function saveBest() { try { localStorage.setItem("sr_best", String(best)); } catch (e) {} }

const stars = Array.from({length: 40}, (_, i) => ({x: (i * 97) % W, y: (i * 53) % 190, r: 0.6 + (i % 3) * 0.5}));
const clouds = Array.from({length: 5}, (_, i) => ({x: i * 190, y: 40 + (i * 37) % 110, s: 0.8 + (i % 3) * 0.3}));

function reset() {
  g = {t: 0, dist: 0, coins: 0, speed: PR[diff].v0, obs: [], cn: [], pop: [],
       spawnIn: 500, py: 0, vy: 0, slide: 0, anim: 0, shake: 0};
}
const lvl = () => 1 + Math.floor(g.dist / 150);
const score = () => Math.floor(g.dist * 10) + g.coins * 50;

/* ---------------- audio (WebAudio, created after first user gesture) ---------------- */
let ac = null;
function ensureAudio() {
  if (!sound) return;
  try {
    if (!ac) ac = new (window.AudioContext || window.webkitAudioContext)();
    if (ac.state === "suspended") ac.resume();
  } catch (e) { ac = null; }
}
function beep(f1, f2, d, type, vol) {
  if (!sound || !ac) return;
  try {
    const o = ac.createOscillator(), gn = ac.createGain(), t = ac.currentTime;
    o.type = type;
    o.frequency.setValueAtTime(f1, t);
    o.frequency.exponentialRampToValueAtTime(f2, t + d);
    gn.gain.setValueAtTime(vol, t);
    gn.gain.exponentialRampToValueAtTime(0.001, t + d);
    o.connect(gn); gn.connect(ac.destination);
    o.start(); o.stop(t + d);
  } catch (e) {}
}

/* ---------------- screens ---------------- */
function showOv(html) { ov.innerHTML = html; ov.style.display = "flex"; }
function hideOv() { ov.style.display = "none"; ov.innerHTML = ""; }
const soundLabel = () => (sound ? "🔊 Sound: ON" : "🔇 Sound: OFF");
function menuScreen() {
  const d = ["easy", "normal", "hard"].map(k =>
    `<button class="btn sm ${k === diff ? "on" : "ghost"}" data-a="diff" data-v="${k}">${k[0].toUpperCase() + k.slice(1)}</button>`).join("");
  showOv(`<div class="panel"><div class="logo">SPEED <span>RUNNER</span></div>
  <div class="sub">ENDLESS ADVENTURE</div><div class="best">🏆 Best Score: ${best}</div>
  <div>${d}</div>
  <div><button class="btn" data-a="play">▶ Play Game</button></div>
  <div><button class="btn sm ghost" data-a="sound">${soundLabel()}</button></div>
  <div class="how"><b>How to Play</b><br>Space / ↑ = jump · ↓ = slide · P = pause · R = restart · M = sound · Enter = start.<br>
  Jump crates, rocks, cones and tall barriers. Slide under the glowing overhead gates. Collect coins for bonus points!<br>
  Touch: tap = jump, swipe down = slide.</div></div>`);
}
function pauseScreen() {
  showOv(`<div class="panel"><h2 class="p">PAUSED</h2>
  <button class="btn" data-a="resume">▶ Resume</button><button class="btn ghost" data-a="restart">↻ Restart</button>
  <button class="btn ghost" data-a="menu">🏠 Main Menu</button></div>`);
}
function overScreen() {
  showOv(`<div class="panel"><h2>GAME OVER</h2>
  ${newBest ? '<div class="best">🎉 New Best Score!</div>' : ""}
  <div class="grid"><div><small>Final Score</small><b>${score()}</b></div><div><small>Coins</small><b>${g.coins}</b></div>
  <div><small>Distance</small><b>${Math.floor(g.dist)} m</b></div><div><small>Best Score</small><b>${best}</b></div></div>
  <button class="btn" data-a="play">▶ Play Again</button><button class="btn ghost" data-a="menu">🏠 Main Menu</button></div>`);
}

/* ---------------- state transitions ---------------- */
function start() { reset(); state = "playing"; hideOv(); ensureAudio(); cv.focus(); }
function pause() { if (state === "playing") { state = "paused"; pauseScreen(); } }
function resume() { if (state === "paused") { state = "playing"; hideOv(); cv.focus(); } }
function toMenu() { reset(); state = "menu"; menuScreen(); }
function toggleSound() {
  sound = !sound; if (sound) ensureAudio();
  document.getElementById("sbtn").textContent = soundLabel();
  if (state === "menu") menuScreen();
}
function crash() {
  state = "over"; g.shake = 1;
  beep(220, 40, 0.45, "sawtooth", 0.18);
  const s = score(); newBest = s > best;
  if (newBest) { best = s; saveBest(); }
  setTimeout(() => { if (state === "over") overScreen(); }, 500);
}
function act(a, v) {
  ensureAudio();
  if (a === "play" || a === "restart") start();
  else if (a === "resume") resume();
  else if (a === "pause") { state === "playing" ? pause() : resume(); }
  else if (a === "menu") toMenu();
  else if (a === "sound") toggleSound();
  else if (a === "diff") { diff = v; reset(); menuScreen(); }
}
document.addEventListener("click", e => {
  const b = e.target.closest("[data-a]");
  if (b) act(b.dataset.a, b.dataset.v);
});

/* ---------------- player actions ---------------- */
function jump() {
  if (state !== "playing" || g.py > 0 || g.vy > 0) return;   // no double jumps
  g.slide = 0; g.vy = JUMPV; g.py = 0.01;
  beep(300, 650, 0.16, "square", 0.07);
}
function slide() {
  if (state !== "playing") return;
  if (g.py <= 0) { if (g.slide <= 0) beep(420, 180, 0.12, "triangle", 0.08); g.slide = 0.7; }
  else g.vy = Math.min(g.vy, -900);                          // fast-fall
}
window.addEventListener("keydown", e => {
  const k = e.key.toLowerCase();
  if ([" ", "arrowup", "arrowdown"].includes(k)) e.preventDefault();
  ensureAudio();
  if (e.repeat) return;
  if (k === " " || k === "arrowup" || k === "w") jump();
  else if (k === "arrowdown" || k === "s") slide();
  else if (k === "p") { state === "playing" ? pause() : resume(); }
  else if (k === "r") { if (state !== "menu") start(); }
  else if (k === "m") toggleSound();
  else if (k === "enter") {
    if (state === "menu" || state === "over") start(); else if (state === "paused") resume();
  }
});
let ty = null;
cv.addEventListener("touchstart", e => { e.preventDefault(); ensureAudio(); ty = e.touches[0].clientY; }, {passive: false});
cv.addEventListener("touchend", e => {
  e.preventDefault();
  if (ty === null) return;
  const dy = e.changedTouches[0].clientY - ty; ty = null;
  if (dy > 30) slide(); else jump();
}, {passive: false});
window.addEventListener("blur", () => { if (state === "playing") pause(); });

/* ---------------- spawning ---------------- */
function addObs(t, x) { g.obs.push({k: t.k, w: t.w, h: t.h, y: t.y, x: x}); }
function spawn() {
  const P = PR[diff], L = lvl();
  let t;
  if (Math.random() < P.over + Math.min(0.15, 0.01 * (L - 1))) t = TYPES[4];
  else t = TYPES[Math.floor(Math.random() * 4)];
  addObs(t, W + 60);
  let extra = 0;
  if (t.k !== "overhead" && t.k !== "barrier" && Math.random() < P.cluster) {
    const t2 = TYPES[Math.floor(Math.random() * 3)];
    extra = t.w + 14 + Math.random() * 10;
    addObs(t2, W + 60 + extra);
    extra += t2.w;
  }
  const f = Math.max(0.75, 1 - 0.02 * (L - 1));
  const sec = Math.max(0.85, (P.gap[0] + Math.random() * (P.gap[1] - P.gap[0])) * f);
  const gap = g.speed * sec;
  g.spawnIn = gap + extra;
  if (Math.random() < 0.7) {            // coins float in the middle of the gap
    const n = 3 + Math.floor(Math.random() * 3), hh = Math.random() < 0.5 ? 26 : 105;
    const cx = W + 60 + gap * 0.5 - n * 18;
    for (let i = 0; i < n; i++) {
      const arc = hh > 50 ? Math.sin(i / Math.max(1, n - 1) * Math.PI) * 25 : 0;
      g.cn.push({x: cx + i * 36, h: hh + arc, got: false, ph: Math.random() * 6});
    }
  }
}

/* ---------------- update ---------------- */
function step(dt) {
  const P = PR[diff];
  g.t += dt; g.anim += dt;
  g.speed = Math.min(P.vmax, g.speed + P.acc * dt);
  const dx = g.speed * dt;
  g.dist += dx / 20;
  if (g.py > 0 || g.vy > 0) {
    g.vy -= GRAV * dt; g.py += g.vy * dt;
    if (g.py <= 0) { g.py = 0; g.vy = 0; }
  }
  if (g.slide > 0) g.slide -= dt;
  g.spawnIn -= dx;
  if (g.spawnIn <= 0) spawn();
  for (const o of g.obs) o.x -= dx;
  for (const c of g.cn) c.x -= dx;
  g.obs = g.obs.filter(o => o.x + o.w > -20);
  g.cn = g.cn.filter(c => !c.got && c.x > -30);
  for (const p of g.pop) p.t += dt;
  g.pop = g.pop.filter(p => p.t < 0.7);

  const pw = g.slide > 0 ? 50 : 38, ph = g.slide > 0 ? 30 : 60;
  const L = PX + 6, R = PX + pw - 6, B = g.py + 4, T = g.py + ph - 4;
  for (const o of g.obs) {
    if (L < o.x + o.w - 3 && R > o.x + 3 && B < o.y + o.h - 3 && T > o.y) { crash(); return; }
  }
  for (const c of g.cn) {
    if (!c.got && c.x + 12 > PX && c.x - 12 < PX + pw && c.h + 12 > g.py && c.h - 12 < g.py + ph) {
      c.got = true; g.coins++; g.pop.push({x: c.x, h: c.h, t: 0});
      beep(900, 1500, 0.12, "sine", 0.1);
    }
  }
}
function update(dt) {
  bgT += dt;
  if (state === "playing") { step(dt); bgOff += g.speed * dt; }
  else if (state === "menu") { bgOff += 90 * dt; g.anim += dt; }
  if (g.shake > 0) g.shake = Math.max(0, g.shake - dt * 2);
  for (const c of clouds) { c.x -= (8 * c.s + (state === "playing" ? g.speed * 0.02 : 0)) * dt; if (c.x < -120) c.x = W + 60; }
}

/* ---------------- drawing ---------------- */
function rr(x, y, w, h, r) { ctx.beginPath(); if (ctx.roundRect) ctx.roundRect(x, y, w, h, r); else ctx.rect(x, y, w, h); }
function drawBackground() {
  const sk = ctx.createLinearGradient(0, 0, 0, GY);
  sk.addColorStop(0, `hsl(${240 + 25 * Math.sin(bgT * 0.05)},60%,12%)`);
  sk.addColorStop(1, `hsl(${285 + 30 * Math.sin(bgT * 0.05 + 1)},60%,30%)`);
  ctx.fillStyle = sk; ctx.fillRect(0, 0, W, H);
  ctx.fillStyle = "#fff";
  for (const s of stars) { ctx.globalAlpha = 0.5 + 0.5 * Math.sin(bgT * 2 + s.x); ctx.fillRect(s.x, s.y, s.r, s.r); }
  ctx.globalAlpha = 1;
  const sg = ctx.createRadialGradient(660, 95, 5, 660, 95, 60);
  sg.addColorStop(0, "#fff3b0"); sg.addColorStop(0.4, "#ff9ad5"); sg.addColorStop(1, "rgba(168,85,247,0)");
  ctx.fillStyle = sg; ctx.beginPath(); ctx.arc(660, 95, 60, 0, 7); ctx.fill();
  ctx.fillStyle = "rgba(255,255,255,.18)";                       // clouds
  for (const c of clouds) {
    ctx.beginPath(); ctx.ellipse(c.x, c.y, 46 * c.s, 14 * c.s, 0, 0, 7); ctx.ellipse(c.x + 28 * c.s, c.y - 8 * c.s, 30 * c.s, 14 * c.s, 0, 0, 7); ctx.fill();
  }
  ctx.fillStyle = "#2a1b52";                                      // mountains (far)
  const mo = (bgOff * 0.08) % 500;
  for (let x = -mo; x < W; x += 500) {
    ctx.beginPath(); ctx.moveTo(x, GY); ctx.lineTo(x + 120, GY - 170); ctx.lineTo(x + 250, GY);
    ctx.lineTo(x + 330, GY - 120); ctx.lineTo(x + 500, GY); ctx.fill();
  }
  const bo = bgOff * 0.25, bk = Math.floor(bo / 60);              // buildings (mid)
  for (let j = 0; j < 16; j++) {
    const x = j * 60 - (bo % 60), h = BH[(bk + j) % 8];
    ctx.fillStyle = "#171433"; ctx.fillRect(x, GY - h, 50, h);
    ctx.fillStyle = "rgba(0,212,255,.55)";
    for (let wy = GY - h + 10; wy < GY - 12; wy += 20) for (let wx = x + 8; wx < x + 42; wx += 14) if ((wx + wy + bk + j) % 3) ctx.fillRect(wx, wy, 6, 8);
  }
  const to = bgOff * 0.6, tk = Math.floor(to / 150);              // trees (near)
  for (let j = 0; j < 7; j++) {
    const x = j * 150 - (to % 150) + 40, h = TH[(tk + j) % 5];
    ctx.fillStyle = "#3b2a1a"; ctx.fillRect(x - 3, GY - h * 0.5, 6, h * 0.5);
    ctx.fillStyle = "#0f5132"; ctx.beginPath(); ctx.moveTo(x, GY - h - 20); ctx.lineTo(x + 24, GY - h * 0.35); ctx.lineTo(x - 24, GY - h * 0.35); ctx.fill();
  }
  const gg = ctx.createLinearGradient(0, GY, 0, H);               // ground
  gg.addColorStop(0, "#1b1b3a"); gg.addColorStop(1, "#0a0a1c");
  ctx.fillStyle = gg; ctx.fillRect(0, GY, W, H - GY);
  ctx.save(); ctx.fillStyle = "#39ff14"; ctx.shadowColor = "#39ff14"; ctx.shadowBlur = 10; ctx.fillRect(0, GY, W, 3); ctx.restore();
  ctx.fillStyle = "#8be9ff";
  const go = bgOff % 80;
  for (let x = -go; x < W; x += 80) ctx.fillRect(x, GY + 40, 44, 5);
}
function drawObs(o) {
  const x = o.x, y = GY - o.y - o.h, w = o.w, h = o.h;
  ctx.save();
  if (o.k === "crate") {
    ctx.fillStyle = "#b8793a"; ctx.strokeStyle = "#4a2c0f"; ctx.lineWidth = 3;
    ctx.fillRect(x, y, w, h); ctx.strokeRect(x + 1.5, y + 1.5, w - 3, h - 3);
    ctx.beginPath(); ctx.moveTo(x, y); ctx.lineTo(x + w, y + h); ctx.moveTo(x + w, y); ctx.lineTo(x, y + h); ctx.stroke();
  } else if (o.k === "rock") {
    ctx.fillStyle = "#7d8597"; ctx.beginPath(); ctx.moveTo(x, y + h); ctx.lineTo(x + 6, y + h * 0.35);
    ctx.lineTo(x + w * 0.4, y); ctx.lineTo(x + w * 0.8, y + h * 0.2); ctx.lineTo(x + w, y + h); ctx.closePath(); ctx.fill();
    ctx.fillStyle = "rgba(255,255,255,.22)"; ctx.beginPath(); ctx.moveTo(x + w * 0.4, y); ctx.lineTo(x + w * 0.8, y + h * 0.2); ctx.lineTo(x + w * 0.45, y + h * 0.4); ctx.fill();
  } else if (o.k === "cone") {
    ctx.fillStyle = "#ff7a1a"; ctx.beginPath(); ctx.moveTo(x + w / 2, y); ctx.lineTo(x + w, y + h); ctx.lineTo(x, y + h); ctx.closePath(); ctx.fill();
    ctx.fillStyle = "#fff"; ctx.fillRect(x + w * 0.28, y + h * 0.45, w * 0.44, 6);
    ctx.fillStyle = "#333"; ctx.fillRect(x - 3, y + h - 5, w + 6, 5);
  } else if (o.k === "barrier") {
    ctx.fillStyle = "#fff"; ctx.fillRect(x, y, w, h);
    ctx.fillStyle = "#e11d48"; for (let i = 0; i < h; i += 24) ctx.fillRect(x, y + i, w, Math.min(12, h - i));
    ctx.strokeStyle = "#222"; ctx.lineWidth = 3; ctx.strokeRect(x, y, w, h);
  } else {
    ctx.strokeStyle = "#556"; ctx.lineWidth = 2;
    ctx.beginPath(); ctx.moveTo(x + 8, 0); ctx.lineTo(x + 8, y); ctx.moveTo(x + w - 8, 0); ctx.lineTo(x + w - 8, y); ctx.stroke();
    ctx.shadowColor = "#ff2bd6"; ctx.shadowBlur = 16; ctx.fillStyle = "#2b1055"; ctx.fillRect(x, y, w, h);
    ctx.fillStyle = "#ffd60a"; ctx.fillRect(x, y, w, 6);
    ctx.fillStyle = "#ff2bd6"; for (let i = 4; i < w - 8; i += 16) ctx.fillRect(x + i, y + h - 10, 8, 8);
  }
  ctx.restore();
}
function drawCoin(c) {
  const cy = GY - c.h + Math.sin(bgT * 4 + c.ph) * 3, sx = Math.abs(Math.cos(bgT * 4 + c.ph)) * 0.8 + 0.2;
  ctx.save(); ctx.shadowColor = "#ffd60a"; ctx.shadowBlur = 14;
  ctx.fillStyle = "#ffd60a"; ctx.beginPath(); ctx.ellipse(c.x, cy, 11 * sx, 11, 0, 0, 7); ctx.fill();
  ctx.fillStyle = "#b88900"; ctx.beginPath(); ctx.ellipse(c.x, cy, 6 * sx, 7, 0, 0, 7); ctx.fill();
  ctx.restore();
}
function drawPlayer() {
  const sl = g.slide > 0, onG = g.py <= 0, h = sl ? 30 : 60, top = GY - g.py - h, x = PX;
  ctx.save(); ctx.shadowColor = "#00d4ff"; ctx.shadowBlur = 16; ctx.lineCap = "round";
  if (sl) {
    ctx.fillStyle = "#00d4ff"; rr(x, top + 8, 46, 22, 10); ctx.fill();
    ctx.fillStyle = "#39ff14"; ctx.beginPath(); ctx.arc(x + 44, top + 18, 10, 0, 7); ctx.fill();
    ctx.fillStyle = "#fff"; ctx.fillRect(x + 46, top + 14, 6, 5);
    ctx.fillStyle = "rgba(0,212,255,.35)"; ctx.fillRect(x - 24, top + 14, 22, 3); ctx.fillRect(x - 16, top + 22, 14, 3);
  } else {
    const sw = onG ? Math.sin(g.anim * 14) * 14 : 6, hx = x + 19;
    ctx.strokeStyle = "#a855f7"; ctx.lineWidth = 7;
    ctx.beginPath(); ctx.moveTo(hx, top + 40); ctx.lineTo(hx + sw, top + (onG ? 60 : 54));
    ctx.moveTo(hx, top + 40); ctx.lineTo(hx - sw, top + (onG ? 60 : 54)); ctx.stroke();
    ctx.strokeStyle = "#00a8cc"; ctx.lineWidth = 6;
    ctx.beginPath(); ctx.moveTo(hx, top + 22); ctx.lineTo(hx - sw * 0.8, top + 36); ctx.moveTo(hx, top + 22); ctx.lineTo(hx + sw * 0.8, top + 36); ctx.stroke();
    ctx.fillStyle = "#00d4ff"; rr(x + 7, top + 16, 24, 26, 8); ctx.fill();
    ctx.fillStyle = "#39ff14"; ctx.beginPath(); ctx.arc(hx, top + 9, 10, 0, 7); ctx.fill();
    ctx.fillStyle = "#fff"; ctx.fillRect(hx + 2, top + 5, 10, 5);
  }
  ctx.restore();
}
function draw() {
  ctx.save();
  if (g.shake > 0) ctx.translate((Math.random() - 0.5) * 16 * g.shake, (Math.random() - 0.5) * 16 * g.shake);
  drawBackground();
  for (const c of g.cn) drawCoin(c);
  for (const o of g.obs) drawObs(o);
  drawPlayer();
  ctx.fillStyle = "#ffd60a"; ctx.font = "bold 16px sans-serif"; ctx.textAlign = "center";
  for (const p of g.pop) { ctx.globalAlpha = 1 - p.t / 0.7; ctx.fillText("+50", p.x, GY - p.h - 18 - p.t * 40); }
  ctx.globalAlpha = 1; ctx.restore();
}

/* ---------------- HUD + main loop ---------------- */
const cache = {};
function setHud(id, v) { if (cache[id] !== v) { cache[id] = v; document.getElementById(id).textContent = v; } }
function hud() {
  setHud("hs", score()); setHud("hc", g.coins); setHud("hd", Math.floor(g.dist) + " m");
  setHud("hv", Math.round(g.speed * 0.25) + " km/h"); setHud("hl", lvl()); setHud("hb", best);
}
let last = 0;
function frame(ts) {
  const dt = Math.min((ts - last) / 1000 || 0, 0.05);   // clamp so tab switches never teleport
  last = ts;
  update(dt); draw(); hud();
  requestAnimationFrame(frame);
}
reset(); menuScreen();
document.getElementById("sbtn").textContent = soundLabel();
requestAnimationFrame(frame);
})();
</script></body></html>
"""


def render_game(difficulty: str, sound: bool) -> None:
    """Embed the game. All gameplay runs in the browser, not in Streamlit reruns."""
    config = {"difficulty": difficulty, "sound": sound, "profiles": PROFILES}
    html = GAME_HTML.replace("__CONFIG__", json.dumps(config))
    components.html(html, height=660, scrolling=False)


def main() -> None:
    st.markdown(PAGE_CSS, unsafe_allow_html=True)
    st.markdown('<h1 class="sr-title">SPEED RUNNER</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sr-sub">ENDLESS ADVENTURE</p>', unsafe_allow_html=True)

    st.session_state.setdefault("difficulty", "Normal")
    st.session_state.setdefault("sound", True)

    c1, c2, c3, c4, c5 = st.columns([2, 1, 1, 1, 1])
    with c1:
        st.selectbox("Difficulty", ["Easy", "Normal", "Hard"], key="difficulty",
                     help="Changing this restarts the game area with the new settings.")
    with c2:
        st.toggle("Sound", key="sound")

    key = st.session_state.difficulty.lower()
    prof = PROFILES[key]
    c3.metric("Start speed", f"{round(prof['v0'] * 0.25)} km/h")
    c4.metric("Top speed", f"{round(prof['vmax'] * 0.25)} km/h")
    c5.metric("Obstacles", FREQUENCY[key])

    st.info("👆 Click the game area first so it receives keyboard input, then press "
            "**Play Game** (or Enter). Best score is saved in your browser.")

    try:
        render_game(key, st.session_state.sound)
    except Exception as exc:  # friendly error handling
        st.error(f"Sorry, the game could not be loaded: {exc}")
        st.caption("Try refreshing the page or upgrading Streamlit: pip install -U streamlit")

    with st.expander("How to play"):
        st.markdown(
            "- **Space / ↑** jump (no double jumps)\n"
            "- **↓** slide under overhead gates\n"
            "- **P** pause/resume, **R** restart, **M** sound, **Enter** start\n"
            "- **Touch:** tap to jump, swipe down to slide\n"
            "- Collect coins (+50 each). Speed and obstacle frequency rise as you run farther."
        )


main()
