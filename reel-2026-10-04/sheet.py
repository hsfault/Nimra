import sys, glob
from PIL import Image
files = sys.argv[2:]; out = sys.argv[1]
ims = [Image.open(f).convert('RGB').resize((432, 768), Image.LANCZOS) for f in files]
s = Image.new('RGB', (432 * len(ims) + 8 * (len(ims) - 1), 768), (40, 40, 40))
for i, im in enumerate(ims): s.paste(im, (i * 440, 0))
s.save(out, quality=88)
