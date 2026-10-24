import math
import random
from motor.utilitarios import suavizar_esqueleto

# ==========================================================
# FEITIÇARIA ÍGNEA — A Doutrina da Transformação
# Escrita de traços fortes e afilados (lâminas de pincel, ponta aguda),
# na linha da caligrafia oriental, mas com GRAMÁTICA:
#
#  1. VOCABULÁRIO DE TRAÇOS (heng, shu, pie, na, dian, ti, arco):
#     cada tipo tem perfil de pressão e curvatura próprios, como num
#     alfabeto de verdade.
#  2. COMPONENTES: grupos de traços ancorados numa grade (haste com
#     ramos, teto, cruz, cuia de chama, irradiação, haste partida...).
#  3. LAYOUTS: o glifo é um componente único, dois lado a lado, um sobre
#     o outro, ou um componente cercado por uma cuia de chama.
#  4. MODIFICADORES: labaredas, cruzamentos, fagulhas ancoradas nas
#     pontas e rugosidade (borda queimada).
#
# "estrutura" regula o equilíbrio: alto = traços firmes na grade
# (escrita); baixo = mais curva, desvio e riscos livres (cicatriz).
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


def _escolher(opcoes):
    """opcoes: lista de (item, peso)."""
    total = sum(p for _, p in opcoes)
    x = random.random() * total
    for item, p in opcoes:
        if x < p:
            return item
        x -= p
    return opcoes[-1][0]


# ---------- lâmina de pincel ----------

def _perfil(c=0.4, ea=1.0, eb=1.6, w0=0.0, w1=0.0):
    """Largura ao longo do traço: sobe até c (expoente ea) e afina até a ponta (expoente eb)."""
    def f(t):
        if t <= c:
            x = t / c if c > 0 else 1.0
            return w0 + (1 - w0) * (x ** ea)
        x = (1 - t) / (1 - c) if c < 1 else 0.0
        return w1 + (1 - w1) * (x ** eb)
    return f


def _traco_s(pts, w, perfil, rug, tipo="livre"):
    return {"pts": _reamostrar(suavizar_esqueleto(pts, iteracoes=3), 0.8),
            "w": w, "perfil": perfil, "rug": rug, "tipo": tipo}


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


# ---------- vocabulário de traços ----------
# Convenção: o traço começa em 'a' (lado grosso) e termina em 'b' (ponta).
# bulge: curvatura lateral relativa ao comprimento (sinal = lado).

TIPOS = {
    "heng": dict(c=0.15, ea=0.8, eb=1.5, w0=0.55, bulge=-0.05),   # horizontal: início chapado, ponta fina
    "shu":  dict(c=0.35, ea=1.0, eb=1.7, w0=0.50, bulge=0.04),    # haste: ponta aguda em b
    "pie":  dict(c=0.20, ea=0.9, eb=1.8, w0=0.70, bulge=0.10),    # desce à esquerda, varrida
    "na":   dict(c=0.70, ea=1.3, eb=0.9, w0=0.10, bulge=-0.09),   # desce à direita, pé pesado
    "dian": dict(c=0.25, ea=0.8, eb=1.3, w0=0.70, bulge=0.15),    # ponto-vírgula (brasa)
    "ti":   dict(c=0.20, ea=1.0, eb=1.5, w0=0.50, bulge=0.0),     # gancho/flick curto
    "arco": dict(c=0.50, ea=1.0, eb=1.5, w0=0.00, bulge=0.20),    # ponta aguda nas duas pontas
}


class _Fabrica:
    """Guarda o mapeamento da grade do glifo para a tela e acumula os traços."""

    def __init__(self, G, w, rug, estr):
        self.G, self.w, self.rug, self.estr = G, w, rug, estr
        self.jit = 0.012 + 0.07 * (1 - estr)
        self.curv = 0.6 + 1.6 * (1 - estr)
        self.tracos, self.pontos = [], []

    def c(self, cell, u, v):
        x0, y0, x1, y1 = cell
        return (x0 + u * (x1 - x0), y0 + v * (y1 - y0))

    def _j(self, p):
        j = self.jit
        return self.G(p[0] + random.uniform(-j, j), p[1] + random.uniform(-j, j))

    def t(self, tipo, a, b, wf=1.0):
        tp = TIPOS[tipo]
        pa, pb = self._j(a), self._j(b)
        L = max(math.hypot(pb[0] - pa[0], pb[1] - pa[1]), 1e-6)
        sinal = -1 if random.random() < (1 - self.estr) * 0.3 else 1
        bj = tp["bulge"] * self.curv * random.uniform(0.6, 1.3) * sinal
        px, py = -(pb[1] - pa[1]) / L, (pb[0] - pa[0]) / L
        mid = ((pa[0] + pb[0]) / 2 + px * bj * L, (pa[1] + pb[1]) / 2 + py * bj * L)
        perf = _perfil(tp["c"], tp["ea"], tp["eb"], tp["w0"], 0.0)
        tr = _traco_s([pa, mid, pb], self.w * wf, perf, self.rug, tipo)
        self.tracos.append(tr)
        return tr

    def curva(self, tipo, pts, wf=1.0):
        tp = TIPOS[tipo]
        perf = _perfil(tp["c"], tp["ea"], tp["eb"], tp["w0"], 0.0)
        tr = _traco_s([self._j(p) for p in pts], self.w * wf, perf, self.rug, tipo)
        self.tracos.append(tr)
        return tr

    def ponto(self, p, r):
        x, y = self.G(*p)
        self.pontos.append((x, y, max(1.5, r)))


# ---------- componentes (cada um ocupa uma célula da grade do glifo) ----------

def c_haste(F, cell, wf=1.0):
    lean = random.uniform(-0.08, 0.08)
    base = F.c(cell, 0.5, 1.0)
    F.t("shu", base, F.c(cell, 0.5 + lean, 0.0), wf * 1.1)
    if random.random() < 0.55:  # pé em gancho
        s = random.choice([-1, 1])
        F.t("ti", base, F.c(cell, 0.5 - 0.3 * s, 0.86), wf * 0.7)


def c_ramos(F, cell, wf=1.0):
    v = random.choice(["arvore", "garfo", "pente"])
    if v == "arvore":
        F.t("shu", F.c(cell, 0.5, 1.0), F.c(cell, 0.5, 0.0), wf * 1.1)
        h = random.uniform(0.28, 0.45)
        if random.random() < 0.75:
            F.t("heng", F.c(cell, 0.04, h + 0.04), F.c(cell, 0.96, h - 0.04), wf * 0.8)
        y0 = random.uniform(0.55, 0.7)
        if random.random() < 0.85:
            F.t("pie", F.c(cell, 0.48, y0), F.c(cell, 0.06, 1.0), wf * 0.8)
        if random.random() < 0.85:
            F.t("na", F.c(cell, 0.52, y0), F.c(cell, 0.94, 1.0), wf * 0.8)
    elif v == "garfo":
        topo_haste = random.uniform(0.38, 0.5)
        F.t("shu", F.c(cell, 0.5, 1.0), F.c(cell, 0.5, topo_haste), wf * 1.1)
        y = topo_haste + 0.05
        F.t("shu", F.c(cell, 0.5, y), F.c(cell, 0.1, 0.0), wf * 0.9)
        F.t("shu", F.c(cell, 0.5, y), F.c(cell, 0.9, 0.0), wf * 0.9)
        if random.random() < 0.55:
            F.t("shu", F.c(cell, 0.5, y), F.c(cell, 0.5, -0.02), wf * 0.85)
    else:
        s = random.choice([-1, 1])
        F.t("shu", F.c(cell, 0.5, 1.0), F.c(cell, 0.5, 0.0), wf)
        for y in (0.74, 0.52, 0.30)[:random.randint(2, 3)]:
            F.t("ti", F.c(cell, 0.5, y), F.c(cell, 0.5 + 0.4 * s, y - 0.2), wf * 0.65)


def c_teto(F, cell, wf=1.0):
    F.t("pie", F.c(cell, 0.54, 0.0), F.c(cell, 0.06, 0.98), wf)
    F.t("na", F.c(cell, 0.42, 0.14), F.c(cell, 0.96, 0.98), wf * 0.9)
    if random.random() < 0.4:
        F.ponto(F.c(cell, 0.5, -0.14), F.w * 0.3 * wf)


def c_cruz(F, cell, wf=1.0):
    F.t("pie", F.c(cell, 0.92, 0.0), F.c(cell, 0.08, 1.0), wf)
    F.t("na", F.c(cell, 0.08, 0.06), F.c(cell, 0.92, 0.94), wf * 0.9)
    if random.random() < 0.4:
        F.t("ti", F.c(cell, 0.5, 0.5), F.c(cell, 0.5 + random.choice([-0.3, 0.3]), 0.12), wf * 0.5)


def c_cuia(F, cell, wf=1.0, interior=True):
    ea, eb = random.uniform(0.04, 0.3), random.uniform(0.04, 0.3)
    fu = random.uniform(0.35, 0.65)
    F.curva("arco", [F.c(cell, 0.0, ea), F.c(cell, 0.05, 0.62), F.c(cell, fu, 1.0),
                     F.c(cell, 0.95, 0.62), F.c(cell, 1.0, eb)], wf * 1.05)
    if random.random() < 0.4:  # gancho na borda, voltado para dentro
        if random.random() < 0.5:
            F.t("ti", F.c(cell, 0.0, ea), F.c(cell, 0.2, ea - 0.12), wf * 0.6)
        else:
            F.t("ti", F.c(cell, 1.0, eb), F.c(cell, 0.8, eb - 0.12), wf * 0.6)
    if not interior:
        return
    v = _escolher([("linguas", 3.0), ("brasa", 1.0), ("vazia", 0.5)])
    if v == "linguas":
        nl = random.randint(1, 3)
        for k in range(nl):
            u = 0.5 + (k - (nl - 1) / 2) * 0.28
            F.t("shu", F.c(cell, u, 0.92), F.c(cell, u + random.uniform(-0.1, 0.1), random.uniform(0.2, 0.55)), wf * 0.85)
    elif v == "brasa":
        F.ponto(F.c(cell, 0.5, 0.55), F.w * 0.35 * wf)


def c_irradia(F, cell, wf=1.0):
    nodo = F.c(cell, 0.5, 0.55)
    x0, y0, x1, y1 = cell
    angs = random.sample([-90, -45, 0, 45, 90, 135, 180, 225], random.randint(3, 5))
    if -90 not in angs and random.random() < 0.7:
        angs[0] = -90
    for a in angs:
        r = random.uniform(0.3, 0.5)
        ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
        ini = (nodo[0] + 0.05 * ca * (x1 - x0), nodo[1] + 0.05 * sa * (y1 - y0))
        fim = (nodo[0] + r * ca * (x1 - x0), nodo[1] + r * sa * (y1 - y0))
        F.t("ti", ini, fim, wf * random.uniform(0.6, 0.95))
    F.ponto(nodo, F.w * 0.28 * wf)


def c_partido(F, cell, wf=1.0):
    xs = 0.5 + random.uniform(-0.05, 0.05)
    corte = random.uniform(0.5, 0.62)
    F.t("shu", F.c(cell, xs, 1.0), F.c(cell, xs, corte), wf * 1.05)
    F.ponto(F.c(cell, xs, corte - 0.1), F.w * 0.3 * wf)
    F.t("shu", F.c(cell, xs, corte - 0.2), F.c(cell, xs + random.uniform(-0.05, 0.05), 0.0), wf * 0.9)


def c_onda(F, cell, wf=1.0):
    F.curva("arco", [F.c(cell, 0.38, 1.0), F.c(cell, 0.7, 0.68), F.c(cell, 0.32, 0.36), F.c(cell, 0.62, 0.0)], wf)
    if random.random() < 0.4:
        F.t("dian", F.c(cell, 0.3, 0.2), F.c(cell, 0.22, 0.28), wf * 0.6)


# ---------- layouts ----------

def _compor(F, ig):
    cruz = ig.get("cruzamentos", 0)
    chama = ig.get("chama", 0)
    cat = ig.get("catalise", 0)
    reig = ig.get("reignicao", 0)
    comp = ig.get("complexidade", 0.5)

    grandes = [(c_ramos, 1.0), (c_cruz, 0.3 + 2 * cruz), (c_cuia, 0.1 + 1.2 * chama),
               (c_irradia, 0.2 + 2 * cat), (c_partido, 0.2 + 2 * reig), (c_onda, 0.8), (c_haste, 0.6)]
    estreitos = [(c_haste, 1.0), (c_onda, 0.8), (c_partido, 0.2 + 2 * reig), (c_ramos, 0.6)]
    de_topo = [(c_teto, 1.0), (c_cruz, 0.3 + 2 * cruz), (c_irradia, 0.2 + 2 * cat)]
    de_base = [(c_haste, 1.0), (c_ramos, 1.0), (c_cuia, 0.1 + 1.2 * chama), (c_partido, 0.2 + 2 * reig), (c_onda, 0.8)]
    pequenos = [(c_haste, 1.0), (c_cruz, 0.5), (c_irradia, 0.4)]

    p_cerc, p_dup, p_topo = comp * 0.22, comp * 0.5, comp * 0.4
    x = random.random()
    if x < p_cerc:
        c_cuia(F, (0.0, 0.14, 1.0, 1.0), 0.95, interior=False)
        _escolher(pequenos)(F, (0.3, 0.12, 0.7, 0.66), 0.55)
    elif x < p_cerc + p_dup:
        esq, dir_ = (0.0, 0.0, 0.36, 1.0), (0.46, 0.0, 1.0, 1.0)
        if random.random() < 0.5:
            esq, dir_ = (0.64, 0.0, 1.0, 1.0), (0.0, 0.0, 0.54, 1.0)
        _escolher(estreitos)(F, esq, 0.8)
        _escolher(grandes)(F, dir_, 0.85)
    elif x < p_cerc + p_dup + p_topo:
        _escolher(de_topo)(F, (0.08, 0.0, 0.92, 0.42), 0.75)
        _escolher(de_base)(F, (0.0, 0.5, 1.0, 1.0), 0.85)
    else:
        _escolher(grandes)(F, (0.0, 0.0, 1.0, 1.0), 1.0)


# ---------- modificadores ----------

def _cruzar(main, H, w, rug):
    n = len(main)
    i = random.randint(int(n * 0.25), int(n * 0.7))
    p = main[i]
    tx, ty = _tangente(main, i)
    ang = random.choice([-1, 1]) * math.radians(random.uniform(35, 75))
    c, s = math.cos(ang), math.sin(ang)
    dx, dy = tx * c - ty * s, tx * s + ty * c
    comp = H * random.uniform(0.18, 0.4)
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
    L = H * random.uniform(0.12, 0.28)

    def q(a, b):
        return (p[0] + tx * L * a + nx * L * b, p[1] + ty * L * a + ny * L * b)

    return _traco_s([q(0, 0), q(0.3, 0.05), q(0.65, 0.22), q(0.95, 0.5)],
                    w * random.uniform(0.35, 0.6),
                    _perfil(0.15, 1.0, random.uniform(1.4, 2.0), 0.6, 0.0), rug)


def _fagulha(F, H, esp):
    """Brasa lançada da ponta de um traço, seguindo a direção dele."""
    cand = [t for t in F.tracos if t["tipo"] in ("shu", "pie", "na", "ti", "arco") and len(t["pts"]) > 10]
    if not cand:
        return
    for _ in range(8):
        t = random.choice(cand)
        pts = t["pts"]
        tx, ty = _tangente(pts, len(pts) - 1, 6)
        nx, ny = -ty, tx
        d, lado = H * random.uniform(0.05, 0.12), H * random.uniform(-0.05, 0.05)
        c = (pts[-1][0] + tx * d + nx * lado, pts[-1][1] + ty * d + ny * lado)
        if _dist_min_all(F.tracos, c) < 10 + esp * 1.5:
            continue
        if random.random() < 0.45:
            F.pontos.append((c[0], c[1], max(1.5, esp * random.uniform(0.7, 1.2))))
        else:
            ang = math.atan2(ty, tx) + random.uniform(-0.5, 0.5)
            ln = H * random.uniform(0.035, 0.07)
            ux, uy = math.cos(ang), math.sin(ang)
            a = (c[0] - ux * ln / 2, c[1] - uy * ln / 2)
            b = (c[0] + ux * ln / 2, c[1] + uy * ln / 2)
            mid = (c[0] - uy * ln * 0.15, c[1] + ux * ln * 0.15)
            F.tracos.append(_traco_s([a, mid, b], esp * random.uniform(1.3, 2.0),
                                     _perfil(0.05, 1.0, 1.2, 0.9, 0.0), F.rug, "dian"))
        return


# ---------- compilador da família ----------

def aplicar(draw, config, cx, cy, n, step, margem, cor, esp, estilo):
    ig = config.get("ignea", {})
    if not ig:
        return

    estr = ig.get("estrutura", 0.6)
    rug = ig.get("rugosidade", 0.5)
    S = min(cx, cy) * 1.45
    Bw, Bh = S * 0.78, S
    slant = random.uniform(-0.12, 0.12)
    espelho = random.random() < 0.5

    def G(x, y):
        if espelho:
            x = 1 - x
        return (cx + (x - 0.5) * Bw + (0.5 - y) * Bh * slant, cy + (y - 0.5) * Bh)

    F = _Fabrica(G, esp * 3.8, rug, estr)
    _compor(F, ig)
    if not F.tracos:
        return

    espessos = [t for t in F.tracos if t["tipo"] in ("shu", "pie", "na", "arco")] or F.tracos

    p_cruz = ig.get("cruzamentos", 0) * 0.5 + (1 - estr) * 0.4
    if random.random() < p_cruz:
        F.tracos.append(_cruzar(random.choice(espessos)["pts"], Bh, F.w, rug))
    for _ in range(3):
        if random.random() < ig.get("labaredas", 0):
            F.tracos.append(_labareda(random.choice(espessos)["pts"], Bh, F.w, rug))
    for _ in range(3):
        if random.random() < ig.get("fagulhas", 0):
            _fagulha(F, Bh, esp)

    tracos, pontos = F.tracos, F.pontos

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