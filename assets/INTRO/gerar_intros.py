"""
Gerador de intros Camis GameDev (YouTube 16:9 e Shorts 9:16).

- Trilha sonora 100% original, sintetizada do zero com numpy (ondas quadradas,
  triangulares e ruído estilo chiptune). Nenhum sample ou música de terceiros
  é usado, portanto o áudio é livre de direitos autorais de terceiros.
- Animação montada com os assets oficiais da marca (assets/LOGOTIPO,
  assets/SÍMBOLOS, assets/FONT).
- Tema claro como padrão (identidade da marca) e variante escura opcional.

Uso:
    pip install numpy pillow imageio-ffmpeg
    python assets/INTRO/gerar_intros.py                 # gera tudo (claro + escuro)
    python assets/INTRO/gerar_intros.py --tema claro    # apenas tema claro
    python assets/INTRO/gerar_intros.py --preview DIR   # salva frames-chave em DIR
"""

import argparse
import math
import subprocess
import wave
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
import imageio_ffmpeg

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
A = ROOT / "assets"
LOGO_DIR = A / "LOGOTIPO" / "RGB (USO PARA WEB)" / "SEM FUNDO"
SYM_DIR = A / "SÍMBOLOS"
FONT_DIR = A / "FONT"

ROXO = (97, 41, 224)
AMARELO = (255, 163, 0)
FPS = 60

TEMAS = {
    "claro": dict(bg=(250, 250, 252), dots=(*ROXO, 20), track=(236, 231, 251),
                  muted=(100, 116, 139), logo="AMARELO E ROXO.png", bracket="COLCHETE ROXO.png",
                  pill_bg=ROXO, pill_fg=(255, 255, 255), glow=(*ROXO, 38)),
    "escuro": dict(bg=(15, 10, 31), dots=(*AMARELO, 18), track=(42, 32, 74),
                   muted=(203, 213, 225), logo="BRANCO E AMARELO.png", bracket="COLCHETE AMARELO.png",
                   pill_bg=AMARELO, pill_fg=(15, 10, 31), glow=(*ROXO, 90)),
}

# Linha do tempo (segundos). s16 = duração de uma semicolcheia.
FORMATOS = {
    "youtube": dict(W=1920, H=1080, dur=5.0, s16=0.1, arp=[72, 76, 79, 84, 76, 79, 84, 88],
                    hit=0.8, coins=[0.9, 1.05, 1.2, 1.35], x0=1.6, chords="FGaG", lvl=3.4,
                    fade0=4.6, logo_w=880, cy=420, tag_y=640, bar_y=750, bar_w=760, bar_h=34,
                    lvl_y=850, url_y=1010, tag_size=34, sym_scale=1.0,
                    syms=[("+ ROXO.png", .17, .20, 90), ("X AMARELO.png", .84, .19, 80),
                          ("ESTRELA AMARELA.png", .11, .70, 110), ("ESTRELA ROXA.png", .89, .73, 100),
                          ("+ AMARELO.png", .70, .09, 60), ("X ROXO.png", .29, .90, 64)]),
    "shorts": dict(W=1080, H=1920, dur=2.4, s16=0.075, arp=[72, 76, 79, 84],
                   hit=0.3, coins=[0.375, 0.45, 0.525], x0=0.6, chords="FG", lvl=1.35,
                   fade0=2.05, logo_w=700, cy=800, tag_y=1015, bar_y=1125, bar_w=640, bar_h=32,
                   lvl_y=1225, url_y=1350, tag_size=36, sym_scale=1.0,
                   syms=[("+ ROXO.png", .20, .29, 96), ("X AMARELO.png", .80, .31, 84),
                         ("ESTRELA AMARELA.png", .14, .63, 110), ("ESTRELA ROXA.png", .86, .61, 104),
                         ("+ AMARELO.png", .68, .24, 64), ("X ROXO.png", .32, .68, 66)]),
}

# ----------------------------------------------------------------------------
# ÁUDIO (síntese chiptune original)
# ----------------------------------------------------------------------------
SR = 44100
OS = 4                      # oversampling para reduzir aliasing
SRO = SR * OS
RNG = np.random.default_rng(7)


def mtof(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def osc(kind, freq, n, duty=0.5):
    f = np.broadcast_to(np.asarray(freq, dtype=float), (n,))
    ph = np.cumsum(f) / SRO % 1.0
    if kind == "square":
        return np.where(ph < duty, 1.0, -1.0)
    if kind == "tri":
        return 4 * np.abs(ph - 0.5) - 1
    return np.sin(2 * np.pi * ph)


def adsr(n, a=0.003, d=0.1, s=0.5, r=0.03):
    t = np.arange(n) / SRO
    dur = n / SRO
    e = np.minimum(t / a, 1.0) if a > 0 else np.ones(n)
    e = e * (s + (1 - s) * np.exp(-np.maximum(t - a, 0) / d))
    if r > 0:
        e = e * np.clip((dur - t) / r, 0, 1)
    return e


class Track:
    def __init__(self, dur):
        self.buf = np.zeros(int((dur + 0.5) * SRO))

    def add(self, sig, start):
        i = int(start * SRO)
        if i >= len(self.buf):
            return
        sig = sig[: len(self.buf) - i]
        self.buf[i:i + len(sig)] += sig


def note(tr, m, start, dur, kind="square", duty=0.5, vol=0.2, a=0.003, d=0.1, s=0.5, r=0.03, vib=0.0):
    n = int(dur * SRO)
    f = mtof(m)
    if vib:
        t = np.arange(n) / SRO
        f = f * (1 + vib * np.sin(2 * np.pi * 6 * t) * np.minimum(t / 0.15, 1))
    tr.add(osc(kind, f, n, duty) * adsr(n, a, d, s, r) * vol, start)


def kick(tr, t0, vol=0.5):
    n = int(0.25 * SRO)
    t = np.arange(n) / SRO
    f = 45 + 120 * np.exp(-t / 0.03)
    tr.add(osc("sine", f, n) * np.exp(-t / 0.09) * vol, t0)


def noise(n):
    return RNG.uniform(-1, 1, n)


def hat(tr, t0, vol=0.08):
    n = int(0.05 * SRO)
    t = np.arange(n) / SRO
    x = np.diff(noise(n + 1))
    tr.add(x * np.exp(-t / 0.012) * vol, t0)


def snare(tr, t0, vol=0.2):
    n = int(0.2 * SRO)
    t = np.arange(n) / SRO
    x = np.diff(noise(n + 1)) * 0.7 + osc("tri", 190, n) * 0.5
    tr.add(x * np.exp(-t / 0.05) * vol, t0)


def crash(tr, t0, vol=0.1, dur=1.3):
    n = int(dur * SRO)
    t = np.arange(n) / SRO
    x = np.diff(noise(n + 1))
    tr.add(x * np.exp(-t / 0.45) * vol, t0)


def coin(tr, t0, k):
    m = 81 + [0, 2, 4, 5, 7][k % 5]
    note(tr, m, t0, 0.05, "square", 0.5, 0.07, d=1, s=1, r=0.005)
    note(tr, m + 7, t0 + 0.05, 0.22, "square", 0.5, 0.07, d=0.08, s=0.0, r=0.02)


CHORDS = {  # raiz do baixo, tríade
    "F": (41, (65, 69, 72)), "G": (43, (67, 71, 74)), "a": (45, (69, 72, 76)), "C": (36, (60, 64, 67)),
}
MELODIA = {"F": (81, 84), "G": (83, 86), "a": (84, 88)}


def compor(F):
    s = F["s16"]
    beat = 4 * s
    tr = Track(F["dur"])

    # 1) Arpejo de abertura (colchetes entrando)
    for i, m in enumerate(F["arp"]):
        note(tr, m, i * s, s * 0.95, "square", 0.25, 0.10 + 0.008 * i, d=0.08, s=0.4)
        hat(tr, i * s, 0.04)

    # 2) Impacto do logo
    hit = F["hit"]
    for m in (60, 64, 67, 72):
        note(tr, m, hit, 0.7, "square", 0.5, 0.045, d=0.2, s=0.0, r=0.05)
    note(tr, 36, hit, 0.6, "tri", vol=0.4, d=0.3, s=0.2)
    note(tr, 48, hit, 0.4, "tri", vol=0.2, d=0.2, s=0.1)
    kick(tr, hit, 0.6)
    crash(tr, hit, 0.09)

    # 3) Moedas (símbolos aparecendo)
    for k, tc in enumerate(F["coins"]):
        coin(tr, tc, k)

    # 4) Groove enquanto a barra de XP enche
    x0 = F["x0"]
    prog = F["chords"]
    for b, c in enumerate(prog):
        tb = x0 + b * beat
        root, triad = CHORDS[c]
        kick(tr, tb, 0.45)
        if b % 2 == 1:
            snare(tr, tb, 0.18)
        for e in range(2):
            te = tb + e * 2 * s
            note(tr, root + 12 * e, te, 2 * s * 0.9, "tri", vol=0.33, d=0.12, s=0.6)
            hat(tr, te + s, 0.06)
            note(tr, MELODIA[c][e], te, 2 * s * 0.92, "square", 0.125, 0.085, d=0.12, s=0.5)
        for m in triad:
            note(tr, m, tb, beat * 0.95, "square", 0.5, 0.022, d=0.15, s=0.3)
    # tom de "progresso" subindo junto com a barra
    x1 = x0 + len(prog) * beat
    n = int((x1 - x0) * SRO)
    f = np.geomspace(mtof(72), mtof(96), n)
    tr.add(osc("sine", f, n) * adsr(n, 0.05, 10, 1, 0.05) * 0.035, x0)

    # 5) Fanfarra LEVEL UP
    trip = (F["lvl"] - x1) / 3
    for i in range(3):
        note(tr, 79, x1 + i * trip, trip * 0.85, "square", 0.25, 0.11, d=0.1, s=0.6)
        snare(tr, x1 + i * trip, 0.08)
    lvl = F["lvl"]
    tail = F["dur"] - lvl
    note(tr, 84, lvl, tail * 0.85, "square", 0.25, 0.12, d=0.5, s=0.25, r=0.2, vib=0.006)
    for m in (72, 76, 79):
        note(tr, m, lvl, tail * 0.9, "square", 0.5, 0.035, d=0.6, s=0.15, r=0.2)
    note(tr, 36, lvl, tail * 0.8, "tri", vol=0.4, d=0.5, s=0.2, r=0.2)
    note(tr, 48, lvl, tail * 0.6, "tri", vol=0.2, d=0.4, s=0.1, r=0.1)
    kick(tr, lvl, 0.6)
    crash(tr, lvl, 0.11)
    for i, m in enumerate((96, 100, 103, 108)):
        note(tr, m, lvl + 0.05 + i * 0.045, 0.12, "square", 0.125, 0.045, d=0.05, s=0.0)

    # Mixagem / masterização
    x = np.convolve(tr.buf, np.ones(8) / 8, mode="same")[::OS]
    x = x[: int(F["dur"] * SR)]
    x = np.convolve(x, [0.25, 0.5, 0.25], mode="same")      # suaviza agudos das quadradas
    x = x / (np.max(np.abs(x)) + 1e-9) * 0.95
    x = np.tanh(1.3 * x) / np.tanh(1.3)
    fade = int(0.04 * SR)
    x[-fade:] *= np.linspace(1, 0, fade)
    x *= 0.891                                                # pico ~ -1 dBFS
    return x


def salvar_wav(path, x):
    pcm = (np.clip(x, -1, 1) * 32767).astype("<i2")
    stereo = np.repeat(pcm[:, None], 2, axis=1)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(stereo.tobytes())


# ----------------------------------------------------------------------------
# VÍDEO
# ----------------------------------------------------------------------------
def load(p):
    im = Image.open(p).convert("RGBA")
    return im.crop(im.getbbox())


def fit_w(im, w):
    return im.resize((w, max(1, round(im.height * w / im.width))), Image.LANCZOS)


def fit_h(im, h):
    return im.resize((max(1, round(im.width * h / im.height)), h), Image.LANCZOS)


def clamp01(x):
    return max(0.0, min(1.0, x))


def ease_out_cubic(x):
    x = clamp01(x)
    return 1 - (1 - x) ** 3


def ease_in_out_cubic(x):
    x = clamp01(x)
    return 4 * x ** 3 if x < 0.5 else 1 - (-2 * x + 2) ** 3 / 2


def ease_out_back(x, k=1.70158):
    x = clamp01(x)
    return 1 + (k + 1) * (x - 1) ** 3 + k * (x - 1) ** 2


def lerp(a, b, t):
    return a + (b - a) * t


def with_alpha(im, alpha):
    if alpha >= 0.999:
        return im
    im = im.copy()
    im.putalpha(im.getchannel("A").point(lambda v: int(v * alpha)))
    return im


def put(canvas, im, cx, cy, scale=1.0, alpha=1.0, angle=0.0):
    if scale <= 0.01 or alpha <= 0.01:
        return
    if abs(scale - 1) > 1e-3:
        im = im.resize((max(1, round(im.width * scale)), max(1, round(im.height * scale))), Image.BICUBIC)
    if angle:
        im = im.rotate(angle, resample=Image.BICUBIC, expand=True)
    im = with_alpha(im, alpha)
    x, y = round(cx - im.width / 2), round(cy - im.height / 2)
    W, H = canvas.size
    l, t = max(0, -x), max(0, -y)
    r, b = min(im.width, W - x), min(im.height, H - y)
    if r <= l or b <= t:
        return
    canvas.alpha_composite(im.crop((l, t, r, b)), (x + l, y + t))


def font(name, size):
    return ImageFont.truetype(str(FONT_DIR / name), size)


def text_img(txt, fnt, fill, stroke=0, stroke_fill=None, pad=8):
    d = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    l, t, r, b = d.textbbox((0, 0), txt, font=fnt, stroke_width=stroke)
    im = Image.new("RGBA", (r - l + 2 * pad, b - t + 2 * pad), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((pad - l, pad - t), txt, font=fnt, fill=fill,
                            stroke_width=stroke, stroke_fill=stroke_fill)
    return im


def pill(txt, fnt, bg, fg, px=34, py=16):
    t = text_img(txt, fnt, fg, pad=0)
    w, h = t.width + 2 * px, t.height + 2 * py
    sc = 3
    big = Image.new("RGBA", (w * sc, h * sc), (0, 0, 0, 0))
    ImageDraw.Draw(big).rounded_rectangle((0, 0, w * sc - 1, h * sc - 1), radius=h * sc // 2, fill=bg)
    im = big.resize((w, h), Image.LANCZOS)
    im.alpha_composite(t, (px, py))
    return im


def rounded_mask(w, h, sc=3):
    big = Image.new("L", (w * sc, h * sc), 0)
    ImageDraw.Draw(big).rounded_rectangle((0, 0, w * sc - 1, h * sc - 1), radius=h * sc // 2, fill=255)
    return big.resize((w, h), Image.LANCZOS)


def gradient(w, h, c0, c1):
    # mistura em luz linear (gamma-correta): transição roxo -> amarelo sem tons "barrentos"
    x = np.linspace(0, 1, w)[None, :, None]
    l0 = (np.array(c0, float) / 255) ** 2.2
    l1 = (np.array(c1, float) / 255) ** 2.2
    lin = l0[None, None, :] * (1 - x) + l1[None, None, :] * x
    arr = np.repeat(lin ** (1 / 2.2) * 255, h, axis=0).astype(np.uint8)
    return Image.fromarray(arr, "RGB").convert("RGBA")


def dot_tile(W, H, color, step=48, r=3):
    im = Image.new("RGBA", (W + step, H + step), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for y in range(0, H + step, step):
        for x in range(0, W + step, step):
            d.ellipse((x - r, y - r, x + r, y + r), fill=color)
    return im


class Cena:
    def __init__(self, F, tema):
        self.F, self.T = F, TEMAS[tema]
        W, H = F["W"], F["H"]
        self.bg = Image.new("RGBA", (W, H), (*self.T["bg"], 255))
        self.dots = dot_tile(W, H, self.T["dots"])

        self.logo = fit_w(load(LOGO_DIR / self.T["logo"]), F["logo_w"])
        lw, lh = self.logo.size
        br = load(SYM_DIR / self.T["bracket"])
        self.br_l = fit_h(br, int(lh * 1.25))
        self.br_r = self.br_l.transpose(Image.FLIP_LEFT_RIGHT)
        self.br_final = lw / 2 + 0.06 * lw + self.br_l.width / 2

        g = Image.new("RGBA", (int(lw * 1.6), int(lh * 2.6)), (0, 0, 0, 0))
        ImageDraw.Draw(g).ellipse((g.width * .12, g.height * .2, g.width * .88, g.height * .8), fill=self.T["glow"])
        self.glow = g.filter(ImageFilter.GaussianBlur(60))

        self.syms = []
        for i, (name, rx, ry, size) in enumerate(F["syms"]):
            im = fit_w(load(SYM_DIR / name), int(size * F["sym_scale"]))
            t_pop = F["coins"][i % len(F["coins"])] + (0.05 if i >= len(F["coins"]) else 0)
            self.syms.append((im, rx * W, ry * H, t_pop, (-1) ** i * (14 + 6 * i), i * 1.3))
        self.star_small = [fit_w(load(SYM_DIR / "ESTRELA AMARELA.png"), 38),
                           fit_w(load(SYM_DIR / "ESTRELA ROXA.png"), 34)]

        self.tag = pill("PROGRAMAÇÃO & GAME DEV", font("Raleway/static/Raleway-ExtraBold.ttf", F["tag_size"]),
                        self.T["pill_bg"], self.T["pill_fg"])
        self.url = text_img("cmbelem.vercel.app", font("Raleway/static/Raleway-SemiBold.ttf", 28), self.T["muted"])
        self.lvl_txt = text_img("LEVEL UP!", font("Bungee/Bungee-Regular.ttf", 64 if W > H else 72),
                                AMARELO, stroke=6, stroke_fill=ROXO)
        self.f_bar = font("Bungee/Bungee-Regular.ttf", 28)
        self.xp_lbl = text_img("XP", self.f_bar, ROXO if tema == "claro" else AMARELO)

        bw, bh = F["bar_w"], F["bar_h"]
        self.track = Image.new("RGBA", (bw, bh), (*self.T["track"], 255))
        self.track.putalpha(rounded_mask(bw, bh))
        self.grad = gradient(bw, bh, ROXO, AMARELO)
        hl = Image.new("RGBA", (bw, bh), (0, 0, 0, 0))
        ImageDraw.Draw(hl).rounded_rectangle((bh * .35, 4, bw - bh * .35, bh * .38), radius=bh // 4,
                                             fill=(255, 255, 255, 70))
        self.grad.alpha_composite(hl)

    def frame(self, t):
        F = self.F
        W, H = F["W"], F["H"]
        cx, cy = W / 2, F["cy"]
        hit, lvl, x0 = F["hit"], F["lvl"], F["x0"]
        c = self.bg.copy()

        off = (t * 30) % 48
        c.alpha_composite(self.dots.crop((int(off), int(off), int(off) + W, int(off) + H)))

        # tremor no impacto e no level up
        sh = 0.0
        for th, amp in ((hit, 10), (lvl, 6)):
            if t >= th:
                sh += amp * math.exp(-(t - th) / 0.08) * math.sin((t - th) * 90)
        lcx, lcy = cx + sh, cy

        # brilho atrás do logo
        ga = ease_out_cubic((t - hit) / 0.5) * (0.85 + 0.15 * math.sin(t * 3))
        put(c, self.glow, cx, cy, 1.0, ga)

        # colchetes: entram até o centro, depois abrem revelando o logo
        bw = self.br_l.width
        closed = bw * 0.75
        start = W / 2 + bw
        p1 = ease_out_cubic(t / (hit * 0.85))
        p2 = ease_out_back((t - hit) / 0.35, 2.2)
        dist = lerp(lerp(start, closed, p1), self.br_final, p2)
        put(c, self.br_l, lcx - dist, lcy)
        put(c, self.br_r, lcx + dist, lcy)

        # logo
        if t >= hit:
            sc = ease_out_back((t - hit) / 0.45, 2.0)
            if t >= lvl:
                sc *= 1 + 0.06 * math.exp(-(t - lvl) / 0.12) * math.cos((t - lvl) * 25)
            put(c, self.logo, lcx, lcy, sc, clamp01((t - hit) / 0.12))

        # símbolos da marca (pop + flutuação)
        for im, sx, sy, tp, rot, ph in self.syms:
            if t >= tp:
                k = (t - tp)
                sc = ease_out_back(k / 0.35, 2.5)
                bob = 10 * math.sin(t * 2.2 + ph)
                put(c, im, sx, sy + bob, sc, clamp01(k / 0.1), rot * k + 8 * math.sin(t * 1.5 + ph))

        # tagline em pílula arredondada
        tt = hit + (x0 - hit) * 0.5
        if t >= tt:
            p = ease_out_back((t - tt) / 0.4)
            put(c, self.tag, cx, F["tag_y"] + 40 * (1 - p), 1.0, clamp01((t - tt) / 0.2))

        # barra de XP arredondada
        bwid, bh = F["bar_w"], F["bar_h"]
        ta = x0 - 0.15
        if t >= ta:
            a = clamp01((t - ta) / 0.2)
            bar = self.track.copy()
            x1 = x0 + len(F["chords"]) * 4 * F["s16"]
            fill = ease_in_out_cubic((t - x0) / (x1 - x0)) if t >= x0 else 0
            fw = int(bwid * fill)
            if fw >= bh // 2:
                fm = Image.new("L", (bwid, bh), 0)
                fm.paste(rounded_mask(fw, bh), (0, 0))
                fi = self.grad.copy()
                fi.putalpha(fm)
                bar.alpha_composite(fi)
            if t >= lvl:
                fl = 0.9 * math.exp(-(t - lvl) / 0.15)
                white = Image.new("RGBA", (bwid, bh), (255, 255, 255, int(255 * fl)))
                m = rounded_mask(bwid, bh)
                white.putalpha(Image.fromarray((np.array(m) * fl).astype(np.uint8)))
                bar.alpha_composite(white)
            put(c, bar, cx, F["bar_y"], 1.0, a)
            put(c, self.xp_lbl, cx - bwid / 2 - self.xp_lbl.width / 2 - 10, F["bar_y"], 1.0, a)
            pct = text_img(f"{int(round(fill * 100))}%", self.f_bar, self.T["muted"])
            put(c, pct, cx + bwid / 2 + pct.width / 2 + 10, F["bar_y"], 1.0, a)

        # LEVEL UP + explosão de estrelas
        if t >= lvl:
            k = t - lvl
            ly = F["lvl_y"]
            for i in range(12):
                ang = i / 12 * 2 * math.pi + 0.3
                d = 60 + (260 if W > H else 220) * ease_out_cubic(k / 0.7)
                put(c, self.star_small[i % 2], cx + math.cos(ang) * d * 1.4, ly + math.sin(ang) * d * 0.7,
                    1.0, clamp01(1 - k / 0.9), k * 200 * (-1) ** i)
            put(c, self.lvl_txt, cx, ly, ease_out_back(k / 0.35, 3.0), clamp01(k / 0.08))

        # assinatura
        ua = clamp01((t - hit - 0.4) / 0.4)
        put(c, self.url, cx, F["url_y"], 1.0, ua)

        # fade final para a cor de fundo
        if t >= F["fade0"]:
            fa = clamp01((t - F["fade0"]) / (F["dur"] - F["fade0"]))
            c = Image.blend(c, self.bg, ease_in_out_cubic(fa))
        return c.convert("RGB")


def render(fmt, tema, preview_dir=None):
    F = FORMATOS[fmt]
    out_dir = HERE
    wav = out_dir / f"trilha_{fmt}.wav"
    if not wav.exists():
        salvar_wav(wav, compor(F))
    mp4 = out_dir / f"intro_{fmt}_{tema}_{F['W']}x{F['H']}.mp4"
    cena = Cena(F, tema)
    n = int(round(F["dur"] * FPS))
    cmd = [imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "error",
           "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{F['W']}x{F['H']}", "-r", str(FPS), "-i", "-",
           "-i", str(wav), "-c:v", "libx264", "-preset", "slow", "-crf", "17", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", str(mp4)]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    keys = {round(F["hit"] - 0.15, 2), round(F["coins"][-1] + 0.2, 2), round((F["x0"] + F["lvl"]) / 2, 2),
            round(F["lvl"] + 0.35, 2), round(F["fade0"] - 0.05, 2)}
    for i in range(n):
        t = i / FPS
        img = cena.frame(t)
        proc.stdin.write(img.tobytes())
        if preview_dir and any(abs(t - k) < 0.5 / FPS for k in keys):
            img.save(Path(preview_dir) / f"{fmt}_{tema}_{t:.2f}s.png")
    proc.stdin.close()
    proc.wait()
    print("OK:", mp4.name)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--tema", choices=["claro", "escuro", "todos"], default="todos")
    ap.add_argument("--formato", choices=["youtube", "shorts", "todos"], default="todos")
    ap.add_argument("--preview", default=None)
    args = ap.parse_args()
    temas = ["claro", "escuro"] if args.tema == "todos" else [args.tema]
    fmts = ["youtube", "shorts"] if args.formato == "todos" else [args.formato]
    if args.preview:
        Path(args.preview).mkdir(parents=True, exist_ok=True)
    for f in fmts:
        (HERE / f"trilha_{f}.wav").unlink(missing_ok=True)
        for tm in temas:
            render(f, tm, args.preview)
