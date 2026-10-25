# Sécurité

## Signaler une faille

Merci de ne pas ouvrir d'issue publique. Utilise le bouton **Report a vulnerability** de l'onglet
[Security](../../security/advisories/new) du dépôt (signalement privé).

## Règles du dépôt

- Aucun secret dans le dépôt : ni mot de passe, ni clé d'API, ni clé SSH, ni fichier `.env`. Les secrets du serveur
  multijoueur vivent sur le serveur (variables d'environnement) ou dans les *Secrets* de GitHub Actions.
- `main` contient les outils (et plus tard le serveur) ; `gh-pages` ne contient que la version jouable générée.
- La page du jeu déclare une politique de sécurité du contenu (CSP, ajoutée par `tools/package_mobile.py`) :
  scripts du site seulement, connexions vers le site seulement. Le multijoueur devra y ajouter l'adresse `wss://`
  de son serveur.
- Le serveur multijoueur fait autorité : il ne fait jamais confiance au client (voir le fil sécurité du projet).
