import random
from motor.utilitarios import traco_roteador

def gerar_bloco(draw, bbox, cor, esp, estilo, telurica_cfg):
    """Gera um único caractere denso e estruturado dentro de uma bounding box."""
    x1, y1, x2, y2 = bbox
    w, h = x2 - x1, y2 - y1
    
    # Micro-grid interno para dar o aspeto "alfabético" (3x3 ou 4x4)
    cols = random.randint(3, 4)
    rows = random.randint(3, 5)
    
    step_x = w / max(1, cols - 1)
    step_y = h / max(1, rows - 1)
    
    def px(c): return x1 + c * step_x
    def py(r): return y1 + r * step_y
    
    densidade = telurica_cfg.get("ortogonal", 0.6)
    
    # 1. Âncora Estrutural (Haste Mestra ou Teto)
    if random.random() < 0.5:
        traco_roteador(draw, (px(0), py(0)), (px(cols-1), py(0)), cor, esp * 1.5, estilo) # Teto pesado
    else:
        cm = cols // 2
        traco_roteador(draw, (px(cm), py(0)), (px(cm), py(rows-1)), cor, esp * 1.5, estilo) # Haste central grossa

    # 2. Preenchimento de Linhas Ortogonais (Labirinto / Alfabeto)
    for r in range(rows):
        for c in range(cols):
            if c < cols - 1 and random.random() < densidade:
                traco_roteador(draw, (px(c), py(r)), (px(c+1), py(r)), cor, esp, estilo)
            if r < rows - 1 and random.random() < densidade:
                traco_roteador(draw, (px(c), py(r)), (px(c), py(r+1)), cor, esp, estilo)
                
    # 3. Diagonais Ocasionais (Quebras na pedra)
    if random.random() < telurica_cfg.get("diagonais", 0.3):
        for _ in range(random.randint(1, 3)):
            c, r = random.randint(0, cols-2), random.randint(0, rows-2)
            if random.random() < 0.5:
                traco_roteador(draw, (px(c), py(r)), (px(c+1), py(r+1)), cor, esp, estilo)
            else:
                traco_roteador(draw, (px(c+1), py(r)), (px(c), py(r+1)), cor, esp, estilo)
                
    # 4. Blocos Sólidos Maciços (O peso geológico)
    if random.random() < telurica_cfg.get("blocos", 0.4):
        for _ in range(random.randint(1, 2)):
            c, r = random.randint(0, cols-2), random.randint(0, rows-2)
            draw.rectangle([px(c), py(r), px(c+1), py(r+1)], fill=cor)

def aplicar(draw, config, cx, cy, n, step, margem, cor, esp, estilo):
    telurica = config.get("telurica", {})
    if not telurica: return
    
    # A área máxima do Grid disponível para esculpir
    tamanho_total = (n - 1) * step
    x_min = cx - tamanho_total / 2
    y_min = cy - tamanho_total / 2
    x_max = cx + tamanho_total / 2
    y_max = cy + tamanho_total / 2
    
    # 50% de chance de Empilhamento (Dois símbolos empilhados)
    if random.random() < 0.5:
        gap = 15 # Espaço entre o símbolo superior e inferior
        meio_y = cy
        
        bbox_top = (x_min + 15, y_min, x_max - 15, meio_y - gap)
        bbox_bot = (x_min + 15, meio_y + gap, x_max - 15, y_max)
        
        gerar_bloco(draw, bbox_top, cor, esp, estilo, telurica)
        gerar_bloco(draw, bbox_bot, cor, esp, estilo, telurica)
    else:
        # Símbolo Monolítico Único (Maior)
        bbox_full = (x_min + 15, y_min + 15, x_max - 15, y_max - 15)
        gerar_bloco(draw, bbox_full, cor, esp, estilo, telurica)