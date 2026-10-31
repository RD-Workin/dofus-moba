"""Turns the published web version (output of package_web.py) into an app installable from the iPhone home screen
(PWA): icon, full screen, offline cache. Usage: python3 package_mobile.py <pub> <out> [icon.png]
<out> is what gets pushed to the GitHub Pages repo (its root)."""
import sys, os, shutil, json, hashlib, base64, re
from PIL import Image

src, dst = sys.argv[1], sys.argv[2]
icon_src = sys.argv[3] if len(sys.argv) > 3 else os.path.join(os.path.dirname(__file__), 'icone.png')
NAME, SHORT, BG = 'Dofus MOBA', 'Dofus MOBA', '#1d1710'

os.makedirs(dst, exist_ok=True)
for f in os.listdir(dst):
    if f not in ('.git', 'README.md', '.nojekyll'):
        p = os.path.join(dst, f)
        shutil.rmtree(p) if os.path.isdir(p) else os.remove(p)
page = open(f'{src}/index.html', encoding='utf8').read()
# Game parts get their content hash in the name (g0.wasm -> g0.1a2b3c4d.wasm): a new version can never be mixed
# with a stale copy from a cache, and unchanged parts (often the engine) are not downloaded again.
files = []
for f in sorted(os.listdir(src)):
    if f == 'index.html':
        continue
    out = f
    if re.fullmatch(r'[gp]\d+\.wasm', f):
        out = f'{f[:-5]}.{hashlib.sha256(open(os.path.join(src, f), "rb").read()).hexdigest()[:8]}.wasm'
        page = page.replace(f'"{f}"', f'"{out}"')
    shutil.copy(os.path.join(src, f), os.path.join(dst, out))
    files.append(out)

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
    h.update(open(os.path.join(dst, f), 'rb').read())
h.update(page.encode())
h.update(open(__file__, 'rb').read())   # une modification de ce script (et donc de la page) est aussi une nouvelle version
h.update(open(os.path.join(os.path.dirname(__file__), 'sw_template.js'), 'rb').read())
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
label = re.sub(r'[^\w .:-]', '', os.environ.get('APP_LABEL', ''))   # « v95 », pris dans le message de publish_github.sh
reg = '''<div id="ver" hidden></div>
<div id="maj" hidden><span>Nouvelle version disponible</span><button type="button">Mettre à jour</button><button type="button" aria-label="Plus tard">✕</button></div>
<style>
#maj { position: fixed; z-index: 10; top: max(8px, env(safe-area-inset-top, 0px)); left: 50%; transform: translateX(-50%);
  display: flex; align-items: center; gap: 10px; padding: 6px 6px 6px 14px; border-radius: 99px; white-space: nowrap;
  background: #3a2f22; border: 1px solid #5a4a36; color: var(--ink); font-size: .9rem; box-shadow: 0 4px 16px #0008; }
#maj[hidden], #ver[hidden] { display: none; }
#ver { position: fixed; z-index: 10; top: max(8px, env(safe-area-inset-top, 0px)); left: 50%; transform: translateX(-50%);
  padding: 4px 12px; border-radius: 99px; background: #3a2f22cc; color: var(--muted); font-size: .8rem; pointer-events: none;
  transition: opacity .6s; }
#maj button { font: inherit; color: var(--ink); background: none; border: 0; padding: 6px 10px; border-radius: 99px; }
#maj button:first-of-type { background: var(--accent); color: #1d1710; font-weight: 600; }
</style>
<script>
// Mise à jour : la page connaît sa version, et va voir de temps en temps celle publiée (version.json, jamais en cache).
// Si elles diffèrent, un bandeau propose de recharger ; le joueur choisit le moment (pas en pleine partie).
(() => {
  const VERSION = '__APP_VERSION__', LABEL = '__APP_LABEL__';
  // Numéro de la version installée, visible quelques secondes à chaque lancement.
  const ver = document.getElementById('ver');
  if (LABEL) {
    ver.textContent = 'Dofus MOBA ' + LABEL; ver.hidden = false;
    setTimeout(() => { ver.style.opacity = 0; setTimeout(() => ver.hidden = true, 700); }, 6000);
  }
  const bar = document.getElementById('maj'), [go, later] = bar.querySelectorAll('button');
  let reg = null, dismissed = null;
  if ('serviceWorker' in navigator)
    navigator.serviceWorker.register('sw.js').then(r => { reg = r; r.update(); }).catch(() => {});
  const check = async () => {
    try {
      const r = await fetch('version.json', { cache: 'no-store' });
      const j = await r.json(), v = j.version;
      if (v && v !== VERSION && v !== dismissed) {
        bar.firstElementChild.textContent = 'Nouvelle version disponible' + (j.label ? ' : ' + j.label : '');
        ver.hidden = true; bar.hidden = false;
      }
    } catch (e) {}   // hors ligne : on réessaiera
  };
  go.onclick = async () => {
    go.textContent = 'Mise à jour…';
    try { if (reg) await reg.update(); } catch (e) {}
    location.reload();
  };
  later.onclick = () => { bar.hidden = true; fetch('version.json', { cache: 'no-store' }).then(r => r.json()).then(j => dismissed = j.version).catch(() => {}); };
  setTimeout(check, 5000);
  setInterval(check, 5 * 60 * 1000);
  document.addEventListener('visibilitychange', () => { if (!document.hidden) check(); });
})();
</script>
'''.replace('__APP_VERSION__', version).replace('__APP_LABEL__', label)
page = page.replace("<title>Kolizéum d'essai</title>", f'<title>{NAME}</title>').replace('<meta name="claude:viewport-fit-sides" content="cover">\n', '')
page = page.replace('<canvas id="canvas"', '</head><body>\n<canvas id="canvas"', 1)
html = head + page + '\n' + reg + '</body></html>\n'
# Sécurité : GitHub Pages ne permet pas d'en-têtes HTTP, la politique passe donc par une balise meta.
# Seuls les scripts du site (et les scripts en ligne de cette page, par leur empreinte) peuvent tourner, et la page
# ne peut contacter que son propre site. 'unsafe-eval' : JavaScriptBridge.eval du jeu ; 'wasm-unsafe-eval' : le moteur.
# Le multijoueur devra ajouter l'adresse wss:// de son serveur à connect-src.
hashes = ' '.join("'sha256-%s'" % base64.b64encode(hashlib.sha256(s.encode()).digest()).decode()
                  for s in re.findall(r'<script>(.*?)</script>', html, re.S))
csp = (f"default-src 'self'; script-src 'self' {hashes} 'unsafe-eval' 'wasm-unsafe-eval'; style-src 'self' 'unsafe-inline'; "
       "img-src 'self' data: blob:; media-src 'self' data: blob:; connect-src 'self'; worker-src 'self' blob:; "
       "object-src 'none'; base-uri 'none'; form-action 'none'")
html = html.replace('<meta charset="utf-8">\n', f'<meta charset="utf-8">\n<meta http-equiv="Content-Security-Policy" content="{csp}">\n'
                    '<meta name="referrer" content="no-referrer">\n', 1)
open(f'{dst}/index.html', 'w', encoding='utf8').write(html)
open(f'{dst}/.nojekyll', 'w').close()
json.dump({'version': version, 'label': label}, open(f'{dst}/version.json', 'w'))
print('version', version, '-', len(assets), 'files cached')
