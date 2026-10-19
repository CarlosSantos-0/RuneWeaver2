import random
from motor.utilitarios import traco_roteador

def aplicar_comuns(draw, config, cx, cy, cor, esp, estilo, usa_curvas):
    comuns = config.get("modulos", {})
    if not comuns: return
    
    if random.random() < comuns.get("haste", 0):
        traco_roteador(draw, (cx + random.randint(-20, 20), cy - random.randint(60, 150)), (cx + random.randint(-20, 20), cy + random.randint(60, 150)), cor, esp, estilo)
        
    if random.random() < comuns.get("anel", 0):
        rx, ry, dy = random.randint(40, 100), random.randint(40, 100), random.randint(-40, 40)
        if usa_curvas: draw.ellipse([cx - rx, cy + dy - ry, cx + rx, cy + dy + ry], outline=cor, width=esp)
        else: draw.polygon([(cx, cy+dy-ry), (cx+rx, cy+dy), (cx, cy+dy+ry), (cx-rx, cy+dy)], outline=cor, width=esp)
        
    if random.random() < comuns.get("arco", 0):
        raio, dy = random.randint(40, 120), random.randint(-80, 80)
        if usa_curvas: draw.arc([cx - raio, cy + dy - raio, cx + raio, cy + dy + raio], start=random.choice([0, 180]), end=random.choice([0, 180])+180, fill=cor, width=esp)
        else:
            dir_arco = random.choice([-1, 1])
            traco_roteador(draw, (cx - raio, cy + dy - raio*dir_arco), (cx, cy + dy + raio*dir_arco), cor, esp, estilo)
            traco_roteador(draw, (cx, cy + dy + raio*dir_arco), (cx + raio, cy + dy - raio*dir_arco), cor, esp, estilo)
            
    if random.random() < comuns.get("ramos", 0):
        for _ in range(random.randint(1, 3)):
            r_cx, r_cy = cx + random.randint(-30, 30), cy + random.randint(-60, 60)
            r_ex, r_ey = r_cx + random.randint(40, 90) * random.choice([-1, 1]), r_cy + random.randint(-60, 60)
            traco_roteador(draw, (r_cx, r_cy), (r_ex, r_ey), cor, esp, estilo)

    for _ in range(random.randint(0, comuns.get("max_flutuantes", 0))):
        fx, fy = cx + random.randint(30, 150) * random.choice([-1, 1]), cy + random.randint(-150, 150)
        if random.random() < 0.5 and usa_curvas: draw.ellipse([fx - esp*1.5, fy - esp*1.5, fx + esp*1.5, fy + esp*1.5], fill=cor)
        else: traco_roteador(draw, (fx, fy), (fx + random.randint(10, 30), fy + random.randint(-10, 10)), cor, esp, estilo)


def aplicar_grid_livre(draw, config, n, passos, step, margem, cor, esp, estilo):
    px, py = random.randint(0, n-1), random.randint(0, n-1)
    pontos_caminho = [(margem + px * step, margem + py * step)]
    for _ in range(passos):
        direcoes = [(0,1), (0,-1), (1,0), (-1,0)]
        if not config.get("estilo", {}).get("letra_de_mao", False): 
            direcoes += [(1,1), (-1,-1), (1,-1), (-1,1)]
        dx, dy = random.choice(direcoes)
        if 0 <= px + dx < n and 0 <= py + dy < n:
            px, py = px + dx, py + dy
            pontos_caminho.append((margem + px * step, margem + py * step))
            
    if config.get("estilo", {}).get("letra_de_mao", False): 
        draw.line(pontos_caminho, fill=cor, width=esp, joint="curve")
    else:
        for i in range(len(pontos_caminho)-1): 
            traco_roteador(draw, pontos_caminho[i], pontos_caminho[i+1], cor, esp, estilo)