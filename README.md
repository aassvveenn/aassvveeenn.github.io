# Interférences — documentation

Carnet musique & écriture. HTML statique, CSS global partagé, hébergé sur GitHub Pages.

---

## Structure

```
interferences/
├── index.html            ← squelette : header + liste de liens uniquement
├── interferences.css     ← feuille de style globale (partagée par toutes les pages)
├── README.md
├── journal/
│   ├── YYYY-MM-DD-slug.html
│   └── ...
├── transmissions/
│   └── transmissions.html
├── rotations/
│   └── rotations.html
└── publications/
    └── publications.html
```

---

## Principes

- `index.html` est un squelette. On ne le touche que pour ajouter un lien vers une nouvelle entrée journal, ou signaler une mise à jour des sections transversales. Jamais de contenu développé dedans.
- `interferences.css` est le seul fichier de style. Toute modification CSS se répercute sur l'ensemble du site.
- Tous les chemins sont **relatifs**. Le repo peut être renommé ou déplacé sans rien casser.
- Les sections `transmissions`, `rotations`, `publications` sont des fichiers monolithiques qui évoluent à leur propre rythme.

---

## Nommage des entrées journal

```
YYYY-MM-DD-slug.html
```

Exemples :
```
2026-03-20-daft-punk.html
2026-03-20-autechre.html
2026-02-26-eliane-radigue.html
```

La date en préfixe garantit l'ordre chronologique naturel dans le dossier. Plusieurs entrées à la même date sont possibles — le slug les distingue. Plusieurs entrées sur le même sujet à des dates différentes sont explicitement prévues.

---

## Workflow pour une nouvelle entrée journal

1. Produire l'entrée avec Claude (ici, dans le projet Claude)
2. Télécharger le fichier `.html` généré
3. Le placer dans `journal/`
4. Ajouter le lien correspondant dans `index.html`
5. Pusher — GitHub Pages publie automatiquement

---

## Workflow pour une mise à jour de section transversale

1. Demander la mise à jour à Claude
2. Télécharger le fichier `.html` mis à jour
3. Remplacer le fichier existant dans le dossier correspondant
4. Pusher

---

## Workflow CSS

Toute modification du style se fait dans `interferences.css` uniquement. On valide le rendu sur `interferences_preview.html` avant de toucher au CSS en production.

---

## Conventions typographiques dans le HTML

| Élément | Classe CSS | Police | Usage |
|---|---|---|---|
| Corps de texte (voix auteur) | `.author-voice` | Playfair Display | Texte de l'auteur, formulations directes |
| Observations | `.observation` | DM Mono | Apports extérieurs, analyses |
| Citation de tiers | `<blockquote>` | Playfair Display italic | Citations d'artistes, d'interviewés |
| Date d'entrée | `.entry-date` | DM Mono | Méta |
| Titre d'entrée | `.entry-title` | DM Mono | Titres des entrées journal |

Albums : `<em>Titre</em>`
Morceaux : entre guillemets dans le texte, sans balise spécifique

---

## Évolution vers Jekyll

Le site est conçu pour une migration Jekyll sans perte. Quand le moment vient :
- Les fichiers HTML deviennent des fichiers Markdown + front matter
- `interferences.css` reste inchangé
- `index.html` devient un layout Liquid généré automatiquement

Rien à réécrire, juste à restructurer.
