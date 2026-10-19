import random
from motor.utilitarios import traco_roteador

def aplicar(draw, config, cx, cy, cor, esp, estilo):
    sep = config.get("sepulcral", {})
    if not sep: return

    if random.random() < sep.get("espinhal", 0):
        altura = random.randint(100, 160)
        traco_roteador(draw, (cx, cy - altura), (cx, cy + altura), cor, esp, estilo)
        for i in range(random.randint(2, 4)):
            y_vert = (cy - altura + 40) + (i * ((altura * 2 - 80) // 3))
            traco_roteador(draw, (cx - random.randint(20, 60), y_vert), (cx + random.randint(20, 60), y_vert), cor, max(2, esp-2), estilo)
        if random.random() < sep.get("cruz", 0):
            traco_roteador(draw, (cx - esp*2.5, cy - altura + 10), (cx + esp*2.5, cy - altura + 10), cor, esp, estilo)
            traco_roteador(draw, (cx - esp*2.5, cy + altura - 10), (cx + esp*2.5, cy + altura - 10), cor, esp, estilo)
            
    if random.random() < sep.get("eco", 0):
        raio_b, dy, ang = random.randint(40, 80), random.randint(-40, 40), random.choice([0, 90, 180, 270])
        for i in range(random.randint(2, 3)): 
            draw.arc([cx - (raio_b + i*25), cy + dy - (raio_b + i*25), cx + (raio_b + i*25), cy + dy + (raio_b + i*25)], start=ang, end=ang+180, fill=cor, width=max(1, esp - i*2))