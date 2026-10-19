import random
import math
from motor.utilitarios import suavizar_esqueleto, desenhar_shodo

def aplicar(draw, config, cx, cy, n, step, margem, cor, esp, estilo):
    aer = config.get("aeral", {})
    if not aer: return

    if random.random() < aer.get("fluxo", 0):
        tipo_estrutura = random.choice(["teto", "serpente", "berco", "ascensao", "laco"])
        pts_esqueleto = []
        if tipo_estrutura == "teto":
            pts_esqueleto.append((margem + random.choice([0, 1])*step, margem + random.randint(0, 1)*step))
            pts_esqueleto.append((margem + random.choice([n-2, n-1])*step, pts_esqueleto[-1][1]))
            pts_esqueleto.append((margem + random.randint(1, n-2)*step, margem + random.randint(2, n-2)*step))
            if random.random() < 0.5: pts_esqueleto.append((margem + random.randint(0, n-1)*step, margem + (n-1)*step))
        elif tipo_estrutura == "serpente":
            pts_esqueleto.append((margem + random.randint(1, n-2)*step, margem))
            pts_esqueleto.append((margem + random.randint(0, 1)*step, margem + int(n/3)*step))
            pts_esqueleto.append((margem + random.randint(n-2, n-1)*step, margem + int(2*n/3)*step))
            pts_esqueleto.append((margem + random.randint(1, n-2)*step, margem + (n-1)*step))
        elif tipo_estrutura == "berco":
            pts_esqueleto.append((margem, margem + random.randint(1, n-2)*step))
            pts_esqueleto.append((margem + int(n/2)*step, margem + (n-1)*step))
            pts_esqueleto.append((margem + (n-1)*step, margem + random.randint(1, n-2)*step))
            pts_esqueleto.append((margem + random.randint(1, n-2)*step, margem))
        elif tipo_estrutura == "ascensao":
            pts_esqueleto.append((margem + random.randint(0, 1)*step, margem + (n-1)*step))
            pts_esqueleto.append((margem + random.randint(n-2, n-1)*step, margem + random.randint(0, 1)*step))
            pts_esqueleto.append((margem + random.randint(0, int(n/2))*step, margem + int(n/2)*step))
            if random.random() < 0.5: pts_esqueleto.append((margem + random.randint(n-2, n-1)*step, margem + (n-1)*step))
        elif tipo_estrutura == "laco":
            pts_esqueleto.append((margem + (n-1)*step, margem))
            pts_esqueleto.append((margem, margem + (n-1)*step))
            pts_esqueleto.append((margem + (n-1)*step, margem + (n-1)*step))
            pts_esqueleto.append((margem, margem))
        
        caminho_fluido = suavizar_esqueleto(pts_esqueleto, iteracoes=4)
        desenhar_shodo(draw, caminho_fluido, cor, esp)
        
        if random.random() < 0.3:
            desenhar_shodo(draw, suavizar_esqueleto([(margem + random.randint(0, 1)*step, margem + random.randint(1, n-2)*step), (margem + random.randint(n-2, n-1)*step, margem + random.randint(1, n-2)*step)], iteracoes=4), cor, esp)
            
    if random.random() < aer.get("espiral", 0):
        c_esp_x, c_esp_y = margem + random.randint(0, n-1)*step, margem + random.randint(1, n-1)*step
        raio_max, voltas, direcao = random.randint(20, 35), random.uniform(1.2, 1.8), random.choice([-1, 1])
        passos_espiral = int(raio_max * 1.5)
        pts_espiral = [(c_esp_x + (raio_max * (1 - (i / max(1, passos_espiral - 1)))) * math.cos((i / max(1, passos_espiral - 1)) * voltas * math.pi * 2 * direcao), c_esp_y + (raio_max * (1 - (i / max(1, passos_espiral - 1)))) * math.sin((i / max(1, passos_espiral - 1)) * voltas * math.pi * 2 * direcao)) for i in range(passos_espiral)]
        desenhar_shodo(draw, pts_espiral, cor, esp)
        
    if random.random() < aer.get("lamina", 0):
        p_start, p_end, c_puxao = (margem + random.randint(0, 1)*step, margem + random.randint(1, n-2)*step), (margem + random.randint(n-2, n-1)*step, margem + random.randint(1, n-2)*step), (cx + random.randint(-40, 40), cy - random.randint(60, 120))
        desenhar_shodo(draw, suavizar_esqueleto([p_start, c_puxao, p_end], iteracoes=5), cor, esp * 1.5)
        
    if random.random() < aer.get("pontilhados", 0):
        px, py, ang_mov, raio_p = margem + random.randint(0, n-1)*step, margem + random.randint(0, n-1)*step, random.uniform(0, math.pi * 2), esp * 0.8
        for i in range(3, 5):
            draw.ellipse([px - raio_p, py - raio_p, px + raio_p, py + raio_p], fill=cor)
            px, py, ang_mov, raio_p = px + math.cos(ang_mov) * (15 + i*3), py + math.sin(ang_mov) * (15 + i*3), ang_mov + 0.2 * random.choice([-1, 1]), raio_p * 0.7