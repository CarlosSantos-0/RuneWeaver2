"""Família Lunar do Omni-Forja.

Composição em quatro estágios (nada aqui é um glifo pronto):

1. ESTRUTURA PRINCIPAL  – um de sete esqueletos paramétricos (crescente,
   haste com estações, órbita, interseção de círculos, laço com cauda,
   arcos opostos, trio crescente-orbe). O esqueleto cria seus componentes e
   registra ÂNCORAS nomeadas (ponta de arco, berço do crescente, costas,
   fim de haste, estação, interseção, vão, centro, satélite).
2. SECUNDÁRIOS          – só se encaixam em âncoras livres, por regras de
   tangência/encontro próprias de cada tipo de âncora. Um teste de colisão
   por amostragem rejeita (ou encolhe) o que congestiona o glifo.
3. PONTOS               – só nascem em âncoras com função: terminação,
   berço, interseção, centro de órbita, satélite, vão.
4. RENDERIZAÇÃO         – o glifo é construído em espaço unitário, centrado
   e escalado de modo uniforme (relações preservadas) e desenhado com
   `traco_roteador`, respeitando os estilos de traço do projeto.

Chaves lidas de config["lunar"] (todas opcionais):
  caligrafia      -> ligaduras entre arcos e caudas curvas
  fases           -> crescentes secundários, trio lunar
  orbitas/eclipse -> círculos e orbes
  auxiliares      -> pontos
  hastes          -> hastes, travessões, caudas
  arcos_internos  -> crescentes/arcos aninhados no berço
"""
import math
import random

from motor.utilitarios import traco_roteador, suavizar_esqueleto

TAU = 2 * math.pi
PX = 56.0  # pixels nominais por unidade (só para dimensionar folgas/pontos)


# --------------------------------------------------------------------------
# Geometria básica (espaço unitário)
# --------------------------------------------------------------------------
def _mais(p, ang, k):
    return (p[0] + math.cos(ang) * k, p[1] + math.sin(ang) * k)


def _dist(p, q):
    return math.hypot(p[0] - q[0], p[1] - q[1])


def _ang(p, q):
    return math.atan2(q[1] - p[1], q[0] - p[0])


def _dir8():
    return random.randrange(8) * math.pi / 4


def _arco(c, r, a0, a1, passo=math.radians(5)):
    n = max(6, int(abs(a1 - a0) / passo) + 1)
    return [(c[0] + r * math.cos(a0 + (a1 - a0) * i / n),
             c[1] + r * math.sin(a0 + (a1 - a0) * i / n)) for i in range(n + 1)]


def _circulo(c, r):
    return _arco(c, r, 0, TAU)


def _arco_por(c, r, p_ini, p_fim, ang_passagem):
    """Arco de (c, r) indo de p_ini a p_fim pelo lado que contém ang_passagem."""
    ai, af = _ang(c, p_ini), _ang(c, p_fim)
    ccw = (af - ai) % TAU
    off = (ang_passagem - ai) % TAU
    varredura = ccw if off <= ccw else ccw - TAU
    pts = _arco(c, r, ai, ai + varredura)
    pts[0], pts[-1] = p_ini, p_fim
    return pts


def _inter(A, r1, B, r2):
    d = _dist(A, B)
    a = (d * d + r1 * r1 - r2 * r2) / (2 * d)
    h2 = r1 * r1 - a * a
    if h2 <= 0:
        return None
    h = math.sqrt(h2)
    ux, uy = (B[0] - A[0]) / d, (B[1] - A[1]) / d
    P = (A[0] + ux * a, A[1] + uy * a)
    return (P[0] - uy * h, P[1] + ux * h), (P[0] + uy * h, P[1] - ux * h)


def _crescente(c1, R, theta, w, d):
    """Crescente: círculo externo (c1, R) e interno deslocado d rumo à boca.

    As duas pontas são compartilhadas; `theta` é a direção da boca.
    """
    u = (math.cos(theta), math.sin(theta))
    t1 = _mais(c1, theta + w, R)
    t2 = _mais(c1, theta - w, R)
    C2 = (c1[0] + u[0] * d, c1[1] + u[1] * d)
    R2 = _dist(C2, t1)
    ext = _arco_por(c1, R, t1, t2, theta + math.pi)
    inn = _arco_por(C2, R2, t2, t1, theta + math.pi)
    return dict(
        c1=c1, R=R, theta=theta, w=w, d=d, ext=ext, inn=inn, R2=R2, C2=C2,
        t1=t1, t2=t2,
        B2=(C2[0] - u[0] * R2, C2[1] - u[1] * R2),          # fundo do berço
        costas=(c1[0] - u[0] * R, c1[1] - u[1] * R),         # ponto mais externo
        chifre=R * math.cos(w) - d + R2,                     # alcance das pontas a partir do berço
        tracos=[ext + inn[1:]],
    )


def _d_para_espessura(R, w, esp_min, d0):
    """Menor d >= d0 cuja espessura nas costas do crescente atinge esp_min."""
    d = d0
    for _ in range(40):
        R2 = math.sqrt(max(1e-6, R * R - 2 * d * R * math.cos(w) + d * d))
        if R - R2 + d >= esp_min:
            return d
        d *= 1.1
    return d


def _crescente_por_berco(B2, theta, R, w, d):
    R2 = math.sqrt(max(1e-6, R * R - 2 * d * R * math.cos(w) + d * d))
    c1 = _mais(B2, theta, R2 - d)
    return _crescente(c1, R, theta, w, d)


def _crescente_por_costas(costas, theta, R, w, d):
    return _crescente(_mais(costas, theta, R), R, theta, w, d)


# --------------------------------------------------------------------------
# Glifo: componentes, âncoras e teste de colisão
# --------------------------------------------------------------------------
class _Glifo:
    def __init__(self, esp):
        self.esp = esp
        self.folga = max(0.16, esp * 2.8 / PX)      # distância mínima entre traços
        self.r_min = max(0.15, esp * 2.2 / PX + 0.07)  # menor círculo legível
        self.esp_min = esp * 2.4 / PX + 0.06        # espessura mínima de crescente
        self.comps = []
        self.pontos = []
        self.ancoras = []
        self.n_sec = 0
        self.tema = None
        self.lados = (1,)
        self.orcamento = random.choice((2, 3, 3, 4))  # máx. de secundários
        self.nome = ''
        self.completo = False  # esqueleto já suficiente: dispensa secundário forçado
        self.log = []

    @staticmethod
    def _amostrar(tracos, pontos):
        out = []
        for pts in tracos:
            for p, q in zip(pts, pts[1:]):
                n = max(1, int(_dist(p, q) / 0.05))
                for i in range(n):
                    t = i / n
                    out.append(((p[0] + (q[0] - p[0]) * t,
                                 p[1] + (q[1] - p[1]) * t), 0.0))
            out.append((pts[-1], 0.0))
        for c, rpx in pontos:
            out.append((c, rpx / PX))
        return out

    def add(self, tracos, pontos=()):
        cid = len(self.comps)
        self.comps.append(dict(id=cid, tracos=tracos,
                               amostras=self._amostrar(tracos, pontos)))
        self.pontos.extend(pontos)
        return cid

    def tentar(self, tracos, pontos=(), ignorar=(), perto=None, host=None):
        """Adiciona o componente se houver espaço; devolve o id ou None.

        `perto=(ponto, raio)` dispensa a checagem contra as amostras do
        componente `host` vizinhas ao ponto de encaixe (o encontro é intencional);
        todos os demais componentes continuam sendo respeitados.
        """
        novas = self._amostrar(tracos, pontos)
        for comp in self.comps:
            if comp['id'] in ignorar:
                continue
            for q, s in comp['amostras']:
                if (perto is not None and (host is None or comp['id'] == host)
                        and _dist(q, perto[0]) < perto[1]):
                    continue
                lim = self.folga + s
                for p, r in novas:
                    if abs(p[0] - q[0]) < lim + r and _dist(p, q) < lim + r:
                        return None
        self.n_sec += 1
        return self.add(tracos, pontos)

    def ancora(self, tipo, pt, ang, host=None, nivel=0, **extra):
        a = dict(tipo=tipo, pt=pt, ang=ang, host=host, nivel=nivel, usada=False)
        a.update(extra)
        self.ancoras.append(a)
        return a


def _sortear(opcoes, fator=1.0):
    """Escolhe no máximo uma opção; os pesos são probabilidades."""
    total = sum(max(0.0, p) * fator for _, p in opcoes)
    if total <= 0 or random.random() >= min(1.0, total):
        return None
    x = random.random() * total
    for nome, p in opcoes:
        x -= max(0.0, p) * fator
        if x <= 0:
            return nome
    return opcoes[-1][0]


# --------------------------------------------------------------------------
# Esqueletos (estrutura principal + âncoras)
# --------------------------------------------------------------------------
def _ancorar_crescente(g, cr, cid, tips=True, nivel=0):
    if tips:
        g.ancora('ponta', cr['t1'], _ang(cr['ext'][1], cr['ext'][0]), cid)
        g.ancora('ponta', cr['t2'], _ang(cr['ext'][-2], cr['ext'][-1]), cid)
    g.ancora('berco', cr['B2'], cr['theta'], cid, cr=cr)
    g.ancora('costas', cr['costas'], cr['theta'] + math.pi, cid, cr=cr)


def _est_crescente(g, cfg):
    theta = _dir8()
    w = random.uniform(1.0, 1.4)
    d = _d_para_espessura(1.0, w, g.esp_min, random.uniform(0.14, 0.5))
    cr = _crescente((0, 0), 1.0, theta, w, d)
    cid = g.add(cr['tracos'])
    _ancorar_crescente(g, cr, cid)


def _est_haste(g, cfg):
    ang = random.choice((math.pi / 2, math.pi / 2, math.pi / 2, 0,
                         math.pi / 4, -math.pi / 4))
    L = random.uniform(0.95, 1.35)
    p0, p1 = _mais((0, 0), ang + math.pi, L), _mais((0, 0), ang, L)
    cid = g.add([[p0, p1]])
    g.ancora('haste_fim', p1, ang, cid)
    g.ancora('haste_fim', p0, ang + math.pi, cid)
    k = random.choice((1, 2, 2, 3))
    if k == 1:
        ts = [random.uniform(-0.4, 0.4) * L]
    elif k == 2:
        ts = [-0.5 * L + random.uniform(-0.1, 0.1), 0.5 * L + random.uniform(-0.1, 0.1)]
    else:
        ts = [-0.66 * L, 0.0, 0.66 * L]
    g.tema = random.choice(('D', 'orbe', 'travessao', 'fase'))
    g.lados = random.choice(((1,), (-1,), (1,), (-1,), (1, -1)))
    folga_entre = 0.5 if k == 3 else 0.9
    for t in ts:
        g.ancora('estacao', _mais((0, 0), ang, t), ang, cid,
                 raio_max=min(0.5, folga_entre * 0.5 * L / (k * 0.6 + 0.4)))
    g.orcamento = max(g.orcamento, k + 1)


def _est_orbita(g, cfg):
    R = 1.0
    alfa = random.uniform(0, TAU)
    aberto = random.random() < 0.85
    if aberto:
        gap = random.uniform(0.9, 2.3)
        pts = _arco((0, 0), R, alfa + gap / 2, alfa + TAU - gap / 2)
        cid = g.add([pts])
        g.ancora('ponta', pts[0], _ang(pts[1], pts[0]), cid)
        g.ancora('ponta', pts[-1], _ang(pts[-2], pts[-1]), cid)
        phi = alfa + math.pi + random.uniform(-0.5, 0.5)
    else:
        cid = g.add([_circulo((0, 0), R)])
        phi = random.uniform(0, TAU)
    g.ancora('satelite', _mais((0, 0), alfa, R), alfa, cid)

    corpo = _sortear_peso([('lua', 3), ('cresc', 3), ('diam', 2), ('raio', 1.3),
                           ('conc', 1)])
    if corpo == 'lua':
        ri = random.uniform(0.3, 0.55)
        c = _mais((0, 0), phi, R - ri)
        i2 = g.add([_circulo(c, ri)])
        g.ancora('centro', c, 0, i2, r=ri)
    elif corpo == 'cresc':
        Rc = random.uniform(0.42, 0.68)
        w = random.uniform(1.05, 1.4)
        d = _d_para_espessura(Rc, w, g.esp_min, random.uniform(0.14, 0.4) * Rc)
        cr = _crescente_por_costas(_mais((0, 0), phi, R), phi + math.pi, Rc, w, d)
        i2 = g.add(cr['tracos'])
        g.ancora('berco', cr['B2'], cr['theta'], i2, cr=cr)
    elif corpo == 'diam':
        beta = random.choice((phi, alfa + math.pi / 2, math.pi / 2, 0))
        e = random.choice((0.0, 0.0, random.uniform(0.15, 0.4)))
        a, b = _mais((0, 0), beta + math.pi, R + e), _mais((0, 0), beta, R + e)
        i2 = g.add([[a, b]])
        g.ancora('haste_fim', b, beta, i2)
        g.ancora('haste_fim', a, beta + math.pi, i2)
        g.ancora('centro', (0, 0), 0, i2, r=R)
    elif corpo == 'raio':
        beta = phi
        e = random.choice((0.0, random.uniform(0.15, 0.45)))
        b = _mais((0, 0), beta, R + e)
        i2 = g.add([[(0, 0), b]])
        g.ancora('haste_fim', b, beta, i2)
        g.ancora('centro', (0, 0), 0, i2, r=R)
    elif corpo == 'conc':
        rc = random.uniform(0.22, 0.36)
        i2 = g.add([_circulo((0, 0), rc)])
        g.ancora('centro', (0, 0), 0, i2, r=rc)


def _sortear_peso(opcoes):
    total = sum(p for _, p in opcoes)
    x = random.random() * total
    for nome, p in opcoes:
        x -= p
        if x <= 0:
            return nome
    return opcoes[-1][0]


def _est_lentes(g, cfg):
    theta = _dir8()
    u = (math.cos(theta), math.sin(theta))
    r1 = 1.0
    r2 = random.uniform(0.62, 1.0)
    lo, hi = abs(r1 - r2) + 0.3, r1 + r2 - 0.3
    dd = random.uniform(lo, hi) if lo < hi else (lo + hi) / 2
    A = (-u[0] * dd / 2, -u[1] * dd / 2)
    B = (u[0] * dd / 2, u[1] * dd / 2)
    I1, I2 = _inter(A, r1, B, r2)
    modo = _sortear_peso([('fase', 3), ('uniao', 3), ('lente', 2), ('dois', 1.2)])
    if modo == 'fase':
        tr = [_circulo(A, r1), _arco_por(B, r2, I1, I2, theta + math.pi)]
    elif modo == 'uniao':
        a_out = _arco_por(A, r1, I1, I2, theta + math.pi)
        b_out = _arco_por(B, r2, I2, I1, theta)
        tr = [a_out + b_out[1:]]
    elif modo == 'lente':
        a_in = _arco_por(A, r1, I1, I2, theta)
        b_in = _arco_por(B, r2, I2, I1, theta + math.pi)
        tr = [a_in + b_in[1:]]
    else:
        tr = [_circulo(A, r1), _circulo(B, r2)]
    cid = g.add(tr)
    g.ancora('intersecao', I1, 0, cid)
    g.ancora('intersecao', I2, 0, cid)
    if modo in ('fase', 'dois'):
        g.ancora('centro', A, 0, cid, r=r1)
    if modo in ('uniao', 'dois'):
        g.ancora('centro', B, 0, cid, r=r2)
    if random.random() < cfg['hastes'] * 1.1:
        if random.random() < 0.55:
            ts = [p[0] * u[0] + p[1] * u[1] for t in tr for p in t]
            e1, e2 = random.uniform(0.0, 0.35), random.uniform(0.0, 0.35)
            a, b = _mais((0, 0), theta + math.pi, -min(ts) + e1), _mais((0, 0), theta, max(ts) + e2)
            hd = theta
        else:
            n = _ang(I1, I2)
            e = random.uniform(0.0, 0.35)
            a, b = _mais(I1, n + math.pi, e), _mais(I2, n, e)
            hd = n
        i2 = g.add([[a, b]])
        g.ancora('haste_fim', b, hd, i2)
        g.ancora('haste_fim', a, hd + math.pi, i2)


def _est_laco(g, cfg):
    r = random.uniform(0.5, 0.85)
    phi = _dir8() + random.uniform(-0.2, 0.2)
    s = random.choice((1, -1))
    P = _mais((0, 0), phi, r)
    ang_t = phi + s * math.pi / 2
    Lt = random.uniform(1.0, 1.9)
    aberto = random.random() < 0.45
    if aberto:
        sweep = random.uniform(4.3, 5.6)
        pts = _arco((0, 0), r, phi, phi - s * sweep)
        cid_c = g.add([pts])
        g.ancora('ponta', pts[-1], _ang(pts[-2], pts[-1]), cid_c)
    else:
        cid_c = g.add([_circulo((0, 0), r)])
    g.ancora('centro', (0, 0), 0, cid_c, r=r)

    curva = random.random() < cfg['caligrafia'] * 0.45
    if curva:
        lado = random.choice((1, -1))
        n = ang_t + lado * math.pi / 2
        ctrl = [P, _mais(P, ang_t, Lt * 0.5),
                _mais(_mais(P, ang_t, Lt * 0.9), n, Lt * 0.3)]
        cauda = suavizar_esqueleto(ctrl, iteracoes=3)
        fim, fim_ang = cauda[-1], _ang(cauda[-2], cauda[-1])
    else:
        fim = _mais(P, ang_t, Lt)
        cauda = [P, fim]
        fim_ang = ang_t
    cid_t = g.add([cauda])
    g.ancora('haste_fim', fim, fim_ang, cid_t)
    if not curva:
        g.tema = random.choice(('travessao', 'orbe', 'fase', 'D'))
        g.lados = random.choice(((1,), (-1,), (1, -1)))
        g.ancora('estacao', _mais(P, ang_t, Lt * random.uniform(0.45, 0.7)),
                 ang_t, cid_t, raio_max=0.3)


def _est_parenteses(g, cfg):
    theta = _dir8()
    u = (math.cos(theta), math.sin(theta))
    n = theta + math.pi / 2
    modo = random.choice(('fora', 'dentro'))
    ra, rb = random.uniform(0.6, 1.0), random.uniform(0.6, 1.0)
    sa, sb = random.uniform(1.7, 2.7), random.uniform(1.7, 2.7)
    if modo == 'dentro':
        sep = ra + rb + random.uniform(0.3, 0.7)
    else:
        sep = 0.22 * (ra + rb) + random.uniform(0.45, 0.9)
    off = random.choice((0.0, random.choice((-1, 1)) * random.uniform(0.15, 0.5)))
    A = (-u[0] * sep / 2, -u[1] * sep / 2)
    B = (u[0] * sep / 2 + math.cos(n) * off, u[1] * sep / 2 + math.sin(n) * off)
    ta, tb = (theta, theta + math.pi) if modo == 'dentro' else (theta + math.pi, theta)
    arc_a = _arco(A, ra, ta - sa / 2, ta + sa / 2)
    arc_b = _arco(B, rb, tb - sb / 2, tb + sb / 2)
    ca, cb = g.add([arc_a]), g.add([arc_b])
    g.orcamento = min(g.orcamento, 2)
    for pts, cid in ((arc_a, ca), (arc_b, cb)):
        g.ancora('ponta', pts[0], _ang(pts[1], pts[0]), cid, semcauda=True)
        g.ancora('ponta', pts[-1], _ang(pts[-2], pts[-1]), cid, semcauda=True)
    if random.random() < cfg['caligrafia'] * 0.5:
        # ligadura: une as pontas do mesmo lado, fechando os dois arcos numa
        # só forma em vez de deixá-los soltos
        k = random.choice((0, -1))
        pa, pb = arc_a[k], arc_b[k]
        g.add([[pa, pb]])
        for a in g.ancoras:
            if a['pt'] in (pa, pb):
                a['usada'] = True
    mA, mB = _mais(A, ta, ra), _mais(B, tb, rb)
    vao = ((mA[0] + mB[0]) / 2, (mA[1] + mB[1]) / 2) if modo == 'dentro' \
        else ((A[0] + B[0]) / 2, (A[1] + B[1]) / 2)
    g.ancora('vao', vao, 0, ca, folga_r=_dist(mA, mB) / 2 if modo == 'dentro' else sep / 2)
    if random.random() < cfg['hastes'] * 0.8:
        i3 = g.add([[mA, mB]])
        g.ancora('haste_fim', mB, _ang(mA, mB), i3, nivel=1)
        g.ancora('haste_fim', mA, _ang(mB, mA), i3, nivel=1)


def _est_trio(g, cfg):
    """Crescente - orbe - (crescente | ponto | haste) ao longo de um eixo.

    As costas de cada crescente tocam (ou quase) a órbita central e as bocas
    ficam voltadas para fora: os crescentes flanqueiam a órbita em vez de
    cercá-la, e a composição se resolve sem sobreposição.
    """
    theta = _dir8()
    f = g.folga
    g.completo = True
    g.orcamento = 0  # a própria composição já é completa; só entram pontos
    ro = random.uniform(max(g.r_min, 0.26), 0.45)
    co = g.add([_circulo((0, 0), ro)])
    g.ancora('centro', (0, 0), 0, co, r=ro)
    segundo = random.choice(('cresc', 'cresc', 'cresc', 'ponto', 'haste'))
    R0 = random.uniform(0.4, 0.7)
    w0 = random.uniform(1.0, 1.4)
    simetrico = random.random() < 0.5
    gap = random.choice((0.0, 0.0, random.uniform(1.2, 2.0) * f))
    for lado in (-1, 1):
        mouth = theta + math.pi if lado == -1 else theta
        costas = _mais((0, 0), mouth, ro + gap)  # costas rente à órbita, boca para fora
        if lado == 1 and segundo != 'cresc':
            if segundo == 'ponto':
                g.ancora('satelite', _mais((0, 0), theta, ro + 0.5), theta, co)
            else:
                fim = _mais((0, 0), theta, ro + random.uniform(0.5, 0.9))
                ch = g.add([[_mais((0, 0), theta, ro), fim]])
                g.ancora('haste_fim', fim, theta, ch)
            continue
        if simetrico or lado == -1:
            R, w = R0, w0
        else:
            R, w = R0 * random.uniform(0.7, 1.0), random.uniform(1.0, 1.4)
        d = _d_para_espessura(R, w, g.esp_min, random.uniform(0.14, 0.45) * R)
        cr = _crescente_por_costas(costas, mouth, R, w, d)
        cid = g.add(cr['tracos'])
        _ancorar_crescente(g, cr, cid)
        if gap > 0:
            g.add([[costas, _mais((0, 0), mouth, ro)]])


# --------------------------------------------------------------------------
# Secundários: regras por tipo de âncora
# --------------------------------------------------------------------------
def _orbe_terminal(g, a):
    for _ in range(4):
        r = max(random.uniform(0.15, 0.27), g.r_min)
        c = _mais(a['pt'], a['ang'], r)
        if g.tentar([_circulo(c, r)], perto=(a['pt'], 2 * r + g.folga), host=a['host']) is not None:
            return True
    return False


def _cauda(g, a):
    for _ in range(4):
        q = _mais(a['pt'], a['ang'], random.uniform(0.35, 0.95))
        cid = g.tentar([[a['pt'], q]], perto=(a['pt'], 2 * g.folga), host=a['host'])
        if cid is not None:
            g.ancora('haste_fim', q, a['ang'], cid, nivel=a['nivel'] + 1)
            return True
    return False


def _travessao_fim(g, a):
    n = a['ang'] + math.pi / 2
    for _ in range(3):
        h = random.uniform(0.2, 0.4)
        pts = [_mais(a['pt'], n, h), _mais(a['pt'], n + math.pi, h)]
        if g.tentar([pts], perto=(a['pt'], 2 * g.folga), host=a['host']) is not None:
            return True
    return False


def _cresc_cap(g, a):
    for _ in range(6):
        R = random.uniform(0.26, 0.42)
        w = random.uniform(1.1, 1.4)
        d = _d_para_espessura(R, w, g.esp_min, random.uniform(0.14, 0.4) * R)
        cr = _crescente_por_costas(a['pt'], a['ang'], R, w, d)
        if g.tentar(cr['tracos'], perto=(a['pt'], 1.8 * R), host=a['host']) is not None:
            return True
    return False


def _berco_orbe(g, a):
    cr = a['cr']
    u = cr['theta']
    rr0 = random.uniform(0.28, 0.5) * cr['R2']
    folga_gap = random.choice((0.0, 0.0, random.uniform(1.2, 2.0) * g.folga))
    for k in range(10):
        rr = rr0 * 0.9 ** k
        if rr < g.r_min:
            break
        c = _mais(cr['B2'], u, rr + folga_gap)
        if min(_dist(c, cr['t1']), _dist(c, cr['t2'])) - rr < g.folga * 1.3:
            continue
        if g.tentar([_circulo(c, rr)], perto=(cr['B2'], 2.2 * rr + folga_gap), host=a['host']) is not None:
            return True
    return False


def _berco_aninhado(g, a):
    cr = a['cr']
    for k in range(10):
        Rn = random.uniform(0.34, 0.6) * cr['R2'] * 0.92 ** k
        if Rn < 0.2:
            break
        wn = random.uniform(1.05, 1.4)
        dn = _d_para_espessura(Rn, wn, g.esp_min, random.uniform(0.14, 0.4) * Rn)
        folga_gap = random.choice((0.0, 1.4 * g.folga, 1.4 * g.folga))
        cn = _crescente_por_costas(_mais(cr['B2'], cr['theta'], folga_gap),
                                   cr['theta'], Rn, wn, dn)
        if g.tentar(cn['tracos'], perto=(cr['B2'], 1.7 * Rn + folga_gap),
                    host=a['host']) is not None:
            return True
    return False


def _berco_axial(g, a):
    cr = a['cr']
    u = cr['theta']
    ini = _mais(cr['costas'], u + math.pi, random.choice((0.0, random.uniform(0.15, 0.5))))
    fim = _mais(cr['B2'], u, random.uniform(0.4, 1.1) * cr['chifre'])
    cid = g.tentar([[ini, fim]], ignorar=(a['host'],))
    if cid is None:
        return False
    g.ancora('haste_fim', fim, u, cid, nivel=1)
    g.ancora('haste_fim', ini, u + math.pi, cid, nivel=1)
    return True


def _cabo(g, a):
    cr = a['cr']
    u = cr['theta'] + math.pi
    fim = _mais(cr['costas'], u, random.uniform(0.5, 1.1))
    cid = g.tentar([[cr['costas'], fim]], perto=(cr['costas'], 0.1), host=a['host'])
    if cid is None:
        return False
    g.ancora('haste_fim', fim, u, cid, nivel=1)
    return True


def _estacao(g, a):
    pt, ang = a['pt'], a['ang']
    ok = False
    for s in g.lados:
        n = ang + s * math.pi / 2
        if g.tema == 'D':
            r = max(min(random.uniform(0.26, 0.48), a['raio_max']), g.r_min)
            ok |= g.tentar([_arco(pt, r, ang, ang + s * math.pi)],
                           perto=(pt, 2 * r + g.folga), host=a['host']) is not None
        elif g.tema == 'orbe':
            r = max(random.uniform(0.2, 0.38), g.r_min)
            c = _mais(pt, n, r)
            ok |= g.tentar([_circulo(c, r)], perto=(pt, 2 * r + g.folga), host=a['host']) is not None
        elif g.tema == 'travessao':
            h = random.uniform(0.22, 0.5)
            if len(g.lados) == 2:
                pts = [_mais(pt, n, h), _mais(pt, n + math.pi, h)]
            else:
                pts = [_mais(pt, n + math.pi, h * 0.5), _mais(pt, n, h)]
            ok |= g.tentar([pts], ignorar=(a['host'],)) is not None
        else:  # 'fase': crescente com as costas encostadas na haste
            R = min(random.uniform(0.26, 0.45), max(0.26, a['raio_max'] * 1.8))
            w = random.uniform(1.1, 1.4)
            d = _d_para_espessura(R, w, g.esp_min, random.uniform(0.14, 0.4) * R)
            cr = _crescente_por_costas(pt, n, R, w, d)
            ok |= g.tentar(cr['tracos'], perto=(pt, 1.6 * R + g.folga), host=a['host']) is not None
    if ok:
        a['usada'] = True
    return ok


def _vao(g, a):
    rmax = a['folga_r'] - g.folga * 1.2
    for k in range(8):
        r = rmax * 0.9 ** k
        if r < g.r_min:
            return False
        if g.tentar([_circulo(a['pt'], r)]) is not None:
            return True
    return False


def _secundarios(g, cfg, fator=1.0):
    fila = list(g.ancoras)
    random.shuffle(fila)
    for a in fila:
        if g.n_sec >= g.orcamento:
            break
        if a['usada']:
            continue
        t = a['tipo']
        nome = None
        if t == 'ponta':
            nome = _sortear([('orbe', cfg['orbitas'] * 0.35),
                             ('cauda', 0.0 if a.get('semcauda') else cfg['hastes'] * 0.5)],
                            fator)
            feito = {'orbe': _orbe_terminal, 'cauda': _cauda}.get(nome)
        elif t == 'haste_fim':
            nome = _sortear([('orbe', cfg['orbitas'] * 0.35),
                             ('trav', cfg['hastes'] * 0.5),
                             ('cresc', cfg['fases'] * 0.5)], fator)
            feito = {'orbe': _orbe_terminal, 'trav': _travessao_fim,
                     'cresc': _cresc_cap}.get(nome)
        elif t == 'berco':
            nome = _sortear([('orbe', cfg['orbitas'] * 0.75),
                             ('anin', cfg['arcos_internos'] * 0.75),
                             ('axial', cfg['hastes'] * 0.5)], fator)
            feito = {'orbe': _berco_orbe, 'anin': _berco_aninhado,
                     'axial': _berco_axial}.get(nome)
        elif t == 'costas':
            nome = _sortear([('cabo', cfg['hastes'] * 0.45)], fator)
            feito = _cabo if nome else None
        elif t == 'estacao':
            nome = 'est'
            feito = _estacao
        elif t == 'vao':
            nome = _sortear([('orbe', cfg['orbitas'] * 0.7)], fator)
            feito = _vao if nome else None
        else:
            feito = None
        if feito is not None and nome:
            if feito(g, a):
                a['usada'] = True
                g.log.append(t + ':' + nome)


# --------------------------------------------------------------------------
# Pontos com função
# --------------------------------------------------------------------------
def _ponto_em(g, a):
    rpx = max(2.5, g.esp * random.choice((1.15, 1.5, 1.9)))
    r = rpx / PX
    t, pt = a['tipo'], a['pt']
    if t in ('ponta', 'haste_fim'):
        enc = random.random() < 0.5
        c = _mais(pt, a['ang'], r * 0.55 if enc else r + g.folga * 0.55)
        return g.tentar([], [(c, rpx)], perto=(pt, 2 * r + g.folga), host=a['host']) is not None
    if t == 'berco':
        cr = a['cr']
        c = _mais(cr['B2'], cr['theta'], random.uniform(0.3, 0.55) * cr['R2'])
        return g.tentar([], [(c, rpx)]) is not None
    if t == 'intersecao':
        return g.tentar([], [(pt, rpx * 1.15)], perto=(pt, 2 * r + g.folga), host=a['host']) is not None
    if t == 'centro':
        if a.get('r', 0) < 0.33:
            return False
        return g.tentar([], [(pt, rpx * 1.2)], perto=(pt, 2 * r + g.folga), host=a['host']) is not None
    if t in ('satelite', 'vao'):
        return g.tentar([], [(pt, rpx * 1.3)], perto=(pt, 2 * r + g.folga), host=a['host']) is not None
    return False


def _pontuar(g, cfg):
    if random.random() >= cfg['auxiliares']:
        return
    cand = [a for a in g.ancoras if not a['usada'] and a['tipo'] in
            ('ponta', 'haste_fim', 'berco', 'intersecao', 'centro', 'satelite', 'vao')]
    random.shuffle(cand)
    cota = random.choice((1, 1, 2, 2, 3))
    for a in cand:
        if cota <= 0:
            break
        if _ponto_em(g, a):
            a['usada'] = True
            cota -= 1


# --------------------------------------------------------------------------
# Composição e renderização
# --------------------------------------------------------------------------
# (nome, função, chave de config que o favorece, peso-base)
_ESQUELETOS = (
    ('crescente', _est_crescente, 'fases', 1.3),
    ('haste', _est_haste, 'hastes', 1.1),
    ('orbita', _est_orbita, 'orbitas', 0.8),
    ('lentes', _est_lentes, 'arcos_internos', 0.9),
    ('laco', _est_laco, 'caligrafia', 0.6),
    ('parenteses', _est_parenteses, None, 0.8),
    ('trio', _est_trio, 'fases', 1.0),
)


def _compor(cfg, esp):
    g = _Glifo(esp)
    pesos = [base * (0.7 + 0.5 * (cfg[k] if k else 0.6)) for _, _, k, base in _ESQUELETOS]
    nome, est, _, _ = random.choices(_ESQUELETOS, weights=pesos)[0]
    g.nome = nome
    est(g, cfg)                      # 1-2. estrutura principal e âncoras
    _secundarios(g, cfg)             # 3-5. secundários ancorados
    if g.n_sec == 0 and not g.completo:  # nunca entregar só o esqueleto cru
        _secundarios(g, cfg, fator=3.0)
    _pontuar(g, cfg)                 # 6. pontos com função
    if g.n_sec == 0:
        cfg2 = dict(cfg, auxiliares=1.0)
        _pontuar(g, cfg2)
    return g


def _reamostrar(pts, passo):
    """Pontos igualmente espaçados (em px) ao longo da polilinha, extremos preservados."""
    if len(pts) < 3:
        return pts
    acum = [0.0]
    for p, q in zip(pts, pts[1:]):
        acum.append(acum[-1] + _dist(p, q))
    total = acum[-1]
    n = max(2, int(round(total / passo)))
    out, j = [pts[0]], 0
    for k in range(1, n):
        alvo = total * k / n
        while acum[j + 1] < alvo:
            j += 1
        t = (alvo - acum[j]) / max(1e-9, acum[j + 1] - acum[j])
        out.append((pts[j][0] + (pts[j + 1][0] - pts[j][0]) * t,
                    pts[j][1] + (pts[j + 1][1] - pts[j][1]) * t))
    out.append(pts[-1])
    return out


def _tracar(draw, pts, cor, esp, estilo):
    giz, brush = estilo.get("giz", False), estilo.get("brush", False)
    if giz or brush:
        # giz e pincelada ignoram segmentos curtos (< 4 px e < 2 px): em curvas
        # densas os círculos pequenos sumiriam. Reamostra em passos maiores.
        pts = _reamostrar(pts, 7 if brush else 5)
    for p1, p2 in zip(pts, pts[1:]):
        traco_roteador(draw, p1, p2, cor, esp, estilo)
    if esp >= 3 and not giz and not brush:
        r = esp / 2.0  # junta redonda: evita falhas entre segmentos em curvas grossas
        for x, y in pts:
            draw.ellipse((x - r, y - r, x + r, y + r), fill=cor)


def _renderizar(draw, g, cx, cy, cor, esp, estilo):
    xs, ys = [], []
    for comp in g.comps:
        for pts in comp['tracos']:
            for x, y in pts:
                xs.append(x)
                ys.append(y)
    for (x, y), rpx in g.pontos:
        xs += [x - rpx / PX, x + rpx / PX]
        ys += [y - rpx / PX, y + rpx / PX]
    mx, my = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
    meia = max(max(xs) - min(xs), max(ys) - min(ys)) / 2
    esc = max(34.0, min(random.uniform(56, 74) / max(meia, 1e-6), 90.0))

    def tr(p):
        return (cx + (p[0] - mx) * esc, cy + (p[1] - my) * esc)

    for comp in g.comps:
        for pts in comp['tracos']:
            _tracar(draw, [tr(p) for p in pts], cor, esp, estilo)
    for c, rpx in g.pontos:
        x, y = tr(c)
        draw.ellipse((x - rpx, y - rpx, x + rpx, y + rpx), fill=cor)


def aplicar(draw, config, cx, cy, cor, esp, estilo):
    """Gera uma runa lunar proceduralmente (sem glifos predefinidos)."""
    lunar = config.get("lunar", {})
    if not lunar:
        return
    esp = max(1, int(esp))
    cfg = dict(
        caligrafia=lunar.get("caligrafia", 0.82),
        fases=lunar.get("fases", 0.88),
        orbitas=lunar.get("orbitas", lunar.get("eclipse", 0.62)),
        auxiliares=lunar.get("auxiliares", 0.72),
        hastes=lunar.get("hastes", 0.58),
        arcos_internos=lunar.get("arcos_internos", 0.62),
    )
    g = _compor(cfg, esp)
    _renderizar(draw, g, cx, cy, cor, esp, estilo)
