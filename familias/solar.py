import random
import math
from motor.utilitarios import traco_roteador

def aplicar(draw, config, cx, cy, n, step, margem, cor, esp, estilo):
    solar = config.get("solar", {})
    if not solar: return

    esp_int = max(1, int(esp))
    
    # 1. Eixos Diretores (A Ordem Solar baseada no Grid)
    eixos = []
    # Cria 1 a 2 linhas retas estruturais (Horizontais ou Verticais)
    if random.random() < solar.get("irradiacao", 0.0) or True: 
        num_eixos = random.randint(1, 2)
        for _ in range(num_eixos):
            is_horiz = random.choice([True, False])
            if is_horiz:
                y_g = random.randint(1, n-2) if n > 2 else 1
                x1_g = random.randint(0, 1)
                x2_g = random.randint(n-2, n-1)
                eixos.append( ("h", y_g, x1_g, x2_g) )
                traco_roteador(draw, 
                               (margem + x1_g*step, margem + y_g*step), 
                               (margem + x2_g*step, margem + y_g*step), 
                               cor, esp_int, estilo)
            else:
                x_g = random.randint(1, n-2) if n > 2 else 1
                y1_g = random.randint(0, 1)
                y2_g = random.randint(n-2, n-1)
                eixos.append( ("v", x_g, y1_g, y2_g) )
                traco_roteador(draw, 
                               (margem + x_g*step, margem + y1_g*step), 
                               (margem + x_g*step, margem + y2_g*step), 
                               cor, esp_int, estilo)

    # 2. Foco e Eclipse (Posicionados exatamente sobre um dos eixos)
    focos_coords = []
    if random.random() < solar.get("foco", 0.0) and eixos:
        eixo = random.choice(eixos)
        # Escolhe um nó do grid que esteja no meio da linha
        if eixo[0] == "h":
            gx = random.randint(eixo[2]+1, eixo[3]-1) if eixo[3]-1 >= eixo[2]+1 else eixo[2]
            gy = eixo[1]
        else:
            gx = eixo[1]
            gy = random.randint(eixo[2]+1, eixo[3]-1) if eixo[3]-1 >= eixo[2]+1 else eixo[2]
            
        fx, fy = margem + gx*step, margem + gy*step
        focos_coords.append((gx, gy)) # Regista a posição no grid
        
        r_foco = int(step * random.uniform(0.3, 0.5))
        if random.random() < solar.get("eclipse", 0.0):
            # Eclipse: Anel denso e bloqueador
            draw.ellipse([fx - r_foco, fy - r_foco, fx + r_foco, fy + r_foco], outline=cor, width=esp_int * 3)
        else:
            # Concentração: Ponto luminoso e anel fino
            draw.ellipse([fx - r_foco*0.25, fy - r_foco*0.25, fx + r_foco*0.25, fy + r_foco*0.25], fill=cor)
            draw.ellipse([fx - r_foco, fy - r_foco, fx + r_foco, fy + r_foco], outline=cor, width=esp_int)

    # 3. Coroa Solar (Semicírculos alinhados com o eixo da linha)
    if random.random() < solar.get("coroa", 0.0) and eixos:
        for _ in range(random.randint(1, 3)):
            eixo = random.choice(eixos)
            if eixo[0] == "h":
                gx = random.randint(eixo[2], eixo[3])
                gy = eixo[1]
                ang_dir = random.choice([0, 180]) # Semicírculo virado para a direita ou esquerda
            else:
                gx = eixo[1]
                gy = random.randint(eixo[2], eixo[3])
                ang_dir = random.choice([90, 270]) # Semicírculo virado para baixo ou cima
                
            px, py = margem + gx*step, margem + gy*step
            r_arco = int(step * random.uniform(0.3, 0.6))
            
            # Se o arco cair exatamente em cima do "Sol", ele transforma-se num halo maior por fora
            if (gx, gy) in focos_coords:
                r_arco = int(step * random.uniform(0.6, 0.8))
            
            draw.arc([px - r_arco, py - r_arco, px + r_arco, py + r_arco], ang_dir - 90, ang_dir + 90, fill=cor, width=esp_int)
            
            # Detalhe de Astrolábio: Pequeno traço cruzando as pontas do arco
            if random.random() < 0.5:
                c1x = px + math.cos(math.radians(ang_dir)) * (r_arco - step*0.2)
                c1y = py + math.sin(math.radians(ang_dir)) * (r_arco - step*0.2)
                c2x = px + math.cos(math.radians(ang_dir)) * (r_arco + step*0.2)
                c2y = py + math.sin(math.radians(ang_dir)) * (r_arco + step*0.2)
                traco_roteador(draw, (c1x, c1y), (c2x, c2y), cor, esp_int, estilo)

    # 4. Terminações (Pontos nas extremidades dos Eixos de Irradiação)
    if random.random() < solar.get("irradiacao", 0.0):
        for eixo in eixos:
            if random.random() < 0.7:
                if eixo[0] == "h":
                    # Ponto numa das extremidades horizontais
                    px = margem + random.choice([eixo[2], eixo[3]]) * step
                    py = margem + eixo[1] * step
                else:
                    # Ponto numa das extremidades verticais
                    px = margem + eixo[1] * step
                    py = margem + random.choice([eixo[2], eixo[3]]) * step
                    
                r_ponto = esp_int * 1.5
                draw.ellipse([px - r_ponto, py - r_ponto, px + r_ponto, py + r_ponto], fill=cor)