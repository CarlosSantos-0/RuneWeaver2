import random
from motor.utilitarios import traco_roteador

def aplicar(draw, config, cx, cy, cor, esp, estilo):
    met = config.get("metalica", {})
    if not met: return

    if random.random() < met.get("triangulo", 0):
        raio_t, dy = random.randint(50, 90), random.randint(-20, 20)
        p_bottom, p_top_l = (cx, cy + dy + raio_t), (cx - raio_t * 0.866, cy + dy - raio_t * 0.5)
        draw.polygon([p_top_l, (cx + raio_t * 0.866, cy + dy - raio_t * 0.5), p_bottom], outline=cor, width=esp)
        
        if random.random() < met.get("enclausuramento", 0): 
            draw.ellipse([cx - raio_t, cy+dy - raio_t, cx + raio_t, cy+dy + raio_t], outline=cor, width=esp)
            
        if random.random() < met.get("secantes", 0):
            for i in range(random.randint(1, 2)): 
                traco_roteador(draw, (cx - (raio_t * 0.866) * (1 - (i + 1)/3), (cy+dy - raio_t * 0.5) + (raio_t * 1.5) * ((i + 1) / 3)), (cx + (raio_t * 0.866) * (1 - (i + 1)/3), (cy+dy - raio_t * 0.5) + (raio_t * 1.5) * ((i + 1) / 3)), cor, esp, estilo)
                
        if random.random() < met.get("nucleo", 0): 
            draw.polygon([(cx, cy+dy - esp*1.5), (cx + esp*1.5, cy+dy), (cx, cy+dy + esp*1.5), (cx - esp*1.5, cy+dy)], fill=cor)
            
        if random.random() < met.get("ancoragem", 0):
            if random.random() < 0.5: 
                traco_roteador(draw, p_bottom, (p_bottom[0], p_bottom[1] + 60), cor, esp, estilo)
            else: 
                traco_roteador(draw, (p_top_l[0], cy+dy - raio_t - 20), (p_top_l[0], cy+dy + raio_t + 20), cor, esp, estilo)