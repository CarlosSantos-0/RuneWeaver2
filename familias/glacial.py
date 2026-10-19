import random
from motor.utilitarios import traco_roteador

def aplicar(draw, config, n, step, margem, cor, esp, estilo):
    glacial = config.get("glacial", {})
    if not glacial: return

    mastro_xs = []
    y_s, y_e = random.randint(0, 1), random.randint(n-2, n-1)
    
    if random.random() < glacial.get("mastros_duplos", 0) and n >= 4:
        mx1 = random.randint(1, n-3)
        mx2 = mx1 + random.randint(1, 2)
        traco_roteador(draw, (margem + mx1*step, margem + y_s*step), (margem + mx1*step, margem + y_e*step), cor, esp, estilo)
        traco_roteador(draw, (margem + mx2*step, margem + y_s*step), (margem + mx2*step, margem + y_e*step), cor, esp, estilo)
        y_p1 = random.randint(y_s, y_e-1)
        traco_roteador(draw, (margem + mx1*step, margem + y_p1*step), (margem + mx2*step, margem + (y_p1+random.choice([-1,0,1]))*step), cor, esp, estilo)
        mastro_xs = [mx1, mx2]
    elif random.random() < glacial.get("mastro", 0):
        mx = random.randint(1, n-2) if n > 3 else random.randint(0, n-1)
        traco_roteador(draw, (margem + mx*step, margem + y_s*step), (margem + mx*step, margem + y_e*step), cor, esp, estilo)
        mastro_xs = [mx]
        
    if random.random() < glacial.get("ramos", 0):
        for mx in mastro_xs:
            for y in range(y_s, y_e + 1):
                if random.random() < 0.6:
                    dx, dy_r = random.choice([-1, 1]), random.choice([-1, 1])
                    dist = 2 if random.random() < glacial.get("ramos_longos", 0) else 1
                    if 0 <= mx + dx*dist < n and 0 <= y + dy_r*dist < n:
                        p1 = (margem + mx*step, margem + y*step)
                        p2 = (margem + (mx+dx*dist)*step, margem + (y+dy_r*dist)*step)
                        traco_roteador(draw, p1, p2, cor, esp, estilo)
                        if random.random() < glacial.get("duplos", 0) and 0 <= mx - dx*dist < n:
                            traco_roteador(draw, p1, (margem + (mx-dx*dist)*step, margem + (y+dy_r*dist)*step), cor, esp, estilo)

    if random.random() < glacial.get("losangos", 0) and mastro_xs:
        mx = random.choice(mastro_xs)
        y_los = random.randint(y_s, max(y_s, y_e - 2))
        if 0 <= mx - 1 and mx + 1 < n:
            for pA, pB in [((margem + mx*step, margem + y_los*step), (margem + (mx+1)*step, margem + (y_los+1)*step)), ((margem + (mx+1)*step, margem + (y_los+1)*step), (margem + mx*step, margem + (y_los+2)*step)), ((margem + mx*step, margem + (y_los+2)*step), (margem + (mx-1)*step, margem + (y_los+1)*step)), ((margem + (mx-1)*step, margem + (y_los+1)*step), (margem + mx*step, margem + y_los*step))]: 
                traco_roteador(draw, pA, pB, cor, esp, estilo)
    
    if random.random() < glacial.get("cristais", 0):
        for _ in range(random.randint(1, 3)):
            c_p = (margem + random.randint(0, n-1)*step, margem + random.randint(0, n-1)*step)
            draw.polygon([(c_p[0], c_p[1]-esp*1.5), (c_p[0]+esp*1.5, c_p[1]), (c_p[0], c_p[1]+esp*1.5), (c_p[0]-esp*1.5, c_p[1])], fill=cor)