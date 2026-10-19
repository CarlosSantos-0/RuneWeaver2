import math
import random
from motor.utilitarios import suavizar_esqueleto

# ==========================================================
# FEITIÇARIA MARINHA — Fluade-Mare
# Um único traço-espinha (horizontal ou vertical) que flui como
# caligrafia cursiva contínua (Técnica do Rio). Sobre essa espinha
# nascem as formas que dão identidade a cada runa:
#   volutas nas pontas, laços, bojos fechados, ramos que se soltam
#   como esteira de pincel e marcas soltas ao redor (estilo Badlit).
# A pena larga dá contraste grosso/fino conforme a direção do traço.
# A Contra-Corrente (ruptura) é um gancho pesado cortado de repente.
# Tudo na cor principal da runa.
# ==========================================================

ANGULO_PENA = math.radians(38)

# Esqueletos normalizados (u: eixo principal, v: lateral), ambos em [-1, 1]
MOLDES = {
    "S":      [(-1, -0.2), (-0.6, -0.85), (-0.1, -0.5), (0.1, 0.5), (0.6, 0.85), (1, 0.2)],
    "N":      [(-1, 0.7), (-0.35, -0.7), (0.35, 0.7), (1, -0.7)],
    "gancho": [(-1, 0.0), (-0.3, 0.05), (0.45, 0.0), (0.95, 0.45), (0.8, 0.95), (0.4, 0.8)],
    "cume":   [(-1, 0.35), (-0.55, 0.1), (-0.1, -0.6), (0.4, -0.9), (0.85, -0.45), (0.95, 0.25)],
    "concha": [(0.8, -0.8), (0.0, -1.0), (-0.8, -0.4), (-0.9, 0.4), (-0.1, 0.9), (0.9, 0.7)],
    "alca":   [(-1, 0.8), (-0.7, -0.5), (-0.2, -0.95), (0.4, -0.7), (0.7, 0.1), (1.0, 0.9)],
    "degrau": [(-1, -0.8), (-0.3, -0.8), (0.3, 0.8), (1, 0.8)],
}


# ---------- utilidades ----------

def _suave(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


def _reamostrar(pts, passo=1.0):
    """Redistribui a polilinha em pontos a ~passo px um do outro."""
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


def _dist_min(trilha, c):
    return min(math.hypot(x - c[0], y - c[1]) for x, y in trilha)


def _trecho_calmo(trilha, i0, i1, limite=0.9):
    """True se o traço não faz curvas fechadas entre i0 e i1."""
    ang0 = math.atan2(*_tangente(trilha, i0)[::-1])
    for k in range(i0, i1, 3):
        ang = math.atan2(*_tangente(trilha, k)[::-1])
        if abs((ang - ang0 + math.pi) % math.tau - math.pi) > limite:
            return False
    return True


def _bezier(p0, p1, p2, p3, passos=24):
    pts = []
    for i in range(passos + 1):
        t = i / passos
        m = 1 - t
        pts.append((m**3 * p0[0] + 3 * m * m * t * p1[0] + 3 * m * t * t * p2[0] + t**3 * p3[0],
                    m**3 * p0[1] + 3 * m * m * t * p1[1] + 3 * m * t * t * p2[1] + t**3 * p3[1]))
    return pts


# ---------- pincel / pena ----------

def _perfil_px(ent_px, sai_px, minimo=0.2, minimo_sai=None):
    """Pressão: entra fino, engorda, afina. Medido em px de comprimento."""
    ms = minimo if minimo_sai is None else minimo_sai
    def f(i, n):
        if ent_px > 0 and i < ent_px:
            return minimo + (1 - minimo) * _suave(i / ent_px)
        if sai_px > 0 and i > n - 1 - sai_px:
            return ms + (1 - ms) * _suave((n - 1 - i) / sai_px)
        return 1.0
    return f


def _perfil_ruptura(i, n):
    """Engorda até um peso brutal e é cortado quase de repente."""
    t = i / max(1, n - 1)
    f = 1.0 + 0.6 * _suave(t / 0.6)
    if t > 0.92:
        f *= 1 - 0.65 * (t - 0.92) / 0.08
    return f


def _tinta(draw, pts, cor, esp, perfil, contraste, modular=True):
    """Pincelada de pena larga: a espessura depende da direção do traço."""
    pts = _reamostrar(pts, 1.0)
    n = len(pts)
    if n < 2:
        return
    fd = []
    for i in range(n):
        tx, ty = _tangente(pts, i, 3)
        fd.append(abs(math.sin(math.atan2(ty, tx) - ANGULO_PENA)))
    fd = _media_movel(fd, 3)
    fase = random.uniform(0, math.tau)
    freq = random.uniform(1.5, 3.0)
    for i, (x, y) in enumerate(pts):
        t = i / (n - 1)
        f = perfil(i, n) * ((1 - contraste) + contraste * fd[i])
        if modular:
            f *= 0.85 + 0.15 * math.sin(fase + t * freq * math.tau)
        raio = max(0.6, esp * 0.5 * f)
        draw.ellipse([x - raio, y - raio, x + raio, y + raio], fill=cor)


# ---------- formas ----------

def _gancho(p, tang, lado, R, giro, encolhe, para_frente):
    """Espiral que nasce tangente ao traço em p (voluta, crista ou anel)."""
    nx, ny = -tang[1] * lado, tang[0] * lado
    ccx, ccy = p[0] + nx * R, p[1] + ny * R
    a0 = math.atan2(-ny, -nx)
    mx, my = -math.sin(a0), math.cos(a0)
    dot = mx * tang[0] + my * tang[1]
    sentido = 1 if (dot > 0) == para_frente else -1
    n_pts = max(12, int(R * giro / 2))
    pts = []
    for i in range(n_pts + 1):
        t = i / n_pts
        ang = a0 + sentido * giro * t
        r = R * (1 - encolhe * t)
        pts.append((ccx + r * math.cos(ang), ccy + r * math.sin(ang)))
    return pts


def _terminal(trilha, esp, escala=1.0, natural=0.7):
    """Voluta que continua o traço pela ponta final, enrolando para dentro."""
    n = len(trilha)
    t1 = _tangente(trilha, n - 1 - 8, 3)
    t2 = _tangente(trilha, n - 1, 3)
    cruz = t1[0] * t2[1] - t1[1] * t2[0]
    lado = (1 if cruz > 0 else -1) if abs(cruz) > 1e-3 else random.choice([-1, 1])
    if random.random() > natural:
        lado = -lado
    R = esp * random.uniform(2.2, 4.0) * escala
    return _gancho(trilha[-1], t2, lado, R, random.uniform(3.8, 6.0),
                   random.uniform(0.6, 0.78), True)


def _inserir_laco(trilha, i0, comp, lado, b_ratio, c_ratio):
    """Troca o trecho [i0, i0+comp] por um laço cursivo (trocoide) que fecha na mesma corda."""
    i1 = i0 + comp
    p0, p1 = trilha[i0], trilha[i1]
    corda = math.hypot(p1[0] - p0[0], p1[1] - p0[1])
    if corda < 12:
        return trilha
    tx, ty = (p1[0] - p0[0]) / corda, (p1[1] - p0[1]) / corda
    nx, ny = -ty * lado, tx * lado
    a = corda / math.tau
    b, c = a * b_ratio, a * c_ratio
    mx, my = (p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2
    laco = []
    for s in range(29):
        th = -math.pi + math.tau * s / 28
        da = a * th - b * math.sin(th)
        dn = c * (1 + math.cos(th))
        laco.append((mx + tx * da + nx * dn, my + ty * da + ny * dn))
    return trilha[:i0] + laco + trilha[i1 + 1:]


def _bojo(trilha, i, lado, esp):
    """Forma fechada (anel/gota) tangente à espinha; devolve pontos e centro."""
    p = trilha[i]
    tang = _tangente(trilha, i)
    R = esp * random.uniform(1.7, 3.2)
    giro = math.tau * random.uniform(1.0, 1.2)
    pts = _gancho(p, tang, lado, R, giro, random.uniform(0.0, 0.2), random.random() < 0.5)
    s = random.uniform(0.7, 1.5)
    ux, uy = -tang[1], tang[0]
    esticado = []
    for x, y in pts:
        dx, dy = x - p[0], y - p[1]
        a = dx * tang[0] + dy * tang[1]
        b = dx * ux + dy * uy
        esticado.append((p[0] + tang[0] * a * s + ux * b, p[1] + tang[1] * a * s + uy * b))
    centro = (p[0] + ux * lado * R, p[1] + uy * lado * R)
    return esticado, centro


def _ramo(trilha, i, lado, esp, espirais):
    """Ramo que se solta da espinha como esteira de pincel. Devolve pontos."""
    p = trilha[i]
    tx, ty = _tangente(trilha, i)
    tipo = random.choice(["pena", "pena", "crista", "esteira"])
    if tipo == "crista":
        R = esp * random.uniform(1.8, 3.2)
        return _gancho(p, (tx, ty), lado, R, random.uniform(2.4, 3.8), random.uniform(0.35, 0.55), False)
    if tipo == "esteira":
        n = len(trilha)
        comp = random.randint(30, 60)
        i0 = max(0, min(i, n - comp - 2))
        if not _trecho_calmo(trilha, i0, i0 + comp, 0.9):
            return []
        dist = esp * random.uniform(1.8, 2.8)
        amp = esp * random.uniform(0.5, 1.0)
        per = random.uniform(18, 30)
        pts = []
        for k in range(i0, i0 + comp):
            ax, ay = _tangente(trilha, k)
            off = dist + amp * math.sin(math.tau * (k - i0) / per)
            pts.append((trilha[k][0] - ay * lado * off, trilha[k][1] + ax * lado * off))
        return pts
    # pena: sai tangente e se afasta curvando
    sentido = random.choice([-1, 1])
    ux, uy = tx * sentido, ty * sentido
    nx, ny = -ty * lado, tx * lado
    c = esp * random.uniform(5, 10)
    pts = _bezier(p,
                  (p[0] + ux * c * 0.55, p[1] + uy * c * 0.55),
                  (p[0] + ux * c * 0.90 + nx * c * 0.45, p[1] + uy * c * 0.90 + ny * c * 0.45),
                  (p[0] + ux * c * 0.65 + nx * c * 0.95, p[1] + uy * c * 0.65 + ny * c * 0.95))
    if random.random() < espirais:
        pts = pts + _terminal(pts, esp, 0.6, 0.8)[1:]
    return pts


def _marca(trilha, i, lado, esp):
    """Marca solta ao lado da espinha (ponto, par de pontos, acento ou onda curta)."""
    p = trilha[i]
    tx, ty = _tangente(trilha, i)
    nx, ny = -ty * lado, tx * lado
    d = esp * random.uniform(3.4, 5.5)
    c = (p[0] + nx * d + tx * random.uniform(-8, 8), p[1] + ny * d + ty * random.uniform(-8, 8))
    tipo = random.choice(["ponto", "ponto", "dois", "acento", "onda"])
    if tipo == "ponto":
        return c, [("ponto", c, esp * random.uniform(0.6, 0.9))]
    if tipo == "dois":
        s = esp * 1.6
        return c, [("ponto", (c[0] - tx * s, c[1] - ty * s), esp * 0.6),
                   ("ponto", (c[0] + tx * s, c[1] + ty * s), esp * 0.6)]
    if tipo == "acento":
        R = esp * random.uniform(2.2, 3.6)
        base = math.atan2(ny, nx)
        sweep = random.uniform(1.2, 1.9)
        pts = [(c[0] + R * math.cos(base + sweep * (k / 14 - 0.5)) - nx * R,
                c[1] + R * math.sin(base + sweep * (k / 14 - 0.5)) - ny * R) for k in range(15)]
        return c, [("traco", pts, esp * 0.8, _perfil_px(R * sweep * 0.35, R * sweep * 0.35, 0.2), True)]
    comp = esp * 3.2
    pts = [(c[0] + tx * (k - 10) / 10 * comp + nx * math.sin(k / 20 * math.tau) * esp * 1.1,
            c[1] + ty * (k - 10) / 10 * comp + ny * math.sin(k / 20 * math.tau) * esp * 1.1) for k in range(21)]
    return c, [("traco", pts, esp * 0.9, _perfil_px(comp * 0.3, comp * 0.3, 0.2), True)]


def _molde(n):
    nome = random.choice(["rio"] + list(MOLDES))
    if nome == "rio":
        k = max(4, n)
        sinal = random.choice([-1, 1])
        pts = []
        for i in range(k):
            u = -1 + 2 * i / (k - 1)
            if 0 < i < k - 1:
                u += random.uniform(-0.2, 0.2) * 2 / (k - 1)
            pts.append([u, sinal * random.uniform(0.25, 1.1)])
            sinal = -sinal
        pts[0][1] *= 0.3
        pts[-1][1] *= 0.3
    else:
        su, sv = random.uniform(0.75, 1.0), random.uniform(0.65, 1.1)
        pts = [[(u + random.uniform(-0.06, 0.06)) * su, (v + random.uniform(-0.1, 0.1)) * sv] for u, v in MOLDES[nome]]
    fu, fv, inv = random.random() < 0.5, random.random() < 0.5, random.random() < 0.5
    pts = [(-u if fu else u, -v if fv else v) for u, v in pts]
    if inv:
        pts.reverse()
    return pts


# ---------- compilador da família ----------

def aplicar(draw, config, cx, cy, n, step, margem, cor, esp, estilo):
    mar = config.get("marinha", {})
    if not mar:
        return

    corrente = mar.get("corrente", 0.7)
    contraste = mar.get("contraste", 0.8)
    p_espirais = mar.get("espirais", 0)
    vertical = random.random() < mar.get("vertical", 0)
    ruptura = random.random() < mar.get("ruptura", 0)

    # 1. ESPINHA: molde fluido escolhido, suavizado e mapeado ao eixo
    L = min(cx, cy) * 0.70
    A = L * (0.22 + 0.38 * corrente)
    ctrl = [(u * L, v * A) for u, v in _molde(n)]
    trilha = _reamostrar(suavizar_esqueleto(ctrl, iteracoes=3), 1.0)
    trilha = [(cx + v, cy + u) if vertical else (cx + u, cy + v) for u, v in trilha]

    # 2. LAÇOS CURSIVOS (último slot primeiro, para os índices não se deslocarem)
    for s in (1, 0):
        if random.random() < mar.get("lacos", 0):
            comp = random.randint(30, 48)
            N0 = len(trilha)
            i0 = int(N0 * (s + random.uniform(0.3, 0.7)) / 2) - comp // 2
            lado = random.choice([-1, 1])
            b_r, c_r = random.uniform(1.7, 2.3), random.uniform(1.5, 2.4)
            if i0 > 8 and i0 + comp < N0 - 8 and _trecho_calmo(trilha, i0, i0 + comp, 0.7):
                trilha = _inserir_laco(trilha, i0, comp, lado, b_r, c_r)

    # 3. VOLUTAS NAS PONTAS (a ponta final vira ruptura, se sorteada)
    ent_px, sai_px = 8, 10
    espiral_fim = espiral_ini = False
    if not ruptura and random.random() < p_espirais:
        sp = _terminal(trilha, esp)
        trilha = trilha + sp[1:]
        sai_px = _comprimento(sp)
        espiral_fim = True
    if random.random() < p_espirais * 0.8:
        sp = _terminal(trilha[::-1], esp)
        trilha = sp[::-1] + trilha[1:]
        ent_px = _comprimento(sp)
        espiral_ini = True
    trilha = _reamostrar(trilha, 1.0)
    fim = "afilar"
    if not ruptura and not espiral_fim:
        fim = random.choice(["afilar", "afilar", "cortar", "bulbo"])
        if fim == "cortar":
            sai_px = 3
    bulbo_ini = (not espiral_ini) and random.random() < 0.25
    N = len(trilha)
    if N < 40:
        return

    elementos = []
    elementos.append(("traco", trilha, esp * 1.9,
                      _perfil_px(ent_px, 0 if ruptura else sai_px, 0.25,
                                 0.85 if fim == "cortar" else 0.25), True))
    if fim == "bulbo":
        elementos.append(("ponto", trilha[-1], esp * 1.0))
    if bulbo_ini:
        elementos.append(("ponto", trilha[0], esp * 0.9))

    lo, hi = int(ent_px) + 8, N - int(sai_px) - 8
    if hi <= lo:
        lo, hi = int(N * 0.15), int(N * 0.85)

    # 4. BOJOS (formas fechadas)
    usados = []
    for _ in range(2):
        if random.random() < mar.get("bojos", 0):
            i = random.randint(lo, hi)
            if any(abs(i - j) < 40 for j in usados) or not _trecho_calmo(trilha, max(0, i - 8), min(N - 1, i + 8), 0.5):
                continue
            usados.append(i)
            pts, centro = _bojo(trilha, i, random.choice([-1, 1]), esp)
            elementos.append(("traco", pts, esp * 0.9, _perfil_px(4, 14, 0.25), True))
            if random.random() < 0.4:
                elementos.append(("ponto", centro, esp * 0.55))

    # 5. RAMOS (esteiras de pincel que se soltam da espinha)
    for _ in range(4):
        if random.random() < mar.get("ramos", 0):
            i = random.randint(lo, hi)
            if any(abs(i - j) < 26 for j in usados):
                continue
            usados.append(i)
            pts = _ramo(trilha, i, random.choice([-1, 1]), esp, p_espirais)
            if len(pts) > 6:
                elementos.append(("traco", pts, esp * 0.9, _perfil_px(3, _comprimento(pts) * 0.6, 0.15), True))

    # 6. MARCAS soltas (estilo Badlit)
    for _ in range(3):
        if random.random() < mar.get("marcas", 0):
            for _tentativa in range(6):
                i = random.randint(int(N * 0.1), int(N * 0.9))
                c, els = _marca(trilha, i, random.choice([-1, 1]), esp)
                if _dist_min(trilha, c) > esp * 2.6:
                    elementos.extend(els)
                    break

    # 7. CONTRA-CORRENTE: gancho pesado cortado de repente
    if ruptura:
        tang = _tangente(trilha, N - 1, 6)
        gan = _gancho(trilha[-1], tang, random.choice([-1, 1]), esp * random.uniform(3.0, 4.6),
                      random.uniform(2.8, 4.2), random.uniform(0.25, 0.4), True)
        elementos.append(("traco", gan, esp * 1.8, _perfil_ruptura, False))

    # 8. ENQUADRAMENTO: centraliza e, se necessário, reduz para caber no canvas
    xs, ys = [], []
    for el in elementos:
        if el[0] == "traco":
            xs += [p[0] for p in el[1]]
            ys += [p[1] for p in el[1]]
        else:
            xs += [el[1][0] - el[2], el[1][0] + el[2]]
            ys += [el[1][1] - el[2], el[1][1] + el[2]]
    ox, oy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
    k = min(1.0, min(cx, cy) * 2 * 0.92 / max(max(xs) - min(xs), max(ys) - min(ys), 1.0))

    def T(p):
        return (cx + (p[0] - ox) * k, cy + (p[1] - oy) * k)

    for el in elementos:
        if el[0] == "traco":
            _, pts, e, perfil, modular = el
            _tinta(draw, [T(p) for p in pts], cor, e, perfil, contraste, modular)
        else:
            x, y = T(el[1])
            r = max(1.5, el[2])
            draw.ellipse([x - r, y - r, x + r, y + r], fill=cor)