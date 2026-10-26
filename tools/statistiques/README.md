# Statistiques de parties

Le jeu enregistre chaque 5 contre 5 (une ligne JSON par partie, `user://stats/parties.jsonl`, voir
`scripts/match_stats.gd` du projet Godot). Sur l'iPhone : Options > Jeu > Statistiques des parties > « Partager le fichier ».

- `run_batch.sh <étiquette> <n° worker> <nombre>` : parties de bots sans écran (`godot ... -- --stattest`), en accéléré.
  `DIR=` dossier du projet Godot ; les lignes vont dans `~/sim/out/<étiquette>_w<n>.jsonl`.
- `analyse_stats.py fichiers.jsonl [--source iphone] [--humain] [--build xxxx]` : rapport Markdown (classes, postes,
  sources de kamas, morts sous tour et plongées, jungler).
