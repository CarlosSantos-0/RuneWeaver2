from PIL import Image
import math

S = 16
img = Image.new("RGBA", (S, S))
c = (S - 1) / 2
for y in range(S):
    for x in range(S):
        d = math.hypot(x - c, y - c) / c
        a = max(0.0, 1.0 - d) ** 1.6
        img.putpixel((x, y), (255, 255, 255, int(a * 255)))
img.save("spell_spark.png")