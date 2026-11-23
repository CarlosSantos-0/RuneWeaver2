import math
import random
from motor.utilitarios import suavizar_esqueleto

# ==========================================================
# FEITIÇARIA ÍGNEA — A Doutrina da Transformação
# Escrita de traços fortes e afilados (lâminas de pincel, ponta aguda),
# na linha da caligrafia oriental / escritas femininas chinesas (Nüshu),
# mas com GRAMÁTICA:
#
#  1. VOCABULÁRIO DE TRAÇOS (heng, shu, pie, na, dian, ti, arco, lamina, gota):
#     cada tipo tem perfil de pressão e curvatura próprios.
#  2. ESPINHAS: o traço principal do glifo. Varredura diagonal, onda em S,
#     haste com pé em gancho, cuia assimétrica ou haste que termina em laço.
#     Podem terminar em ESPIRAL e podem ser partidas por uma brasa.
#  3. SATÉLITES: traços e pontos ancorados na espinha (ramos, lâminas que
#     cruzam, colunas de pontos, vírgulas, forquilhas, ganchos de ponta,
#     irradiação). Nunca se repete o mesmo tipo de satélite no glifo.
#  4. LAYOUTS: espinha única + satélites, duas espinhas DIFERENTES lado a lado,
#     componente de topo sobre espinha, ou cuia cercando um núcleo.
#  5. FILTRO ANTI-REPETIÇÃO: cada glifo é avaliado (variedade de direções,
#     verticalidade, proporção, número de elementos). Os que parecem
#     "palito" ou "arco solitário" são descartados e refeitos, com a mesma
#     seed, então o resultado continua determinístico.
#  6. MODIFICADORES: labaredas, cruzamentos, fagulhas e rugosidade.
#
# "estrutura" regula o equilíbrio: alto = traços firmes (escrita);
# baixo = mais curva, desvio e inclinação (cicatriz).
# "complexidade" regula quantos elementos o glifo pode ter.
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


def _traco_s(pts, w, perfil, rug, tipo="livre", it=3):
    return {"pts": _reamostrar(suavizar_esqueleto(pts, iteracoes=it), 0.8),
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
    "heng":   dict(c=0.15, ea=0.8, eb=1.5, w0=0.55, bulge=-0.05),  # horizontal: início chapado, ponta fina
    "shu":    dict(c=0.35, ea=1.0, eb=1.7, w0=0.50, bulge=0.04),   # haste: ponta aguda em b
    "pie":    dict(c=0.20, ea=0.9, eb=1.8, w0=0.70, bulge=0.10),   # desce à esquerda, varrida
    "na":     dict(c=0.70, ea=1.3, eb=0.9, w0=0.10, bulge=-0.09),  # desce à direita, pé pesado
    "dian":   dict(c=0.25, ea=0.8, eb=1.3, w0=0.70, bulge=0.15),   # ponto-vírgula (brasa)
    "ti":     dict(c=0.20, ea=1.0, eb=1.5, w0=0.50, bulge=0.0),    # gancho/flick curto
    "arco":   dict(c=0.50, ea=1.0, eb=1.5, w0=0.00, bulge=0.20),   # ponta aguda nas duas pontas
    "lamina": dict(c=0.48, ea=1.0, eb=1.5, w0=0.00, bulge=0.06),   # barriga no meio, duas pontas agudas
    "gota":   dict(c=0.30, ea=0.7, eb=1.2, w0=0.60, bulge=0.14),   # vírgula grossa
}


class _Fabrica:
    """Guarda o mapeamento da grade do glifo para a tela e acumula os traços."""

    def __init__(self, G, w, rug, estr, H, asp):
        self.G, self.w, self.rug, self.estr = G, w, rug, estr
        self.H, self.asp = H, asp          # altura da caixa do glifo (px) e razão largura/altura
        self.jit = 0.012 + 0.07 * (1 - estr)
        self.curv = 0.6 + 1.6 * (1 - estr)
        self.tilt = math.radians(6 + 24 * (1 - estr))
        self.rot = 0.0                     # rotação (rad) aplicada às coordenadas de célula
        self.tracos, self.pontos = [], []

    def c(self, cell, u, v):
        if self.rot:
            du, dv = u - 0.5, v - 0.5
            cs, sn = math.cos(self.rot), math.sin(self.rot)
            u, v = 0.5 + du * cs - dv * sn, 0.5 + du * sn + dv * cs
        x0, y0, x1, y1 = cell
        return (x0 + u * (x1 - x0), y0 + v * (y1 - y0))

    def ju(self, p, k=1.0):
        """Ponto da grade com tremor, ainda em coordenadas do glifo."""
        j = self.jit * k
        return (p[0] + random.uniform(-j, j), p[1] + random.uniform(-j, j))

    def _j(self, p):
        return self.G(*self.ju(p))

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

    def curva_s(self, tipo, pts_tela, wf=1.0, perf=None):
        """Curva a partir de pontos já em coordenadas de tela (sem tremor extra)."""
        if perf is None:
            tp = TIPOS[tipo]
            perf = _perfil(tp["c"], tp["ea"], tp["eb"], tp["w0"], 0.0)
        tr = _traco_s(pts_tela, self.w * wf, perf, self.rug, tipo)
        self.tracos.append(tr)
        return tr

    def sx(self, tipo, pts_tela, wf=1.0):
        """Traço em coordenadas de tela, com o perfil do tipo."""
        return self.curva_s(tipo, pts_tela, wf)

    def ponto(self, p, r):
        x, y = self.G(*p)
        self.pontos.append((x, y, max(1.5, r)))

    def ponto_s(self, x, y, r):
        self.pontos.append((x, y, max(1.5, r)))


# ---------- geometria auxiliar ----------

def _espiral_u(F, E, T, lado, R, voltas, passos=10):
    """Continuação em espiral (raio decrescente) a partir de E, saindo na direção T.
    Tudo em coordenadas do glifo; a conta é feita num espaço isotrópico."""
    asp = F.asp
    tx, ty = T[0] * asp, T[1]
    d = math.hypot(tx, ty) or 1.0
    tx, ty = tx / d, ty / d
    nx, ny = -ty * lado, tx * lado
    cx_, cy_ = E[0] * asp + nx * R, E[1] + ny * R
    phi0 = math.atan2(-ny, -nx)
    total = voltas * math.tau
    n = max(6, int(passos * voltas))
    out = []
    for k in range(1, n + 1):
        th = total * k / n
        r = R * (1 - 0.62 * k / n)
        a = phi0 + lado * th
        out.append(((cx_ + r * math.cos(a)) / asp, cy_ + r * math.sin(a)))
    return out


def _ancora(pts, t):
    i = max(0, min(len(pts) - 1, int(t * (len(pts) - 1))))
    return pts[i], _tangente(pts, i, 6)


def _ponta(pts, fim):
    """Ponto da extremidade e direção apontando para fora do traço."""
    if fim:
        return pts[-1], _tangente(pts, len(pts) - 1, 6)
    tx, ty = _tangente(pts, 0, 6)
    return pts[0], (-tx, -ty)


def _livre(F, c, r):
    return _dist_min_all(F.tracos, c) > F.w * 0.7 + r


# ---------- espinhas (traço principal) ----------
# Cada gerador devolve (pontos locais [0..1], tipo de perfil, fator de largura).

def _sp_varredura():
    u0 = random.uniform(0.6, 0.95)
    u1 = random.uniform(0.02, 0.4)
    o1, o2 = random.uniform(-0.22, 0.22), random.uniform(-0.22, 0.22)
    v0, v1 = random.uniform(0.0, 0.08), random.uniform(0.92, 1.0)
    pts = [(u0, v0),
           (u0 + (u1 - u0) * 0.33 + o1, 0.36),
           (u0 + (u1 - u0) * 0.66 + o2, 0.68),
           (u1, v1)]
    return pts, "lamina", 1.9


def _sp_onda():
    a = random.uniform(0.14, 0.3)
    lean = random.uniform(-0.12, 0.12)
    s = random.choice([-1, 1])
    nb = random.choice([4, 5])
    vs = [i / (nb - 1) for i in range(nb)]
    pts = []
    for i, v in enumerate(vs):
        if i in (0, nb - 1):
            u = 0.5 + lean * (1 if i == 0 else -1)
        else:
            u = 0.5 + s * a * ((-1) ** (i - 1)) * (1 - 0.25 * i / nb)
        pts.append((u, v + random.uniform(-0.03, 0.03) * (0 < i < nb - 1)))
    return pts, "lamina", 1.6


def _sp_gancho():
    lean = random.uniform(-0.15, 0.2)
    s = random.choice([-1, 1])
    pts = [(0.55 + lean, 0.0), (0.52 + lean * 0.6, 0.3), (0.5, 0.62), (0.46 - lean * 0.5, 0.86),
           (0.46 - s * 0.12, 0.98), (0.46 - s * 0.28, 0.9)]
    return pts, "shu", 1.7


def _sp_cuia():
    ea, eb = random.uniform(0.02, 0.4), random.uniform(0.02, 0.4)
    if abs(ea - eb) < 0.12:
        eb = min(0.45, ea + 0.15)
    fu = random.uniform(0.25, 0.75)
    base = [(0.0, ea), (0.04, 0.62), (fu, 1.0), (0.96, 0.62), (1.0, eb)]
    sy = random.uniform(0.6, 1.0)
    ang = math.radians(random.uniform(-38, 38))
    cs, sn = math.cos(ang), math.sin(ang)
    pts = []
    for u, v in base:
        v = 0.5 + (v - 0.5) * sy
        du, dv = u - 0.5, v - 0.5
        pts.append((0.5 + du * cs - dv * sn, 0.5 + du * sn + dv * cs))
    return pts, "arco", 1.5


def _sp_laco():
    lean = random.uniform(-0.1, 0.1)
    pts = [(0.62 + lean, 0.0), (0.56 + lean, 0.3), (0.42, 0.62), (0.34, 0.78)]
    return pts, "lamina", 1.7


_ESPINHAS = {"varredura": _sp_varredura, "onda": _sp_onda, "gancho": _sp_gancho,
             "cuia": _sp_cuia, "laco": _sp_laco}


def _partir(F, tr):
    """Parte o traço em dois, com uma brasa no intervalo."""
    pts = tr["pts"]
    n = len(pts)
    a, b = int(n * random.uniform(0.38, 0.46)), int(n * random.uniform(0.54, 0.62))
    if a < 8 or n - b < 8:
        return tr
    F.tracos.remove(tr)
    perf = _perfil(0.5, 1.0, 1.4, 0.0, 0.0)
    t1 = _traco_s(pts[:a + 1], tr["w"], perf, tr["rug"], "lamina", it=0)
    t2 = _traco_s(pts[b:], tr["w"], perf, tr["rug"], "lamina", it=0)
    F.tracos += [t1, t2]
    mid = pts[(a + b) // 2]
    F.ponto_s(mid[0], mid[1], F.w * random.uniform(0.24, 0.34))
    return t1 if a >= n - b else t2


def espinha(F, cell, tipo, wf0=1.0, ig=None, curl=None):
    pts_l, perf_t, wf = _ESPINHAS[tipo]()
    pts = [F.c(cell, u, v) for u, v in pts_l]
    if random.random() < 0.5:
        pts.reverse()
    pj = [F.ju(p) for p in pts]
    if curl is None:
        curl = tipo == "laco" or (tipo != "cuia" and random.random() < 0.42)
    perf = None
    if curl:
        E, P = pj[-1], pj[-2]
        lado = random.choice([-1, 1])
        R = random.uniform(0.05, 0.09)
        voltas = random.choice([0.9, 1.2, 1.5])
        if tipo == "laco":
            voltas = random.choice([1.3, 1.6, 1.9])
        pj = pj + _espiral_u(F, E, (E[0] - P[0], E[1] - P[1]), lado, R, voltas)
        perf = _perfil(0.42, 1.0, 1.2, TIPOS[perf_t]["w0"], 0.0)
    tr = F.curva_s(perf_t, [F.G(*p) for p in pj], wf * wf0, perf)
    reig = (ig or {}).get("reignicao", 0)
    if not curl and tipo != "cuia" and random.random() < 0.08 + 0.5 * reig:
        tr = _partir(F, tr)
    return tr


# ---------- componentes antigos reaproveitados como elementos ----------

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
    # X assimétrico: um braço longo e outro curto, cruzando fora do centro
    u0, u1 = random.uniform(0.7, 0.95), random.uniform(0.02, 0.25)
    F.t("pie", F.c(cell, u0, 0.0), F.c(cell, u1, 1.0), wf)
    cy_ = random.uniform(0.3, 0.6)
    F.t("na", F.c(cell, random.uniform(0.0, 0.2), cy_ - random.uniform(0.2, 0.3)),
        F.c(cell, random.uniform(0.8, 1.0), cy_ + random.uniform(0.3, 0.42)), wf * 0.9)
    if random.random() < 0.4:
        F.t("ti", F.c(cell, 0.5, 0.5), F.c(cell, 0.5 + random.choice([-0.3, 0.3]), 0.12), wf * 0.5)


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


_OUTROS = {"cruz": c_cruz, "ramos": c_ramos, "irradia": c_irradia, "teto": c_teto}


def _elemento(F, cell, tipo, ig, wf0=1.0):
    """Cria um elemento (espinha ou componente) numa célula, levemente inclinado.
    Devolve o traço mais longo criado, para ancorar satélites."""
    F.rot = random.uniform(-1, 1) * F.tilt
    try:
        if tipo in _ESPINHAS:
            return espinha(F, cell, tipo, wf0, ig)
        n0 = len(F.tracos)
        _OUTROS[tipo](F, cell, wf0)
        novos = F.tracos[n0:]
        return max(novos, key=lambda t: len(t["pts"])) if novos else None
    finally:
        F.rot = 0.0


# ---------- satélites (ancorados num traço) ----------

def s_ramo(F, sp, H):
    p, (tx, ty) = _ancora(sp["pts"], random.uniform(0.2, 0.8))
    ang = random.choice([-1, 1]) * math.radians(random.uniform(28, 75))
    c, s = math.cos(ang), math.sin(ang)
    dx, dy = tx * c - ty * s, tx * s + ty * c
    L = H * random.uniform(0.16, 0.38)
    bj = random.choice([-1, 1]) * L * random.uniform(0.05, 0.2)
    mid = (p[0] + dx * L * 0.5 - dy * bj, p[1] + dy * L * 0.5 + dx * bj)
    F.sx(random.choice(["pie", "shu", "ti"]), [p, mid, (p[0] + dx * L, p[1] + dy * L)],
         random.uniform(0.7, 1.1))


def s_cruza(F, sp, H):
    p, (tx, ty) = _ancora(sp["pts"], random.uniform(0.3, 0.7))
    ang = random.choice([-1, 1]) * math.radians(random.uniform(35, 80))
    c, s = math.cos(ang), math.sin(ang)
    dx, dy = tx * c - ty * s, tx * s + ty * c
    L = H * random.uniform(0.28, 0.6)
    atras = random.uniform(0.25, 0.45)
    bj = random.choice([-1, 1]) * L * random.uniform(0.04, 0.16)
    p0 = (p[0] - dx * L * atras, p[1] - dy * L * atras)
    p3 = (p[0] + dx * L * (1 - atras), p[1] + dy * L * (1 - atras))
    mid = ((p0[0] + p3[0]) / 2 - dy * bj, (p0[1] + p3[1]) / 2 + dx * bj)
    F.sx(random.choice(["lamina", "lamina", "pie"]), [p0, mid, p3], random.uniform(0.8, 1.3))


def s_pontos(F, sp, H):
    for _ in range(6):
        p, (tx, ty) = _ancora(sp["pts"], random.uniform(0.1, 0.9))
        lado = random.choice([-1, 1])
        nx, ny = -ty * lado, tx * lado
        d = H * random.uniform(0.12, 0.26)
        base = (p[0] + nx * d, p[1] + ny * d)
        n = random.choice([2, 2, 3, 3, 4])
        e = H * random.uniform(0.06, 0.11)
        curv = random.uniform(-0.25, 0.25)
        r0 = F.w * random.uniform(0.28, 0.42)
        novos, ok = [], True
        for k in range(n):
            o = k - (n - 1) / 2
            c = (base[0] + tx * e * o + nx * curv * e * o * o * 0.5,
                 base[1] + ty * e * o + ny * curv * e * o * o * 0.5)
            r = r0 * (1 - 0.18 * abs(o)) * random.uniform(0.85, 1.1)
            if not _livre(F, c, r):
                ok = False
                break
            novos.append((c[0], c[1], r))
        if ok:
            for c in novos:
                F.ponto_s(*c)
            return


def s_virgula(F, sp, H):
    for _ in range(8):
        p, (tx, ty) = _ancora(sp["pts"], random.uniform(0.0, 1.0))
        lado = random.choice([-1, 1])
        nx, ny = -ty * lado, tx * lado
        d = H * random.uniform(0.16, 0.3)
        c = (p[0] + nx * d, p[1] + ny * d)
        a = math.atan2(ty, tx) + random.uniform(-0.9, 0.9)
        L = H * random.uniform(0.1, 0.2)
        ux, uy = math.cos(a), math.sin(a)
        if not _livre(F, c, L * 0.5):
            continue
        bj = L * random.uniform(0.1, 0.25) * random.choice([-1, 1])
        pa = (c[0] - ux * L / 2, c[1] - uy * L / 2)
        pb = (c[0] + ux * L / 2, c[1] + uy * L / 2)
        mid = (c[0] - uy * bj, c[1] + ux * bj)
        F.sx("gota", [pa, mid, pb], random.uniform(1.1, 1.6))
        return


def s_forquilha(F, sp, H):
    p, (tx, ty) = _ponta(sp["pts"], random.random() < 0.5)
    p = (p[0] - tx * H * 0.03, p[1] - ty * H * 0.03)
    base = math.atan2(ty, tx)
    for sgn in (-1, 1):
        a = base + sgn * math.radians(random.uniform(20, 55))
        L = H * random.uniform(0.1, 0.26)
        bj = L * random.uniform(-0.12, 0.12)
        ux, uy = math.cos(a), math.sin(a)
        mid = (p[0] + ux * L * 0.5 - uy * bj, p[1] + uy * L * 0.5 + ux * bj)
        F.sx("ti", [p, mid, (p[0] + ux * L, p[1] + uy * L)], random.uniform(0.55, 0.9))


def s_ponta(F, sp, H):
    """Gancho curto na extremidade, como o flick final de um traço de pincel."""
    fim = random.random() < 0.5
    pts = sp["pts"]
    i = int(len(pts) * (0.9 if fim else 0.1))
    i = max(0, min(len(pts) - 1, i))
    p = pts[i]
    tx, ty = _tangente(pts, i, 6)
    if not fim:
        tx, ty = -tx, -ty
    a = math.atan2(ty, tx) + random.choice([-1, 1]) * math.radians(random.uniform(30, 70))
    L = H * random.uniform(0.09, 0.2)
    ux, uy = math.cos(a), math.sin(a)
    bj = L * random.uniform(-0.15, 0.15)
    mid = (p[0] + ux * L * 0.5 - uy * bj, p[1] + uy * L * 0.5 + ux * bj)
    F.sx("ti", [p, mid, (p[0] + ux * L, p[1] + uy * L)], random.uniform(0.55, 0.8))


def s_radial(F, sp, H):
    """Pequena irradiação (faíscas) na ponta do traço."""
    p, (tx, ty) = _ponta(sp["pts"], random.random() < 0.5)
    nodo = (p[0] + tx * H * 0.07, p[1] + ty * H * 0.07)
    base = math.atan2(ty, tx)
    nr = random.randint(3, 4)
    for k in range(nr):
        a = base + (k - (nr - 1) / 2) * math.radians(random.uniform(38, 55))
        L = H * random.uniform(0.08, 0.16)
        ux, uy = math.cos(a), math.sin(a)
        ini = (nodo[0] + ux * H * 0.02, nodo[1] + uy * H * 0.02)
        F.sx("ti", [ini, (ini[0] + ux * L * 0.5, ini[1] + uy * L * 0.5),
                    (ini[0] + ux * L, ini[1] + uy * L)], random.uniform(0.45, 0.7))
    F.ponto_s(nodo[0], nodo[1], F.w * 0.26)


def s_linguas(F, sp, H):
    """Línguas de chama dentro de uma cuia."""
    base = max(sp["pts"], key=lambda q: q[1])
    nl = random.randint(1, 3)
    for k in range(nl):
        u = (k - (nl - 1) / 2) * H * 0.12
        a = (base[0] + u, base[1] - H * 0.1)
        b = (a[0] + random.uniform(-0.05, 0.05) * H, a[1] - H * random.uniform(0.18, 0.34))
        m = ((a[0] + b[0]) / 2 + random.uniform(-0.03, 0.03) * H, (a[1] + b[1]) / 2)
        F.sx("shu", [a, m, b], 0.85)


def _satelites(F, sp, H, n, ig):
    if sp is None or n <= 0:
        return
    cruz = ig.get("cruzamentos", 0)
    cat = ig.get("catalise", 0)
    opcoes = [(s_ramo, 2.0), (s_cruza, 1.2 + 2 * cruz), (s_pontos, 1.8), (s_virgula, 1.0),
              (s_forquilha, 1.1), (s_ponta, 1.2), (s_radial, 0.1 + 1.6 * cat)]
    for _ in range(n):
        f = _escolher(opcoes)
        opcoes = [(g, p) for g, p in opcoes if g is not f]
        f(F, sp, H)


# ---------- layouts ----------

def _pesos_espinha(ig, estreita=False):
    chama = ig.get("chama", 0)
    cruz = ig.get("cruzamentos", 0)
    cat = ig.get("catalise", 0)
    base = [("varredura", 3.0), ("onda", 2.0), ("gancho", 2.0), ("laco", 1.3)]
    if not estreita:
        base += [("cuia", 0.05 + 0.8 * chama), ("cruz", 0.3 + 2 * cruz),
                 ("ramos", 0.7), ("irradia", 0.1 + 1.5 * cat)]
    return base


def _compor(F, ig):
    comp = ig.get("complexidade", 0.5)
    chama = ig.get("chama", 0)
    completo = (0.0, 0.0, 1.0, 1.0)

    p_cerc = 0.03 + comp * 0.06
    p_dup = 0.12 + comp * 0.30
    p_topo = 0.05 + comp * 0.12
    x = random.random()

    if x < p_cerc:
        sp = _elemento(F, (0.0, 0.16, 1.0, 1.0), "cuia", ig, 0.95)
        interno = _escolher([("gancho", 1.0), ("varredura", 1.0), ("onda", 0.8), ("cruz", 0.6)])
        _elemento(F, (0.3, 0.2, 0.7, 0.78), interno, ig, 0.55)
    elif x < p_cerc + p_dup:
        cels = [(0.0, 0.0, 0.4, 1.0), (0.46, 0.0, 1.0, 1.0)]
        if random.random() < 0.5:
            cels = [(0.6, 0.0, 1.0, 1.0), (0.0, 0.0, 0.54, 1.0)]
        pesos = _pesos_espinha(ig, estreita=True)
        a = _escolher(pesos)
        b = _escolher([(t, p) for t, p in pesos if t != a])
        sp_a = _elemento(F, cels[0], a, ig, 0.8)
        sp_b = _elemento(F, cels[1], b, ig, 0.95)
        _satelites(F, sp_b, F.H, int(random.random() < 0.55 + 0.3 * comp), ig)
        _satelites(F, sp_a, F.H * 0.6, int(random.random() < 0.3 + 0.3 * comp), ig)
    elif x < p_cerc + p_dup + p_topo:
        topo = _escolher([("teto", 1.0), ("cruz", 0.3 + 2 * ig.get("cruzamentos", 0)),
                          ("irradia", 0.2 + 2 * ig.get("catalise", 0))])
        _elemento(F, (0.08, 0.0, 0.92, 0.42), topo, ig, 0.75)
        pesos = [(t, p) for t, p in _pesos_espinha(ig) if t not in ("cruz", "irradia", "teto")]
        base_t = _escolher(pesos)
        sp = _elemento(F, (0.0, 0.5, 1.0, 1.0), base_t, ig, 0.85)
        _satelites(F, sp, F.H * 0.5, int(random.random() < 0.5), ig)
    else:
        tipo = _escolher(_pesos_espinha(ig))
        sp = _elemento(F, completo, tipo, ig, 1.0)
        n = 1 + int(random.random() < 0.35 + 0.5 * comp) + int(random.random() < 0.10 + 0.45 * comp)
        if tipo in _OUTROS:       # esses já são compostos: menos satélites
            n = int(random.random() < 0.5)
        if tipo == "cuia" and random.random() < chama:
            s_linguas(F, sp, F.H)
        _satelites(F, sp, F.H, n, ig)


# ---------- filtro anti-repetição ----------

def _penalidade(F, comp):
    """0 = glifo aceito. Quanto maior, mais parecido com 'palito' / 'arco solitário'."""
    if not F.tracos:
        return 99.0
    bins = [0.0] * 8
    tot = vert = 0.0
    xs, ys = [], []
    for t in F.tracos:
        pts = t["pts"][::4] + [t["pts"][-1]]
        xs += [p[0] for p in pts]
        ys += [p[1] for p in pts]
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            dx, dy = x1 - x0, y1 - y0
            d = math.hypot(dx, dy)
            if d < 1e-6:
                continue
            a = math.atan2(dy, dx) % math.pi
            bins[min(7, int(a / (math.pi / 8)))] += d
            tot += d
            if abs(dx) < 0.26 * d:
                vert += d
    for (x, y, r) in F.pontos:
        xs.append(x)
        ys.append(y)
    if tot <= 0:
        return 99.0
    ent = -sum((b / tot) * math.log2(b / tot) for b in bins if b > 0)
    w, h = max(xs) - min(xs), max(ys) - min(ys)
    asp = w / max(h, 1.0)
    n_el = len(F.tracos) + 0.34 * len(F.pontos)
    pen = 0.0
    pen += max(0.0, 1.55 - ent) * 2
    pen += max(0.0, vert / tot - 0.5) * 4
    pen += max(0.0, 0.42 - asp) * 4 + max(0.0, asp - 1.7) * 4
    pen += max(0.0, 3.0 - n_el) + max(0.0, n_el - (5.5 + 4 * comp))
    return pen


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
    cand = [t for t in F.tracos
            if t["tipo"] in ("shu", "pie", "na", "ti", "arco", "lamina") and len(t["pts"]) > 10]
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
    comp = ig.get("complexidade", 0.5)
    S = min(cx, cy) * 1.45
    Bw, Bh = S * random.uniform(0.62, 0.92), S
    slant = random.uniform(-0.22, 0.22)
    espelho = random.random() < 0.5

    def G(x, y):
        if espelho:
            x = 1 - x
        return (cx + (x - 0.5) * Bw + (0.5 - y) * Bh * slant, cy + (y - 0.5) * Bh)

    # gera candidatos até um passar no filtro anti-repetição (determinístico por seed)
    melhor = None
    for _ in range(16):
        cand = _Fabrica(G, esp * 3.8, rug, estr, Bh, Bw / Bh)
        _compor(cand, ig)
        pen = _penalidade(cand, comp)
        if melhor is None or pen < melhor[0]:
            melhor = (pen, cand)
        if pen == 0.0:
            break
    F = melhor[1]
    if not F.tracos:
        return

    espessos = [t for t in F.tracos if t["tipo"] in ("shu", "pie", "na", "arco", "lamina")] or F.tracos

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