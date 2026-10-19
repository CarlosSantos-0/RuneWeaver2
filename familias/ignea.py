import math
import random
from motor.utilitarios import suavizar_esqueleto

# ==========================================================
# FEITIÇARIA ÍGNEA — A Doutrina da Transformação
# Glifos de traços fortes e afilados (lâminas de pincel, ponta aguda),
# na linha da caligrafia oriental. Cada runa nasce de UM arquétipo
# estrutural, sorteado conforme os pesos do preset:
#   lâmina    - haste alta e curva, a "língua de fogo" básica
#   fênix     - duas lâminas que se cruzam (transformação)
#   chama     - base em cuia com chamas de alturas diferentes (Chama Viva)
#   catálise  - explosão de raios a partir de um núcleo
#   brasa     - traços curtos e pesados + brasas (combustão lenta)
#   reignição - lâmina partida, com uma brasa no intervalo
# Por cima, modificadores: cruzamentos, labaredas, fagulhas e
# rugosidade (borda queimada). Tudo na cor principal da runa.
# ==========================================================


# ---------- utilidades ----------

def _reamostrar(pts, passo=0.8):
    if len(pts) < 2:
        return list(pts)
    out = [pts[0]]
    pos = passo
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        seg = math.hypot(x1 - x0, y1 - y0)
        if seg == 0:
            continue
        while pos <= seg:
            t = pos / seg
            out.append((x0 + (x1 - x0) * t, y0 + (y1 - y0) * t))
            pos += passo
        pos -= seg
    out.append(pts[-1])
    return out


def _tangente(pts, i, janela=4):
    i = max(0, min(len(pts) - 1, i))
    a = pts[max(0, i - janela)]
    b = pts[min(len(pts) - 1, i + janela)]
    dx, dy = b[0] - a[0], b[1] - a[1]
    d = math.hypot(dx, dy) or 1.0
    return dx / d, dy / d


def _comprimento(pts):
    return sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(pts, pts[1:]))


def _media_movel(v, w):
    n = len(v)
    out = []
    for i in range(n):
        a, b = max(0, i - w), min(n, i + w + 1)
        out.append(sum(v[a:b]) / (b - a))
    return out


def _dist_min_all(tracos, c):
    d = 1e9
    for t in tracos:
        for x, y in t["pts"][::3]:
            d = min(d, math.hypot(x - c[0], y - c[1]))
    return d


# ---------- lâmina de pincel ----------

def _perfil(c=0.4, ea=1.0, eb=1.6, w0=0.0, w1=0.0):
    """Largura ao longo do traço: sobe até c (expoente ea) e afina até a ponta (expoente eb).
    eb alto = ponta longa e finíssima. w0/w1 = largura relativa no começo/fim."""
    def f(t):
        if t <= c:
            x = t / c if c > 0 else 1.0
            return w0 + (1 - w0) * (x ** ea)
        x = (1 - t) / (1 - c) if c < 1 else 0.0
        return w1 + (1 - w1) * (x ** eb)
    return f


def _traco_s(pts, w, perfil, rug):
    return {"pts": _reamostrar(suavizar_esqueleto(pts, iteracoes=3), 0.8),
            "w": w, "perfil": perfil, "rug": rug}


def _traco(P, ctrl, w, perfil, rug):
    return _traco_s([P(a, b) for a, b in ctrl], w, perfil, rug)


def _desenhar(draw, pts, cor, w, perfil, rug):
    """Carimba círculos de raio variável: ponta aguda e borda irregular (queimada)."""
    pts = _reamostrar(pts, 0.8)
    n = len(pts)
    if n < 2:
        return
    rr = [v * 2.0 for v in _media_movel([random.uniform(-1, 1) for _ in range(n)], 2)]
    jx = [v * 2.0 for v in _media_movel([random.uniform(-1, 1) for _ in range(n)], 4)]
    jy = [v * 2.0 for v in _media_movel([random.uniform(-1, 1) for _ in range(n)], 4)]
    for i, (x, y) in enumerate(pts):
        t = i / (n - 1)
        r = w * 0.5 * perfil(t)
        r *= max(0.3, 1 + rug * 0.5 * rr[i])
        r = max(0.5, r)
        x += rug * 1.2 * jx[i]
        y += rug * 1.2 * jy[i]
        draw.ellipse([x - r, y - r, x + r, y + r], fill=cor)


def _brasa(draw, c, r, rug, cor):
    """Brasa: polígono irregular."""
    pts = []
    m = 11
    for k in range(m):
        a = math.tau * k / m
        rr = max(0.8, r * (1 + rug * 0.35 * random.uniform(-1, 1)))
        pts.append((c[0] + rr * math.cos(a), c[1] + rr * math.sin(a)))
    draw.polygon(pts, fill=cor)


# ---------- arquétipos (coordenadas locais: a = eixo da chama 0..1, b = lateral) ----------

def _arq_lamina(P, w, rug):
    s = random.choice([-1, 1])
    b0, b1 = random.uniform(-0.15, 0.15), random.uniform(-0.22, 0.22)
    ctrl = [(0.0, b0), (0.5, (b0 + b1) / 2 + s * random.uniform(0.08, 0.28)), (1.0, b1)]
    if random.random() < 0.5:  # pé em gancho na base
        ctrl.insert(0, (0.05, b0 - s * random.uniform(0.08, 0.16)))
    perf = _perfil(random.uniform(0.25, 0.5), random.uniform(0.7, 1.2), random.uniform(1.3, 2.2),
                   random.choice([0.0, 0.0, 0.3]), 0.0)
    return [_traco(P, ctrl, w * random.uniform(0.9, 1.15), perf, rug)], []


def _arq_fenix(P, w, rug):
    s = random.choice([-1, 1])
    cruz = random.uniform(0.40, 0.60)
    ctrl_a = [(0.05, -0.32 * s), (cruz, 0.03 * s + random.uniform(-0.06, 0.06)), (0.97, 0.26 * s)]
    ctrl_b = [(0.12, 0.34 * s), (cruz + 0.04, -0.02 * s + random.uniform(-0.06, 0.06)), (0.88, -0.30 * s)]
    tracos = [
        _traco(P, ctrl_a, w, _perfil(0.35, 0.9, random.uniform(1.4, 2.2), 0.0, 0.0), rug),
        _traco(P, ctrl_b, w * random.uniform(0.55, 0.8), _perfil(0.4, 1.0, random.uniform(1.3, 2.0), 0.25, 0.0), rug),
    ]
    if random.random() < 0.65:  # cauda
        tracos.append(_traco(P, [(cruz, 0.0), (cruz * 0.55, 0.14 * s), (0.0, 0.02 * s)],
                             w * 0.6, _perfil(0.3, 1.0, 1.3, 0.0, 0.0), rug))
    return tracos, []


def _arq_chama(P, w, rug):
    base = [(0.12, -0.55), (0.03, -0.2), (0.0, 0.05), (0.06, 0.35), (0.16, 0.58)]
    nl = random.randint(2, 4)
    lam = []
    for k in range(nl):
        b = -0.36 + 0.72 * k / (nl - 1) + random.uniform(-0.06, 0.06)
        h = random.uniform(0.6, 1.0) * (1 - 0.45 * abs(b))
        lean = b * random.uniform(0.2, 0.6) + random.uniform(-0.08, 0.08)
        bojo = random.choice([-1, 1]) * random.uniform(0.03, 0.12)
        lam.append((h, [(0.07, b), (h * 0.5, b + lean * 0.5 + bojo), (h, b + lean)]))
    lam.sort(key=lambda x: -x[0])  # a mais alta primeiro (será o traço principal)
    tracos = [_traco(P, ctrl, w * random.uniform(0.55, 0.95),
                     _perfil(0.3, 1.0, random.uniform(1.3, 2.0), 0.35, 0.0), rug) for _, ctrl in lam]
    tracos.append(_traco(P, base, w * 0.9, _perfil(0.5, 1.0, 1.0, 0.0, 0.0), rug))
    return tracos, []


def _arq_catalise(P, w, rug):
    m = random.randint(5, 8)
    ca = random.uniform(0.4, 0.55)
    off = random.uniform(0, math.tau)
    tracos = []
    for k in range(m):
        phi = off + math.tau * k / m + random.uniform(-0.3, 0.3)
        r0 = random.uniform(0.03, 0.06)
        r1 = random.uniform(0.15, 0.48) * (1 + 0.35 * math.cos(phi))
        curl = random.uniform(-0.09, 0.09)
        ctrl = [(ca + r0 * math.cos(phi), r0 * math.sin(phi)),
                (ca + 0.5 * r1 * math.cos(phi) - curl * math.sin(phi), 0.5 * r1 * math.sin(phi) + curl * math.cos(phi)),
                (ca + r1 * math.cos(phi), r1 * math.sin(phi))]
        tracos.append(_traco(P, ctrl, w * random.uniform(0.4, 0.9),
                             _perfil(0.12, 1.0, random.uniform(1.2, 1.8), 0.55, 0.0), rug))
    tracos.sort(key=lambda t: -_comprimento(t["pts"]))
    return tracos, [P(ca, 0.0) + (w * 0.55,)]


def _arq_brasa(P, w, rug):
    tracos = [_traco(P, [(0.03, -0.55), (0.0, 0.0), (0.05, 0.55)], w * 0.5, _perfil(0.5, 1.0, 1.4, 0.0, 0.0), rug)]
    m = random.randint(3, 5)
    for k in range(m):
        b = -0.42 + 0.84 * k / (m - 1) + random.uniform(-0.05, 0.05)
        a0 = random.uniform(0.1, 0.32)
        ln = random.uniform(0.1, 0.26)
        tilt = random.uniform(-0.12, 0.12)
        ctrl = [(a0, b), (a0 + ln * 0.5, b + tilt * 0.4 + random.uniform(-0.04, 0.04)), (a0 + ln, b + tilt)]
        tracos.append(_traco(P, ctrl, w * random.uniform(0.9, 1.35), _perfil(0.12, 1.0, 1.4, 0.8, 0.0), rug))
    pontos = [P(random.uniform(0.45, 0.8), random.uniform(-0.4, 0.4)) + (w * random.uniform(0.18, 0.32),)
              for _ in range(random.randint(1, 3))]
    return tracos, pontos


def _arq_reignicao(P, w, rug):
    s = random.choice([-1, 1])
    bm = random.uniform(-0.1, 0.1)
    corte = random.uniform(0.38, 0.48)
    low = [(0.0, bm - 0.1 * s), (corte * 0.5, bm + 0.1 * s * random.uniform(0.5, 1.5)), (corte, bm)]
    up = [(corte + 0.12, bm + random.uniform(-0.06, 0.06)),
          (0.75, bm - 0.1 * s * random.uniform(0.3, 1.2)),
          (1.0, bm + random.uniform(-0.2, 0.2))]
    tracos = [
        _traco(P, up, w * 1.05, _perfil(0.45, 0.9, random.uniform(1.4, 2.2), 0.0, 0.0), rug),
        _traco(P, low, w * 0.95, _perfil(0.5, 1.0, 1.5, random.choice([0.0, 0.3]), 0.1), rug),
    ]
    return tracos, [P(corte + 0.06, bm + random.uniform(-0.03, 0.03)) + (w * 0.5,)]


# ---------- modificadores ----------

def _cruzar(main, H, w, rug):
    n = len(main)
    i = random.randint(int(n * 0.25), int(n * 0.7))
    p = main[i]
    tx, ty = _tangente(main, i)
    ang = random.choice([-1, 1]) * math.radians(random.uniform(35, 75))
    c, s = math.cos(ang), math.sin(ang)
    dx, dy = tx * c - ty * s, tx * s + ty * c
    comp = H * random.uniform(0.18, 0.42)
    atras = random.uniform(0.2, 0.45)
    bj = random.choice([-1, 1]) * comp * 0.12
    p0 = (p[0] - dx * comp * atras, p[1] - dy * comp * atras)
    p3 = (p[0] + dx * comp * (1 - atras), p[1] + dy * comp * (1 - atras))
    mid = (p[0] - dy * bj, p[1] + dx * bj)
    perf = _perfil(0.4, 1.0, random.uniform(1.3, 1.9), random.choice([0.0, 0.3]), 0.0)
    return _traco_s([p0, mid, p3], w * random.uniform(0.45, 0.8), perf, rug)


def _labareda(main, H, w, rug):
    n = len(main)
    i = random.randint(int(n * 0.35), int(n * 0.9))
    p = main[i]
    tx, ty = _tangente(main, i)
    side = random.choice([-1, 1])
    nx, ny = -ty * side, tx * side
    L = H * random.uniform(0.12, 0.3)

    def q(a, b):
        return (p[0] + tx * L * a + nx * L * b, p[1] + ty * L * a + ny * L * b)

    ctrl = [q(0, 0), q(0.3, 0.05), q(0.65, 0.22), q(0.95, 0.5)]
    return _traco_s(ctrl, w * random.uniform(0.35, 0.6), _perfil(0.15, 1.0, random.uniform(1.4, 2.0), 0.6, 0.0), rug)


def _fagulha(main, tracos, pontos, H, esp, rug):
    n = len(main)
    for _ in range(8):
        i = random.randint(int(n * 0.2), int(n * 0.95))
        tx, ty = _tangente(main, i)
        side = random.choice([-1, 1])
        nx, ny = -ty * side, tx * side
        d, f = H * random.uniform(0.12, 0.3), H * random.uniform(-0.05, 0.2)
        c = (main[i][0] + nx * d + tx * f, main[i][1] + ny * d + ty * f)
        if _dist_min_all(tracos, c) < 16 + esp * 2:
            continue
        if random.random() < 0.4:
            pontos.append((c[0], c[1], esp * random.uniform(0.8, 1.5)))
        else:
            ang = math.atan2(ty, tx) + random.uniform(-0.7, 0.7)
            ln = H * random.uniform(0.04, 0.09)
            ux, uy = math.cos(ang), math.sin(ang)
            a = (c[0] - ux * ln / 2, c[1] - uy * ln / 2)
            b = (c[0] + ux * ln / 2, c[1] + uy * ln / 2)
            mid = (c[0] - uy * ln * 0.15 * side, c[1] + ux * ln * 0.15 * side)
            tracos.append(_traco_s([a, mid, b], esp * random.uniform(1.4, 2.2),
                                   _perfil(0.05, 1.0, 1.2, 0.9, 0.0), rug))
        return


# ---------- compilador da família ----------

def aplicar(draw, config, cx, cy, n, step, margem, cor, esp, estilo):
    ig = config.get("ignea", {})
    if not ig:
        return
    rug = ig.get("rugosidade", 0.5)
    H = min(cx, cy) * 1.45
    w = esp * 3.0

    # orientação: majoritariamente vertical, ponta para cima
    r = random.random()
    if r < 0.78:
        ang = math.radians(-90 + random.uniform(-22, 22))
    elif r < 0.90:
        ang = math.radians(90 + random.uniform(-22, 22))
    else:
        ang = math.radians(random.choice([0, 180]) + random.uniform(-15, 15))
    espelho = random.choice([-1, 1])
    dx, dy = math.cos(ang), math.sin(ang)
    px, py = -dy * espelho, dx * espelho

    def P(a, b):
        return (cx + dx * (a - 0.5) * H + px * b * H, cy + dy * (a - 0.5) * H + py * b * H)

    # arquétipo
    pesos = [(_arq_lamina, 1.0),
             (_arq_fenix, 2 * ig.get("fenix", 0)),
             (_arq_chama, 2 * ig.get("chama", 0)),
             (_arq_catalise, 2 * ig.get("catalise", 0)),
             (_arq_brasa, 2 * ig.get("brasa", 0)),
             (_arq_reignicao, 2 * ig.get("reignicao", 0))]
    x = random.random() * sum(p for _, p in pesos)
    escolhido = pesos[0][0]
    for fn, p in pesos:
        if x < p:
            escolhido = fn
            break
        x -= p
    tracos, pontos = escolhido(P, w, rug)
    main = tracos[0]["pts"]

    for _ in range(2):
        if random.random() < ig.get("cruzamentos", 0):
            tracos.append(_cruzar(main, H, w, rug))
    for _ in range(3):
        if random.random() < ig.get("labaredas", 0):
            tracos.append(_labareda(main, H, w, rug))
    for _ in range(4):
        if random.random() < ig.get("fagulhas", 0):
            _fagulha(main, tracos, pontos, H, esp, rug)

    # enquadramento: centraliza e reduz se passar do canvas
    xs, ys = [], []
    for t in tracos:
        m = t["w"] / 2
        xs += [p[0] - m for p in t["pts"]] + [p[0] + m for p in t["pts"]]
        ys += [p[1] - m for p in t["pts"]] + [p[1] + m for p in t["pts"]]
    for px_, py_, r_ in pontos:
        xs += [px_ - r_, px_ + r_]
        ys += [py_ - r_, py_ + r_]
    ox, oy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
    k = min(1.0, min(cx, cy) * 2 * 0.92 / max(max(xs) - min(xs), max(ys) - min(ys), 1.0))

    def T(p):
        return (cx + (p[0] - ox) * k, cy + (p[1] - oy) * k)

    for t in tracos:
        _desenhar(draw, [T(p) for p in t["pts"]], cor, t["w"] * k, t["perfil"], t["rug"])
    for px_, py_, r_ in pontos:
        _brasa(draw, T((px_, py_)), max(1.5, r_ * k), rug, cor)