import random
import math
from motor.utilitarios import traco_roteador

def aplicar(draw, config, cx, cy, cor, esp, estilo):
    sang = config.get("sanguinea", {})
    if not sang: return

    if random.random() < sang.get("estrela", 0):
        pontas = random.choice([3, 4, 5, 6])
        raio_est, dy_est = random.randint(60, 100), random.randint(-40, 20)
        vertices = [(cx + raio_est * math.cos(math.radians((i * 360 / pontas) - 90)), (cy + dy_est) + raio_est * math.sin(math.radians((i * 360 / pontas) - 90))) for i in range(pontas)]
        salto = 2 if pontas > 4 else 1 
        for i in range(pontas): 
            traco_roteador(draw, vertices[i], vertices[(i + salto) % pontas], cor, esp, estilo)
            
    if random.random() < sang.get("olho", 0):
        l_olho, h_olho, dy_olho = random.randint(20, 40), random.randint(10, 20), random.randint(-40, 10)
        draw.arc([cx - l_olho, cy + dy_olho - h_olho*2, cx + l_olho, cy + dy_olho], start=0, end=180, fill=cor, width=esp)
        draw.arc([cx - l_olho, cy + dy_olho, cx + l_olho, cy + dy_olho + h_olho*2], start=180, end=360, fill=cor, width=esp)
        draw.ellipse([cx-3, cy+dy_olho-3, cx+3, cy+dy_olho+3], fill=cor) 
        
    if random.random() < sang.get("punhal", 0):
        comp_punhal, y_top, y_bot = random.randint(80, 140), cy - random.randint(20, 60), cy + random.randint(80, 140)
        pts_punhal = []
        for i in range(11): pts_punhal.append((cx - ((esp * 1.5) * (1 - (i/10)**2)), y_top + (y_bot - y_top) * (i/10)))
        for i in range(10, -1, -1): pts_punhal.append((cx + ((esp * 1.5) * (1 - (i/10)**2)), y_top + (y_bot - y_top) * (i/10)))
        draw.polygon(pts_punhal, fill=cor)
        traco_roteador(draw, (cx, cy - 80), (cx, y_top), cor, esp, estilo)
        
    if random.random() < sang.get("espinhos", 0):
        for _ in range(random.randint(2, 3)):
            alt_nasc, dir_esp = cy + random.randint(-40, 40), random.choice([-1, 1])
            p_meio1, p_meio2 = (cx + 30 * dir_esp, alt_nasc - 20), (cx + 50 * dir_esp, alt_nasc + 15)
            draw.line([(cx, alt_nasc), p_meio1, p_meio2, (cx + 80 * dir_esp, alt_nasc - 30)], fill=cor, width=max(1, esp-1), joint="curve")
            draw.line([p_meio2, (p_meio2[0] + 15 * dir_esp, p_meio2[1] + 25)], fill=cor, width=max(1, esp-2), joint="curve")