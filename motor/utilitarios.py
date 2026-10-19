import math
import random

def desenhar_pincelada(draw, p1, p2, cor, espessura):
    distancia = math.hypot(p2[0] - p1[0], p2[1] - p1[1])
    passos = int(distancia / 2)
    if passos == 0: return
    for i in range(passos):
        t = i / passos
        x = p1[0] + (p2[0] - p1[0]) * t
        y = p1[1] + (p2[1] - p1[1]) * t
        pressao = math.sin(t * math.pi) 
        raio = (espessura * 0.3) + (espessura * 0.8 * pressao)
        draw.ellipse([x - raio, y - raio, x + raio, y + raio], fill=cor)

def desenhar_giz(draw, p1, p2, cor, espessura):
    distancia = math.hypot(p2[0] - p1[0], p2[1] - p1[1])
    passos = int(distancia / 4)
    if passos == 0: return
    for _ in range(3):
        pts = []
        for i in range(passos + 1):
            t = i / passos if passos > 0 else 0
            x = p1[0] + (p2[0] - p1[0]) * t + random.uniform(-2, 2)
            y = p1[1] + (p2[1] - p1[1]) * t + random.uniform(-2, 2)
            pts.append((x, y))
        draw.line(pts, fill=cor, width=max(1, int(espessura // 3)), joint="curve")

def traco_roteador(draw, p1, p2, cor, espessura, estilo):
    # BLINDAGEM GLOBAL: Garante que a espessura é sempre um inteiro >= 1
    esp_int = max(1, int(espessura)) 
    
    if estilo.get("giz", False): 
        desenhar_giz(draw, p1, p2, cor, esp_int)
    elif estilo.get("brush", False): 
        desenhar_pincelada(draw, p1, p2, cor, esp_int)
    else: 
        draw.line([p1, p2], fill=cor, width=esp_int, joint="curve")

def suavizar_esqueleto(pts, iteracoes=4):
    if len(pts) < 3: return pts
    for _ in range(iteracoes):
        novo_caminho = [pts[0]] 
        for i in range(len(pts) - 1):
            p0, p1 = pts[i], pts[i+1]
            q = (0.75 * p0[0] + 0.25 * p1[0], 0.75 * p0[1] + 0.25 * p1[1])
            r = (0.25 * p0[0] + 0.75 * p1[0], 0.25 * p0[1] + 0.75 * p1[1])
            novo_caminho.extend([q, r])
        novo_caminho.append(pts[-1]) 
        pts = novo_caminho
    return pts

def desenhar_shodo(draw, pts, cor, esp_base):
    if not pts or len(pts) < 2: return
    pts_densos = []
    for i in range(len(pts)-1):
        p1, p2 = pts[i], pts[i+1]
        dist = math.hypot(p2[0]-p1[0], p2[1]-p1[1])
        steps = max(2, int(dist))
        for j in range(steps):
            t = j / steps
            pts_densos.append((p1[0] + (p2[0]-p1[0])*t, p1[1] + (p2[1]-p1[1])*t))
    pts_densos.append(pts[-1])
    n = len(pts_densos)
    for i in range(n):
        t = i / max(1, n - 1)
        pressao = math.sin(t * math.pi) ** 0.7 
        raio = max(0.5, (esp_base / 2.0) * (0.3 + 0.7 * pressao))
        x, y = pts_densos[i]
        draw.ellipse([x - raio, y - raio, x + raio, y + raio], fill=cor)