# SKILLOR — YouTube Shorts France

Pipeline Python **France-first** pour une chaîne YouTube Shorts de science du quotidien :

`Sujet français → script français → voix française → visuels → sous-titres → SEO français → upload privé`

## Positionnement éditorial
- **Audience :** France et francophonie, adultes curieux de science simple.
- **Série :** *Réflexes du corps* — 500 phénomènes familiers (paupière qui saute, déjà-vu, bâillement, sommeil, etc.).
- **Langue :** tous les éléments visibles et audibles sont générés en français naturel.
- **Sécurité :** aucune promesse médicale, aucun engagement artificiel, aucune automatisation de vues/commentaires.

## Réglages France actifs
| Élément | Valeur |
|---|---|
| Recherche de tendances | `FR` |
| Région YouTube | `FR` |
| Fuseau de publication | `Europe/Paris` |
| Voix de secours/principale | Kokoro français `ff_siwis` |
| Moteur vocal | `TTS_ENGINE=kokoro` |
| Série | `body_glitches_fr` |

## Démarrage
```bash
cp env.example .env
# renseignez au minimum GROQ_API_KEY ; ajoutez OAuth YouTube pour publier
python scripts/generate_body_glitch_topics.py
python src/main.py
```

Une publication est privée par défaut : relisez le fond, la prononciation, les visuels et les métadonnées avant de la rendre publique.

## Signaux qui aident YouTube à identifier l'audience française
Le système envoie des signaux cohérents et honnêtes : langue du script, voix FR, titre/description/tags FR, région de tendances `FR`, créneaux Paris et thèmes cohérents. **Aucun réglage ne garantit une recommandation** : l'algorithme apprend surtout des spectateurs qui choisissent et regardent réellement les vidéos.
