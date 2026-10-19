import random
import math
from motor.utilitarios import traco_roteador

def aplicar(draw, config, cx, cy, n, step, margem, cor, esp, estilo):
    crist = config.get("cristalina", {})
    if not crist: return

    raio_cristal = random.randint(100, 150)
    
    if random.random() < crist.get("anel_base", 0):
        bbox = [cx - raio_cristal, cy - raio_cristal, cx + raio_cristal, cy + raio_cristal]
        draw.ellipse(bbox, outline=cor, width=esp)
        if random.random() < 0.4:
            r_gap = raio_cristal - (esp * 3)
            draw.ellipse([cx - r_gap, cy - r_gap, cx + r_gap, cy + r_gap], outline=cor, width=max(1, esp - 2))

    pontas_cristal = random.choice([3, 4, 6, 8])
    angulo_offset = random.choice([0, math.pi/pontas_cristal, math.pi/2])
    vertices_cristal = [(cx + raio_cristal * math.cos(angulo_offset + i * (2 * math.pi / pontas_cristal)), cy + raio_cristal * math.sin(angulo_offset + i * (2 * math.pi / pontas_cristal))) for i in range(pontas_cristal)]
        
    if random.random() < crist.get("poligono", 0):
        for i in range(pontas_cristal):
            traco_roteador(draw, vertices_cristal[i], vertices_cristal[(i+1)%pontas_cristal], cor, esp, estilo)
            if pontas_cristal >= 5 and random.random() < 0.5:
                traco_roteador(draw, vertices_cristal[i], vertices_cristal[(i+2)%pontas_cristal], cor, max(1, esp-1), estilo)

    if random.random() < crist.get("diagonais", 0):
        for i in range(pontas_cristal // 2):
            traco_roteador(draw, vertices_cristal[i], vertices_cristal[(i + (pontas_cristal // 2)) % pontas_cristal], cor, max(1, esp-1), estilo)
        if random.random() < 0.5: traco_roteador(draw, (cx, cy - raio_cristal), (cx, cy + raio_cristal), cor, esp, estilo)
        if random.random() < 0.5: traco_roteador(draw, (cx - raio_cristal, cy), (cx + raio_cristal, cy), cor, esp, estilo)

    if random.random() < crist.get("caleidoscopio", 0):
        for camada in range(random.randint(1, 2)):
            raio_interno = raio_cristal * (0.6 - (camada * 0.25))
            rot_interna = angulo_offset + (math.pi / pontas_cristal)
            vert_internos = [(cx + raio_interno * math.cos(rot_interna + i * (2 * math.pi / pontas_cristal)), cy + raio_interno * math.sin(rot_interna + i * (2 * math.pi / pontas_cristal))) for i in range(pontas_cristal)]
            for i in range(pontas_cristal): traco_roteador(draw, vert_internos[i], vert_internos[(i+1)%pontas_cristal], cor, max(1, esp-2), estilo)
            if camada == 0 and random.random() < 0.6:
                draw.ellipse([cx - (raio_interno * 0.5), cy - (raio_interno * 0.5), cx + (raio_interno * 0.5), cy + (raio_interno * 0.5)], outline=cor, width=esp)

    if random.random() < crist.get("ressonancia", 0):
        r_no = esp * 1.5
        if random.random() < 0.7: draw.ellipse([cx - r_no, cy - r_no, cx + r_no, cy + r_no], fill=cor)
        for vx, vy in vertices_cristal: draw.ellipse([vx - r_no, vy - r_no, vx + r_no, vy + r_no], fill=cor)