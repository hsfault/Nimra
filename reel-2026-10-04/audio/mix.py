"""Builds the reel soundtrack: synthesized music bed + sound design + voice-over.

Everything is generated from timeline.json so audio and picture share one clock.
Output: build/mix.wav (48 kHz stereo, pre-loudness-normalisation).
"""
import json
import os

import numpy as np
import soundfile as sf
from scipy.signal import butter, fftconvolve, lfilter, resample_poly, sosfilt

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SR = 48000
TL = json.load(open(os.path.join(ROOT, "timeline.json")))
DUR = TL["duration"]
N = int(DUR * SR)
rng = np.random.default_rng(4)


def t_axis(d):
    return np.arange(int(d * SR)) / SR


def env_ad(n, a, d):
    """Linear attack (s) then exponential decay with time constant d (s)."""
    t = np.arange(n) / SR
    e = np.exp(-np.maximum(t - a, 0) / d)
    if a > 0:
        e *= np.clip(t / a, 0, 1)
    return e


def bp(x, lo, hi, order=2):
    sos = butter(order, [lo, hi], btype="band", fs=SR, output="sos")
    return sosfilt(sos, x)


def lp(x, f, order=2):
    return sosfilt(butter(order, f, btype="low", fs=SR, output="sos"), x)


def hp(x, f, order=2):
    return sosfilt(butter(order, f, btype="high", fs=SR, output="sos"), x)


def sweep_bp(x, f0, f1, q=2.5, block=256):
    """Band-pass whose centre glides exponentially from f0 to f1 (whoosh/riser core)."""
    out = np.zeros_like(x)
    nb = len(x) // block + 1
    zi = None
    for i in range(nb):
        s = slice(i * block, (i + 1) * block)
        if s.start >= len(x):
            break
        f = f0 * (f1 / f0) ** (i / max(nb - 1, 1))
        lo, hi = f / (1 + 1 / q), min(f * (1 + 1 / q), SR / 2 - 100)
        b, a = butter(2, [lo, hi], btype="band", fs=SR)
        if zi is None or len(zi) != max(len(a), len(b)) - 1:
            zi = np.zeros(max(len(a), len(b)) - 1)
        out[s], zi = lfilter(b, a, x[s], zi=zi)
    return out


def glide_sine(f0, f1, d, curve="exp"):
    t = t_axis(d)
    f = f0 * (f1 / f0) ** (t / d) if curve == "exp" else f0 + (f1 - f0) * t / d
    return np.sin(2 * np.pi * np.cumsum(f) / SR)


def norm(x, peak=1.0):
    m = np.max(np.abs(x)) or 1
    return x / m * peak


# ---------------------------------------------------------------- sound effects (mono)
def sfx_whoosh(d=0.7):
    n = rng.standard_normal(int(d * SR))
    x = sweep_bp(n, 250, 4200, q=1.6)
    t = t_axis(d)
    e = np.sin(np.pi * np.clip(t / d, 0, 1)) ** 2.2
    e = e * np.clip((t / d) / 0.6, 0, 1) ** 0.5
    return norm(x * e) * 0.8


def sfx_boom(d=2.2):
    t = t_axis(d)
    body = np.sin(2 * np.pi * np.cumsum(32 + 63 * np.exp(-t / 0.18)) / SR)
    body *= env_ad(len(t), 0.004, 0.65)
    click = lp(rng.standard_normal(len(t)), 1800) * env_ad(len(t), 0.001, 0.03) * 0.5
    air = lp(rng.standard_normal(len(t)), 400) * env_ad(len(t), 0.01, 0.5) * 0.35
    return norm(body + click + air)


def sfx_ping(d=0.9):
    t = t_axis(d)
    x = (np.sin(2 * np.pi * 1318.5 * t) + 0.6 * np.sin(2 * np.pi * 1975.5 * t) + 0.18 * np.sin(2 * np.pi * 3951 * t))
    x *= env_ad(len(t), 0.003, 0.22)
    return norm(x) * 0.7


def sfx_riser(d):
    t = t_axis(d)
    n = sweep_bp(rng.standard_normal(len(t)), 300, 7000, q=1.2)
    tone = np.sin(2 * np.pi * np.cumsum(180 * (4.0 ** (t / d))) / SR) * 0.35
    e = (t / d) ** 2.4
    return norm((n + tone) * e) * 0.9


def sfx_scribble(d=0.38):
    t = t_axis(d)
    n = bp(rng.standard_normal(len(t)), 1800, 5200)
    am = 0.5 + 0.5 * np.sign(np.sin(2 * np.pi * 23 * t + 2 * np.sin(2 * np.pi * 5 * t)))
    e = np.sin(np.pi * t / d) ** 0.7
    return norm(n * (0.35 + 0.65 * am) * e) * 0.7


def sfx_thud(d=0.8):
    t = t_axis(d)
    body = np.sin(2 * np.pi * np.cumsum(45 + 45 * np.exp(-t / 0.05)) / SR) * env_ad(len(t), 0.002, 0.16)
    knock = bp(rng.standard_normal(len(t)), 150, 1400) * env_ad(len(t), 0.0005, 0.025)
    return norm(body + 0.7 * knock)


def sfx_sparkle(d=0.9):
    x = np.zeros(int(d * SR))
    for i in range(7):
        st = int(rng.uniform(0, d * 0.6) * SR)
        f = rng.uniform(2800, 6200)
        tt = t_axis(0.3)
        b = np.sin(2 * np.pi * f * tt) * env_ad(len(tt), 0.002, 0.07)
        x[st:st + len(b)] += b[: len(x) - st]
    return norm(x) * 0.55


def sfx_tick(d=0.06):
    t = t_axis(d)
    x = bp(rng.standard_normal(len(t)), 2500, 6000) * env_ad(len(t), 0.0003, 0.006)
    x += 0.4 * np.sin(2 * np.pi * 2300 * t) * env_ad(len(t), 0.0003, 0.008)
    return norm(x) * 0.6


def sfx_ticks():
    """Clock ticks that speed up across the 'every errand hour' scene."""
    d = 2.8
    x = np.zeros(int(d * SR))
    tt, gap = 0.0, 0.3
    k = 0
    while tt < d - 0.1:
        tk = sfx_tick() * (1.0 if k % 2 == 0 else 0.7)
        s = int(tt * SR)
        x[s:s + len(tk)] += tk[: len(x) - s]
        tt += gap
        gap = max(0.09, gap * 0.9)
        k += 1
    return x * np.linspace(0.7, 1, len(x))


def sfx_down(d=1.1):
    t = t_axis(d)
    x = np.sin(2 * np.pi * np.cumsum(330 * (1 / 3) ** (t / d)) / SR)
    x += 0.3 * np.sin(2 * np.pi * np.cumsum(660 * (1 / 3) ** (t / d)) / SR)
    return norm(x * env_ad(len(t), 0.01, 0.45)) * 0.6


def sfx_whir(d=1.3):
    t = t_axis(d)
    n = sweep_bp(rng.standard_normal(len(t)), 400, 1600, q=3)
    tone = np.sin(2 * np.pi * np.cumsum(140 + 120 * t / d) / SR) * (0.5 + 0.5 * np.sin(2 * np.pi * 18 * t))
    e = np.sin(np.pi * t / d) ** 1.5
    return norm((0.6 * n + 0.4 * tone) * e) * 0.7


def sfx_pop(d=0.12):
    t = t_axis(d)
    x = np.sin(2 * np.pi * np.cumsum(300 + 500 * np.exp(-t / 0.015)) / SR) * env_ad(len(t), 0.001, 0.03)
    return norm(x) * 0.7


def sfx_shing(d=1.4):
    t = t_axis(d)
    x = sum(a * np.sin(2 * np.pi * f * t) for f, a in [(2210, 1), (3170, .7), (4480, .5), (5330, .35), (6890, .2)])
    x *= env_ad(len(t), 0.004, 0.32)
    x += sweep_bp(rng.standard_normal(len(t)), 6000, 2500, q=2) * env_ad(len(t), 0.002, 0.08) * 0.6
    return norm(x) * 0.5


def sfx_chime(d=2.6):
    t = t_axis(d)
    f = 1174.66
    x = sum(a * np.sin(2 * np.pi * f * r * t) * np.exp(-t / (0.9 / r ** 0.6)) for r, a in [(1, 1), (2.0, .4), (2.76, .35), (5.4, .15)])
    x *= np.clip(t / 0.003, 0, 1)
    return norm(x) * 0.7


def sfx_typing():
    x = np.zeros(int(0.9 * SR))
    for i, st in enumerate([0, .13, .26, .5, .63, .76]):
        tk = sfx_tick(0.05) * 0.5
        s = int(st * SR)
        x[s:s + len(tk)] += tk
    return lp(x, 4500)


def sfx_shimmer(d=1.6):
    t = t_axis(d)
    x = np.zeros(len(t))
    for f in [2349, 2794, 3520, 4186, 4699, 5588]:
        x += np.sin(2 * np.pi * f * t + rng.uniform(0, 6)) * (0.5 + 0.5 * np.sin(2 * np.pi * rng.uniform(5, 9) * t))
    e = np.sin(np.pi * np.clip(t / d, 0, 1)) ** 2
    return norm(x * e) * 0.45


SFX = {
    "whoosh": sfx_whoosh, "boom": sfx_boom, "riser": sfx_riser, "ping": sfx_ping, "scribble": sfx_scribble, "thud": sfx_thud,
    "sparkle": sfx_sparkle, "ticks": sfx_ticks, "down": sfx_down, "whir": sfx_whir, "pop": sfx_pop,
    "shing": sfx_shing, "chime": sfx_chime, "typing": sfx_typing, "shimmer": sfx_shimmer, "tick": sfx_tick,
}


# ---------------------------------------------------------------- music bed
def midi(n):
    return 440.0 * 2 ** ((n - 69) / 12)


BPM = 96
BEAT = 60 / BPM
BAR = 4 * BEAT
# Dm(add9) - Bbmaj7 - F/A - Csus2  (minor, calm, cinematic)
CHORDS = [[50, 53, 57, 64], [46, 50, 53, 57], [45, 53, 57, 60], [48, 55, 60, 62]]
ROOTS = [38, 34, 33, 36]


def saw_pad(f, d):
    t = t_axis(d)
    x = np.zeros(len(t))
    for det in (-0.07, 0.0, 0.07):
        ff = f * 2 ** (det / 12)
        for h in range(1, 11):
            x += np.sin(2 * np.pi * ff * h * t + h) / h * np.exp(-h / 4.5)
    return x


def pluck(f, d=1.2):
    t = t_axis(d)
    x = np.sin(2 * np.pi * f * t) + 0.35 * np.sin(2 * np.pi * 2 * f * t) + 0.12 * np.sin(2 * np.pi * 3 * f * t)
    return x * env_ad(len(t), 0.004, 0.32)


def build_music():
    nbars = int(np.ceil(DUR / BAR)) + 1
    pad = np.zeros(int((nbars + 1) * BAR * SR) + 3 * SR)
    bass = np.zeros_like(pad)
    arp = np.zeros_like(pad)
    kick = np.zeros_like(pad)
    for b in range(nbars):
        t0 = b * BAR
        ci = b % 4
        # pad: overlapping chords with soft attack/release
        seg = sum(saw_pad(midi(n), BAR + 1.2) for n in CHORDS[ci])
        e = np.clip(np.arange(len(seg)) / (0.5 * SR), 0, 1) * np.clip((len(seg) - np.arange(len(seg))) / (1.0 * SR), 0, 1)
        s = int(t0 * SR)
        pad[s:s + len(seg)] += seg * e
        for k in range(8):  # eighth-note pulse bass + arp
            tt = t0 + k * BEAT / 2
            s = int(tt * SR)
            bt = t_axis(BEAT / 2 + 0.2)
            bn = np.sin(2 * np.pi * midi(ROOTS[ci]) * bt) + 0.3 * np.sin(2 * np.pi * 2 * midi(ROOTS[ci]) * bt)
            bn *= env_ad(len(bt), 0.008, 0.16) * (1.0 if k % 2 == 0 else 0.6)
            bass[s:s + len(bn)] += bn
            note = CHORDS[ci][[0, 2, 3, 1, 2, 3, 1, 2][k]] + 24
            p = pluck(midi(note)) * (0.9 if k % 2 == 0 else 0.6)
            arp[s:s + len(p)] += p
        for k in (0, 2):
            s = int((t0 + k * BEAT) * SR)
            kt = t_axis(0.5)
            kk = np.sin(2 * np.pi * np.cumsum(45 + 90 * np.exp(-kt / 0.03)) / SR) * env_ad(len(kt), 0.001, 0.12)
            kick[s:s + len(kk)] += kk
    pad = lp(pad, 1400, 4)
    pad, bass, arp, kick = (x[:N] for x in (pad, bass, arp, kick))
    t = np.arange(N) / SR

    def seg_env(points):
        return np.interp(t, [p[0] for p in points], [p[1] for p in points])

    # arrangement: sparse hook, build through the errands, breathe on the question, lift on the logo
    pad_g = seg_env([(0, .55), (3.8, .65), (19.3, .75), (23.4, .9), (27.5, .8), (DUR, 0)])
    bass_g = seg_env([(0, 0), (3.6, 0), (3.85, .8), (19.1, .85), (19.5, .25), (23.3, .3), (24.35, 0), (24.4, 1), (26, .6), (DUR, 0)])
    arp_g = seg_env([(0, .25), (3.8, .35), (8.2, .55), (19.2, .6), (19.5, .3), (23.4, .25), (24.4, .5), (DUR - .5, .2), (DUR, 0)])
    kick_g = seg_env([(0, 0), (8.15, 0), (8.2, .9), (19.2, .9), (19.3, 0), (DUR, 0)])
    pad_m = norm(pad) * pad_g * 0.32
    bass_m = norm(lp(bass, 300)) * bass_g * 0.38
    arp_m = norm(lp(arp, 5000)) * arp_g * 0.2
    kick_m = norm(kick) * kick_g * 0.42
    return pad_m, bass_m, arp_m, kick_m


# ---------------------------------------------------------------- helpers: reverb, pan, compressor
def reverb_ir(d=2.4, pre=0.015):
    n = int(d * SR)
    t = np.arange(n) / SR
    irs = []
    for _ in range(2):
        ir = rng.standard_normal(n) * np.exp(-t / (d / 6.9))
        ir = lp(ir, 6000)
        ir[: int(pre * SR)] = 0
        irs.append(ir / np.sqrt(np.sum(ir ** 2)))
    return irs


IR = reverb_ir()


def reverb(st):
    return np.stack([fftconvolve(st[:, c], IR[c])[: len(st)] for c in range(2)], axis=1)


def pan(x, p):
    """p in [-1, 1]; equal-power."""
    a = (p + 1) * np.pi / 4
    return np.stack([x * np.cos(a), x * np.sin(a)], axis=1)


def compress(x, thresh_db=-20, ratio=3.0, att=0.005, rel=0.12):
    env = np.abs(x)
    a_a, a_r = np.exp(-1 / (att * SR)), np.exp(-1 / (rel * SR))
    out = np.zeros_like(env)
    e = 0.0
    for i, v in enumerate(env):
        e = a_a * e + (1 - a_a) * v if v > e else a_r * e + (1 - a_r) * v
        out[i] = e
    db = 20 * np.log10(out + 1e-9)
    gain_db = np.minimum(0, (thresh_db - db) * (1 - 1 / ratio))
    return x * 10 ** (gain_db / 20)


# ---------------------------------------------------------------- voice-over
def build_vo():
    vo = np.zeros(N)
    for key, start in TL["vo"].items():
        x, sr = sf.read(os.path.join(HERE, "vo", f"{key}.wav"))
        if x.ndim > 1:
            x = x.mean(axis=1)
        x = resample_poly(x, SR, sr)
        s = int(start * SR)
        vo[s:s + len(x)] += x[: N - s]
    vo = hp(vo, 85, 2)
    # gentle presence lift + warmth
    vo = vo + 0.18 * bp(vo, 2500, 6000) + 0.1 * bp(vo, 150, 350)
    vo = compress(norm(vo), thresh_db=-18, ratio=3.0)
    return norm(vo) * 0.9


def main():
    music = build_music()
    vo = build_vo()

    # duck the music under the voice
    env = lp(np.abs(vo), 6, 1)
    env = np.clip(env / (np.max(env) * 0.5), 0, 1)
    duck = 1 - 0.55 * env

    pad_m, bass_m, arp_m, kick_m = music
    mus = pan(pad_m * duck, 0) + pan(bass_m * duck, 0) + pan(arp_m * duck, 0.25) + pan(kick_m * duck, 0)
    # stereo width on the pad via a short Haas delay
    d = int(0.012 * SR)
    mus[:, 1] = np.concatenate([np.zeros(d), mus[:-d, 1]]) * 0.5 + mus[:, 1] * 0.5

    fx = np.zeros((N, 2))
    pans = {"whoosh": None, "ping": 0.35, "pop": 0.2, "sparkle": 0.3, "shing": 0, "chime": 0, "scribble": -0.2}
    for i, (kind, at, gain, *dur) in enumerate(TL["sfx"]):
        x = SFX[kind](*dur) * gain
        s = int(at * SR)
        if s >= N:
            continue
        x = x[: N - s]
        if kind in ("whoosh", "riser"):  # moving whooshes sweep across the stereo field
            p = np.linspace(-0.7, 0.7, len(x)) * (1 if i % 2 else -1)
            a = (p + 1) * np.pi / 4
            st = np.stack([x * np.cos(a), x * np.sin(a)], axis=1)
        else:
            st = pan(x, pans.get(kind, 0) or 0)
        fx[s:s + len(st)] += st

    vo_st = pan(vo, 0)
    wet = reverb(mus * 0.5 + fx * 0.6 + vo_st * 0.12)
    mix = mus * 0.2 + fx * 0.3 + vo_st * 1.0 + wet * 0.14

    # fade tail and soft-limit
    t = np.arange(N) / SR
    mix *= np.clip((DUR - t) / 0.6, 0, 1)[:, None]
    scale = 1.4 / np.max(np.abs(mix))
    if os.environ.get("STEMS"):
        bed = mus * 0.2 + fx * 0.3 + wet * 0.14
        for name, st in (("vo", vo_st), ("bed", bed)):
            sf.write(os.path.join(ROOT, "build", f"stem_{name}.wav"), (st * scale / np.tanh(1.4) * 0.95).astype(np.float32), SR, subtype="FLOAT")
    mix = np.tanh(mix * scale) / np.tanh(1.4) * 0.95
    os.makedirs(os.path.join(ROOT, "build"), exist_ok=True)
    sf.write(os.path.join(ROOT, "build", "mix.wav"), mix.astype(np.float32), SR, subtype="FLOAT")
    print("wrote build/mix.wav", mix.shape)


if __name__ == "__main__":
    main()
