# markdown_to_html.py

Convertit un fichier Markdown au format ECRI en blocs HTML pour le site *Interférences*.

## Dépendance

```
pip install markdown-it-py
```

## Usage

```
python markdown_to_html.py input.md [output.html]
```

Sans argument de sortie, imprime sur stdout.

## Format d'entrée (ECRI)

```
# Titre              → ignoré
## Modèle pour les réponses
Nom du modèle        → injecté en italique au début du premier bloc Response

## Prompt: [titre optionnel]
YYYY-MM-DD           → ignoré
contenu...

## Response:
YYYY-MM-DD           → ignoré
contenu...
```

## Format de sortie

| Section ECRI | HTML produit |
|---|---|
| `## Prompt:` | `<div class="author-voice">` |
| `## Prompt: Titre` | `<h3 class="section-title">` + `<div class="author-voice">` |
| `## Response:` | `<div class="ai-voice">` |

Le fichier produit est un fragment HTML (`<main>...</main>`), sans `<html>/<head>/<body>` — prévu pour être injecté via `fetch` dans `index.html`.

## Transformations appliquées au contenu

- Markdown standard (gras, italique, liens) → HTML
- `![alt](url_youtube)` → iframe embed responsive
- `<img src="...">` → src réécrit en `journal/media/nom_fichier`
- Blocs HTML verbatim (`<figure>`, `<iframe>`, etc.) → passés tels quels
