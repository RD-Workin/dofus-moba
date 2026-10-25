"""Turns the published web version (output of package_web.py) into an app installable from the iPhone home screen
(PWA): icon, full screen, offline cache. Usage: python3 package_mobile.py <pub> <out> [icon.png]
<out> is what gets pushed to the GitHub Pages repo (its root)."""
import sys, os, shutil, json, hashlib
from PIL import Image

src, dst = sys.argv[1], sys.argv[2]
icon_src = sys.argv[3] if len(sys.argv) > 3 else os.path.join(os.path.dirname(__file__), 'icone.png')
NAME, SHORT, BG = 'Dofus MOBA', 'Dofus MOBA', '#1d1710'

os.makedirs(dst, exist_ok=True)
for f in os.listdir(dst):
    if f not in ('.git', 'README.md', '.nojekyll'):
        p = os.path.join(dst, f)
        shutil.rmtree(p) if os.path.isdir(p) else os.remove(p)
files = [f for f in sorted(os.listdir(src)) if f != 'index.html']
for f in files:
    shutil.copy(os.path.join(src, f), dst)

# Icons: full-bleed square (iOS rounds the corners itself).
os.makedirs(f'{dst}/icons')
icon = Image.open(icon_src).convert('RGBA')
for size in (180, 192, 512):
    im = Image.new('RGB', (size, size), BG)
    im.paste(icon.resize((size, size), Image.LANCZOS), (0, 0), icon.resize((size, size), Image.LANCZOS))
    im.save(f'{dst}/icons/icon-{size}.png')
icons = ['icons/icon-180.png', 'icons/icon-192.png', 'icons/icon-512.png']

json.dump({
    'name': NAME, 'short_name': SHORT, 'lang': 'fr', 'start_url': './', 'scope': './', 'id': './',
    'display': 'fullscreen', 'orientation': 'landscape', 'background_color': BG, 'theme_color': BG,
    'icons': [{'src': 'icons/icon-192.png', 'sizes': '192x192', 'type': 'image/png'},
              {'src': 'icons/icon-512.png', 'sizes': '512x512', 'type': 'image/png', 'purpose': 'any maskable'}],
}, open(f'{dst}/manifest.webmanifest', 'w', encoding='utf8'), ensure_ascii=False, indent=1)

# Cache name changes with the content, so a new version replaces the old one on next launch.
h = hashlib.sha256()
for f in files:
    h.update(open(os.path.join(src, f), 'rb').read())
page = open(f'{src}/index.html', encoding='utf8').read()
h.update(page.encode())
version = h.hexdigest()[:10]
assets = ['./', 'manifest.webmanifest'] + files + icons
sw = open(os.path.join(os.path.dirname(__file__), 'sw_template.js'), encoding='utf8').read()
open(f'{dst}/sw.js', 'w', encoding='utf8').write(
    sw.replace('__VERSION__', version).replace('__ASSETS__', json.dumps(assets)))

# Page: the published copy may carry the artifact's document wrapper; keep only the template's content.
if page.startswith('<!doctype'):
    page = page[page.index('<body>') + len('<body>'):].replace('</body></html>', '').strip()
head = f'''<!doctype html>
<html lang="fr"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no, viewport-fit=cover">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="{SHORT}">
<meta name="theme-color" content="{BG}">
<link rel="manifest" href="manifest.webmanifest">
<link rel="apple-touch-icon" href="icons/icon-180.png">
<link rel="icon" href="icons/icon-192.png">
'''
reg = '''<script>
if ('serviceWorker' in navigator) navigator.serviceWorker.register('sw.js').catch(() => {});
</script>
'''
page = page.replace("<title>Kolizéum d'essai</title>", f'<title>{NAME}</title>').replace('<meta name="claude:viewport-fit-sides" content="cover">\n', '')
page = page.replace('<canvas id="canvas"', '</head><body>\n<canvas id="canvas"', 1)
open(f'{dst}/index.html', 'w', encoding='utf8').write(head + page + '\n' + reg + '</body></html>\n')
open(f'{dst}/.nojekyll', 'w').close()
print('version', version, '-', len(assets), 'files cached')
