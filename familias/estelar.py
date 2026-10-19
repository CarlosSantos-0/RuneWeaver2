import random
import math
from motor.utilitarios import traco_roteador

def aplicar(draw, config, cx, cy, n, step, margem, cor, esp, estilo):
    estelar = config.get("estelar", {})
    if not estelar: return

    # 1. Eixo Astral (Inspirado nos mapas criptográficos com linhas e cruzes)
    if random.random() < estelar.get("eixo_astral", 0.0):
        if random.random() < 0.5:
            # Eixo Vertical Principal
            traco_roteador(draw, (cx, cy - 140), (cx, cy + 140), cor, esp, estilo)
            for _ in range(random.randint(1, 4)): # Reduzido para despoluir
                y_cruz = cy + random.randint(-110, 110)
                w_cruz = random.randint(15, 45) # Cruzes mais contidas
                traco_roteador(draw, (cx - w_cruz, y_cruz), (cx + w_cruz, y_cruz), cor, max(1, int(esp*0.8)), estilo)
                # Pequenas luas/sinais nas pontas das cruzes
                if random.random() < estelar.get("orbitas", 0.0):
                    r_orb = random.randint(6, 10)
                    draw.arc([cx - w_cruz - r_orb, y_cruz - r_orb, cx - w_cruz + r_orb, y_cruz + r_orb], 90, 270, fill=cor, width=max(1, int(esp*0.7)))
                    draw.arc([cx + w_cruz - r_orb, y_cruz - r_orb, cx + w_cruz + r_orb, y_cruz + r_orb], 270, 90, fill=cor, width=max(1, int(esp*0.7)))
        else:
            # Eixo Horizontal
            traco_roteador(draw, (cx - 140, cy), (cx + 140, cy), cor, esp, estilo)
            for _ in range(random.randint(1, 4)):
                x_cruz = cx + random.randint(-110, 110)
                h_cruz = random.randint(15, 45)
                traco_roteador(draw, (x_cruz, cy - h_cruz), (x_cruz, cy + h_cruz), cor, max(1, int(esp*0.8)), estilo)

    # 2. Constelações (Mapeamento de Astros Limpo)
    if random.random() < estelar.get("constelacao", 0.0):
        num_estrelas = random.randint(4, 7) # Ligeiramente menos estrelas para evitar saturação
        estrelas_set = set()
        
        # Garante estrelas em posições únicas no grid
        while len(estrelas_set) < num_estrelas:
            ex = margem + random.randint(0, n-1) * step
            ey = margem + random.randint(0, n-1) * step
            estrelas_set.add((ex, ey))
            
        estrelas = list(estrelas_set)
        
        # A MÁGICA DA LIMPEZA: Ordenar as estrelas da esquerda para a direita (por X)
        # Isto impede que a linha da constelação volte para trás e se cruze a si mesma!
        estrelas.sort(key=lambda p: (p[0], p[1]))

        # Conecta as estrelas na ordem (Caminho principal)
        for i in range(num_estrelas - 1):
            traco_roteador(draw, estrelas[i], estrelas[i+1], cor, max(1, int(esp * 0.6)), estilo)
            
        # Ligações secundárias controladas (apenas ramifica para a vizinha seguinte)
        for i in range(num_estrelas - 2):
            if random.random() < 0.3:
                traco_roteador(draw, estrelas[i], estrelas[i+2], cor, max(1, int(esp * 0.4)), estilo)

        # 3. Desenho dos Astros e Órbitas
        if random.random() < estelar.get("estrelas", 0.0):
            for i, (ex, ey) in enumerate(estrelas):
                # Mecânica de "Captura-Astral": O primeiro astro pode ser massivo
                if i == 0 and random.random() < 0.4:
                    raio = esp * 2.5
                    if random.random() < estelar.get("orbitas", 0.0):
                        draw.ellipse([ex - raio - 10, ey - raio - 10, ex + raio + 10, ey + raio + 10], outline=cor, width=max(1, int(esp*0.6)))
                else:
                    raio = esp * 1.2
                
                # Desenha o astro sólido
                draw.ellipse([ex - raio, ey - raio, ex + raio, ey + raio], fill=cor)

                # Desenha pequenos arcos / frequências ao redor das estrelas comuns
                if random.random() < estelar.get("orbitas", 0.0) and i != 0:
                    r_orb = raio + random.randint(8, 20)
                    ang_start = random.randint(0, 360)
                    draw.arc([ex - r_orb, ey - r_orb, ex + r_orb, ey + r_orb], ang_start, ang_start + random.randint(90, 180), fill=cor, width=max(1, int(esp*0.7)))