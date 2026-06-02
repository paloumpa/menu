# Mes Menus — Famille Cordedda

Application PWA de gestion des menus familiaux, hébergée sur GitHub Pages.

**Accès :** https://paloumpa.github.io/menu

## Fonctionnalités

- Planning hebdomadaire 2 semaines (Elle / Lui / Enfants)
- Liste de courses automatique par rayon
- Suivi macros et objectifs caloriques
- Modification manuelle des repas
- Synchronisation temps réel Firebase (multi-appareils)
- Génération automatique des menus via IA (Groq / Ollama local)
- Historique des 4 dernières semaines
- Notifications rappel courses (samedi 9h)
- Installable sur mobile (PWA)

## Génération automatique

Le workflow GitHub Actions (generate-menus.yml) tourne chaque mardi à 7h (Paris) et génère la semaine suivante via l'API Groq (gratuit).  
Nécessite le secret GROQ_API_KEY dans Settings → Secrets → Actions.

Génération locale alternative : ouvrir _menus_generate.html avec Ollama/Gemma actif.