import random
import math
from motor.utilitarios import traco_roteador

def desenhar_termo_algebrico(draw, bbox, cor, esp, estilo, complexidade):
    """Desenha um símbolo alienígena expansivo que imita um termo de uma equação."""
    x1, y1, x2, y2 = bbox
    w, h = x2 - x1, y2 - y1
    
    # Grid local expansivo (3x3) para forçar traços longos e estruturados
    def pt(c, r): 
        return (x1 + c * (w/2), y1 + r * (h/2))
        
    # 1. Estruturas Base de Encapsulamento (As "paredes" da matemática)
    base = random.choice(["raiz", "colchete_esq", "colchete_dir", "haste_absoluta", "triangulo", "ampulheta", "livre"])
    
    if base == "raiz":
        # Um teto e uma descida (imita uma raiz quadrada)
        traco_roteador(draw, pt(0,2), pt(0,0), cor, esp, estilo)
        traco_roteador(draw, pt(0,0), pt(2,0), cor, esp, estilo)
    elif base == "colchete_esq":
        traco_roteador(draw, pt(0,0), pt(0,2), cor, esp, estilo)
        traco_roteador(draw, pt(0,0), pt(1,0), cor, esp, estilo)
        traco_roteador(draw, pt(0,2), pt(1,2), cor, esp, estilo)
    elif base == "colchete_dir":
        traco_roteador(draw, pt(2,0), pt(2,2), cor, esp, estilo)
        traco_roteador(draw, pt(2,0), pt(1,0), cor, esp, estilo)
        traco_roteador(draw, pt(2,2), pt(1,2), cor, esp, estilo)
    elif base == "haste_absoluta":
        c = random.choice([0, 1, 2])
        traco_roteador(draw, pt(c,0), pt(c,2), cor, esp, estilo)
    elif base == "triangulo":
        traco_roteador(draw, pt(0,2), pt(1,0), cor, esp, estilo)
        traco_roteador(draw, pt(1,0), pt(2,2), cor, esp, estilo)
        traco_roteador(draw, pt(0,2), pt(2,2), cor, esp, estilo)
    elif base == "ampulheta":
        traco_roteador(draw, pt(0,0), pt(2,0), cor, esp, estilo)
        traco_roteador(draw, pt(0,2), pt(2,2), cor, esp, estilo)
        traco_roteador(draw, pt(0,0), pt(2,2), cor, esp, estilo)
        traco_roteador(draw, pt(0,2), pt(2,0), cor, esp, estilo)

    # 2. Conexões Geométricas Internas (O conteúdo da equação)
    # Usamos passos inteiros na grid (c=0, 1 ou 2) para garantir traços longos
    num_linhas = int(3 * complexidade) + 1
    for _ in range(num_linhas):
        c1, r1 = random.randint(0,2), random.randint(0,2)
        c2, r2 = random.randint(0,2), random.randint(0,2)
        if (c1, r1) != (c2, r2):
            traco_roteador(draw, pt(c1,r1), pt(c2,r2), cor, esp, estilo)

    # 3. Variáveis de Massa e Órbitas (Círculos e pontos bem definidos)
    num_pontos = int(2 * complexidade) + 1
    for _ in range(num_pontos):
        c, r = random.randint(0,2), random.randint(0,2)
        px, py = pt(c,r)
        
        chance = random.random()
        if chance < 0.4: # Ponto de densidade (Massa)
            r_pt = esp * 1.6
            draw.ellipse([px-r_pt, py-r_pt, px+r_pt, py+r_pt], fill=cor)
        elif chance < 0.7: # Órbita (Variável)
            r_orb = (w/2) * random.uniform(0.3, 0.7)
            draw.ellipse([px-r_orb, py-r_orb, px+r_orb, py+r_orb], outline=cor, width=max(1, int(esp*0.8)))

def aplicar(draw, config, cx, cy, n, step, margem, cor, esp, estilo):
    grav = config.get("gravitacional", {})
    if not grav: return

    esp_int = max(1, int(esp))
    complexidade = grav.get("complexidade", 0.7)
    
    tamanho_total = (n - 1) * step
    
    # Decide o arquétipo da equação
    # 60% Fração Complexa, 40% Equação Linear
    if random.random() < 0.6:
        # ==========================================
        # LAYOUT: FRAÇÃO (A Divisão de Massas)
        # ==========================================
        bar_w = tamanho_total * random.uniform(0.6, 0.95)
        # Desenha a grande barra de fração central
        traco_roteador(draw, (cx - bar_w/2, cy), (cx + bar_w/2, cy), cor, esp_int, estilo)
        
        # Numerador (Termo Superior)
        num_w = bar_w * random.uniform(0.4, 0.8)
        h_term = tamanho_total * random.uniform(0.2, 0.35)
        bbox_num = (cx - num_w/2, cy - h_term - esp_int*3, cx + num_w/2, cy - esp_int*3)
        desenhar_termo_algebrico(draw, bbox_num, cor, esp_int, estilo, complexidade)
        
        # Denominador (Termo Inferior)
        den_w = bar_w * random.uniform(0.4, 0.8)
        bbox_den = (cx - den_w/2, cy + esp_int*3, cx + den_w/2, cy + h_term + esp_int*3)
        desenhar_termo_algebrico(draw, bbox_den, cor, esp_int, estilo, complexidade)
        
        # Coeficiente Lateral (O "Sinal de Igual" ou variável extra à esquerda/direita)
        if random.random() < 0.5:
            lado = random.choice([-1, 1]) # -1 = esquerda, 1 = direita
            side_w = tamanho_total * 0.2
            px_center = cx + lado * (bar_w/2 + side_w/2 + esp_int*4)
            bbox_side = (px_center - side_w/2, cy - side_w/2, px_center + side_w/2, cy + side_w/2)
            desenhar_termo_algebrico(draw, bbox_side, cor, esp_int, estilo, complexidade * 0.5)

    else:
        # ==========================================
        # LAYOUT: EQUAÇÃO LINEAR (Termos Lado a Lado)
        # ==========================================
        num_termos = random.randint(2, 3)
        term_w = tamanho_total * random.uniform(0.25, 0.35)
        gap = term_w * random.uniform(0.3, 0.6)
        
        total_w = num_termos * term_w + (num_termos - 1) * gap
        start_x = cx - total_w / 2
        
        for i in range(num_termos):
            bx = start_x + i * (term_w + gap)
            bbox = (bx, cy - term_w/2, bx + term_w, cy + term_w/2)
            desenhar_termo_algebrico(draw, bbox, cor, esp_int, estilo, complexidade)
            
            # Sinais de Ligação (Operadores entre os termos)
            if i < num_termos - 1:
                op_x = bx + term_w + gap/2
                tipo_op = random.choice(["ponto", "igual", "menos", "vazio"])
                
                if tipo_op == "ponto":
                    r_pt = esp_int * 1.5
                    draw.ellipse([op_x-r_pt, cy-r_pt, op_x+r_pt, cy+r_pt], fill=cor)
                elif tipo_op == "igual":
                    traco_roteador(draw, (op_x - gap/4, cy - esp_int*1.5), (op_x + gap/4, cy - esp_int*1.5), cor, esp_int, estilo)
                    traco_roteador(draw, (op_x - gap/4, cy + esp_int*1.5), (op_x + gap/4, cy + esp_int*1.5), cor, esp_int, estilo)
                elif tipo_op == "menos":
                    traco_roteador(draw, (op_x - gap/3, cy), (op_x + gap/3, cy), cor, esp_int, estilo)