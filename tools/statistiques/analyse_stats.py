"""Analyse des statistiques de parties (scripts/match_stats.gd) : un ou plusieurs fichiers .jsonl (simulations ou
parties partagées depuis le téléphone). Usage : python3 analyse_stats.py fichier.jsonl [...] [--source iphone]
[--build a62c4c1c] [--humain]. Écrit un rapport Markdown sur la sortie standard."""
import sys, json, math
from collections import defaultdict

args = [a for a in sys.argv[1:] if not a.startswith('--')]
opts = dict(zip(sys.argv[1:], sys.argv[2:]))
games = []
for path in args:
    for line in open(path, encoding='utf8'):
        line = line.strip()
        if line:
            try:
                games.append(json.loads(line))
            except ValueError:
                pass
if '--source' in opts:
    games = [g for g in games if g['source'] == opts['--source']]
if '--build' in opts:
    games = [g for g in games if g['build'] == opts['--build']]
done = [g for g in games if g['gagnant'] in (0, 1)]
only_human = '--humain' in sys.argv


def pct(a, b):
    return f'{100 * a / b:.0f} %' if b else '-'


def ci(w, n):
    """Victoires sur n : pourcentage ± intervalle à 95 %."""
    if not n:
        return '-'
    p = w / n
    return f'{100 * p:.0f} % ± {100 * 1.96 * math.sqrt(p * (1 - p) / n):.0f}'


def mean(xs):
    xs = list(xs)
    return sum(xs) / len(xs) if xs else 0.0


def at(curve, m):
    return curve[m - 1] if len(curve) >= m else None


out = []
p = out.append
p(f'# Statistiques : {len(games)} parties ({len(done)} terminées par un Prisme)\n')
if not games:
    print('\n'.join(out))
    sys.exit()
dur = [g['duree'] / 60 for g in done]
p(f'- Durée moyenne d\'une partie terminée : {mean(dur):.1f} min (de {min(dur, default=0):.0f} à {max(dur, default=0):.0f})')
p(f'- Victoires de Bonta (équipe 0) : {ci(sum(g["gagnant"] == 0 for g in done), len(done))}')
p(f'- Kills par partie : {mean(sum(g["kills"]) for g in games):.1f}, soit {mean(sum(g["kills"]) / max(1, g["duree"] / 60) for g in games):.2f} par minute')
p(f'- Sources : ' + ', '.join(f'{s} {sum(g["source"] == s for g in games)}' for s in sorted({g["source"] for g in games})))
p('')

rows = defaultdict(list)       # (axe, valeur) -> [(partie, héros)]
for g in games:
    for i, h in enumerate(g['heros']):
        if only_human and not h['humain']:
            continue
        rows[('classe', h['id'])].append((g, h, i))
        rows[('poste', h['poste'])].append((g, h, i))


def table(axis, title):
    p(f'## {title}\n')
    p('| | parties | victoires | K / M / A | kamas/min | kamas à 5 / 10 / 15 min | dégâts héros/min | dégâts tours/min | niv. final | temps mort |')
    p('|---|---|---|---|---|---|---|---|---|---|')
    keys = sorted({k for a, k in rows if a == axis})
    stats = []
    for k in keys:
        rs = rows[(axis, k)]
        fin = [(g, h) for g, h, i in rs if g['gagnant'] in (0, 1)]
        w = sum(g['gagnant'] == h['equipe'] for g, h in fin)
        mins = lambda g: max(1.0, g['duree'] / 60)
        curve = [mean(x for x in (at(h['courbe_kamas'], m) for g, h, i in rs) if x is not None) for m in (5, 10, 15)]
        stats.append((w / len(fin) if fin else 0, k))
        p(f'| **{k}** | {len(rs)} | {ci(w, len(fin))} | {mean(h["k"] for g, h, i in rs):.1f} / {mean(h["m"] for g, h, i in rs):.1f} / '
          f'{mean(h["a"] for g, h, i in rs):.1f} | {mean(h["kamas"] / mins(g) for g, h, i in rs):.0f} | '
          f'{" / ".join(f"{c:.0f}" for c in curve)} | {mean(h["degats_heros"] / mins(g) for g, h, i in rs):.0f} | '
          f'{mean(h["degats_tours"] / mins(g) for g, h, i in rs):.0f} | {mean(h["niv"] for g, h, i in rs):.1f} | '
          f'{pct(sum(h["temps_mort"] for g, h, i in rs), sum(g["duree"] for g, h, i in rs))} |')
    p('')
    return stats


table('poste', 'Par poste')
table('classe', 'Par classe')

# Sources de kamas par poste.
p('## D\'où viennent les kamas (part du total, par poste)\n')
srcs = ['sbires', 'sbires_partage', 'jungle', 'objectifs', 'kills', 'assists', 'tours', 'autre']
p('| poste | ' + ' | '.join(srcs) + ' | sbires tués/min | monstres tués/min |')
p('|---|' + '---|' * (len(srcs) + 2))
for k in sorted({k for a, k in rows if a == 'poste'}):
    rs = rows[('poste', k)]
    tot = sum(h['kamas'] for g, h, i in rs) or 1
    p(f'| {k} | ' + ' | '.join(pct(sum(h['src'].get(s, 0) for g, h, i in rs), tot) for s in srcs) +
      f' | {mean(h["sbires"] / max(1, g["duree"] / 60) for g, h, i in rs):.1f} | {mean(h["monstres"] / max(1, g["duree"] / 60) for g, h, i in rs):.1f} |')
p('')

# Morts.
deaths = []
for g in games:
    for d in g['morts']:
        h = g['heros'][d['victime']]
        if only_human and not h['humain']:
            continue
        deaths.append((g, d, h))
n = len(deaths)
p(f'## Morts ({n}, {n / max(1, len(games)):.1f} par partie)\n')
p(f'- Sous une tour ennemie : {pct(sum(d["sous_tour"] for g, d, h in deaths), n)} ; la tour a frappé dans les 4 dernières secondes : {pct(sum(d["tour_frappe"] for g, d, h in deaths), n)}')
p(f'- Plongées (sous la tour ennemie en frappant un héros) : {pct(sum(d["plongee"] for g, d, h in deaths), n)}')
p(f'- Part moyenne de la tour dans les dégâts reçus avant une mort sous tour : {mean(d["part_tour"] for g, d, h in deaths if d["sous_tour"]) * 100:.0f} %')
p(f'- Achevé par la tour seule (aucun héros n\'a le kill) : {pct(sum(d["tueur"] < 0 for g, d, h in deaths), n)}')
p(f'- En infériorité (au moins 2 ennemis de plus autour) : {pct(sum(d["ennemis"] >= d["allies"] + 2 for g, d, h in deaths), n)} ; seul contre 1 : {pct(sum(d["ennemis"] == 1 and d["allies"] == 0 for g, d, h in deaths), n)}')
p(f'- Dans la fontaine ennemie : {pct(sum(d["fontaine"] for g, d, h in deaths), n)} ; dans la jungle : {pct(sum(d["jungle"] for g, d, h in deaths), n)}')
p('')
p('| par poste | morts/partie | sous tour | tour a frappé | plongées | infériorité |')
p('|---|---|---|---|---|---|')
for k in sorted({h['poste'] for g, d, h in deaths}):
    ds = [(g, d) for g, d, h in deaths if h['poste'] == k]
    ng = len(rows[('poste', k)]) or 1
    p(f'| {k} | {len(ds) / ng:.1f} | {pct(sum(d["sous_tour"] for g, d in ds), len(ds))} | {pct(sum(d["tour_frappe"] for g, d in ds), len(ds))} | '
      f'{pct(sum(d["plongee"] for g, d in ds), len(ds))} | {pct(sum(d["ennemis"] >= d["allies"] + 2 for g, d in ds), len(ds))} |')
p('')
p('| phase | morts | sous tour | plongées |')
p('|---|---|---|---|')
for lo, hi in ((0, 300), (300, 600), (600, 900), (900, 1200), (1200, 99999)):
    ds = [d for g, d, h in deaths if lo <= d['t'] < hi]
    p(f'| {lo // 60}-{hi // 60 if hi < 99999 else "fin"} min | {len(ds)} | {pct(sum(d["sous_tour"] for d in ds), len(ds))} | {pct(sum(d["plongee"] for d in ds), len(ds))} |')
p('')

# Tours et objectifs.
first_tower = [min((t['t'] for t in g['tours']), default=None) for g in games]
first_tower = [x for x in first_tower if x is not None]
p('## Tours et objectifs\n')
p(f'- Première tour tombée à {mean(first_tower) / 60:.1f} min en moyenne ; tours détruites par partie : {mean(len(g["tours"]) for g in games):.1f}')
for kind in ('tortue', 'seigneur'):
    taken = [o for g in games for o in g['objectifs'] if o.startswith(kind)]
    p(f'- {kind.capitalize()} : {len(taken) / max(1, len(games)):.1f} par partie')
p('')

# Jungler : écart de kamas avec son équipe, et victoires selon le jungler le plus riche.
p('## Jungler\n')
gap = []
richer = []
for g in done:
    for team in (0, 1):
        hs = [h for h in g['heros'] if h['equipe'] == team]
        jg = [h for h in hs if h['poste'] == 'jungle']
        if not jg:
            continue
        others = [h['kamas'] for h in hs if h['poste'] != 'jungle']
        gap.append(jg[0]['kamas'] / max(1, mean(others)))
    j = {h['equipe']: h for h in g['heros'] if h['poste'] == 'jungle'}
    if len(j) == 2 and j[0]['kamas'] != j[1]['kamas']:
        rich = 0 if j[0]['kamas'] > j[1]['kamas'] else 1
        richer.append(g['gagnant'] == rich)
p(f'- Kamas du jungler / moyenne des 4 autres de son équipe : {mean(gap):.2f}')
p(f'- L\'équipe dont le jungler est le plus riche gagne : {ci(sum(richer), len(richer))}')
for k in ('exp', 'gold', 'mid', 'soutien', 'jungle'):
    r = []
    for g in done:
        j = {h['equipe']: h for h in g['heros'] if h['poste'] == k}
        if len(j) == 2 and j[0]['kamas'] != j[1]['kamas']:
            r.append(g['gagnant'] == (0 if j[0]['kamas'] > j[1]['kamas'] else 1))
    p(f'- Poids du poste {k} : l\'équipe dont ce poste a le plus de kamas gagne {ci(sum(r), len(r))}')
p('')
print('\n'.join(out))
