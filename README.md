# Dofus MOBA

MOBA dans l'univers de Dofus (Godot 4.4.1, export Web sans threads).

**Jouer :** https://rd-workin.github.io/dofus-moba/

## Installer sur iPhone

1. Ouvrir le lien ci-dessus dans **Safari**.
2. Bouton Partager, puis **Sur l'écran d'accueil**.
3. Lancer « Dofus MOBA » depuis l'icône : plein écran, en paysage. Après un premier chargement complet, le jeu marche aussi sans réseau.

## Organisation du dépôt

- `main` : outils et, plus tard, le serveur multijoueur.
- `gh-pages` : la version jouable publiée (fichiers générés, ne pas modifier à la main). GitHub Pages sert cette branche.

## Publier une nouvelle version

1. Exporter le jeu et le découper comme pour la page web (`prototype/package_web.py` du projet), ce qui donne un dossier `<pub>`.
2. `python3 tools/package_mobile.py <pub> <copie de la branche gh-pages>` : ajoute le manifeste, les icônes et le service worker (`tools/sw_template.js`).
3. Committer et pousser la branche `gh-pages`. Au lancement suivant, l'app télécharge la nouvelle version et remplace l'ancienne.
