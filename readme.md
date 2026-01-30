# 🚎 FilBleu Predictor — Prédiction des retards 

**FilBleu Predictor** est un projet de **Data Science, Machine Learning et Visualisation de données**
appliqué aux transports en commun, basé sur les données **GTFS et GTFS-RT** du réseau **Fil Bleu (Tours Métropole)**.

L’objectif est double :
- **analyser les retards observés** sur le réseau,
- **estimer un retard en minutes** pour une situation donnée  
  (ligne, arrêt, heure, jour), via une application interactive.

---

## 🎯 Objectifs du projet

- Mettre en place une **collecte automatisée de données temps réel** via API
- Transformer des données brutes GTFS / GTFS-RT en un **dataset exploitable**
- Analyser les retards (tendances temporelles, lignes, arrêts)
-Mettre en place **un modèle prédictif** pour estimer les retards en minutes
- Déployer une **application Streamlit** pour l'utilisateur

---

## 📁 Structure du projet

```

C:.
├── data/
│   ├── raw/          # Données brutes (GTFS / GTFS-RT)
│   ├── processed/    # Données intermédiaires
│   └── final/        # Datasets ML
│
├── models/           # Modèles entraînés et métriques
├── demo/             # Version déployable (modèle + données exemple)
├── src/              # Code source
│   ├── scraping/     # Collecte, parsing, calcul des retards
│   └── ml/           # Préparation dataset & entraînement
│
├── app.py            # Application Streamlit
├── requirements.txt
└── README.md

```
---


## 📊 Données & collecte

### Sources des données
Les données proviennent de sources **officielles open data** (site : https://transport.data.gouv.fr), mises à disposition par le réseau Fil Bleu :

- **GTFS statique**  
  Structure du réseau : lignes, arrêts, trajets et horaires théoriques
- **GTFS-RT (temps réel)**  
  Informations de passage et de retard, fournies via une **API publique**  
  (format **Protocol Buffers**)

---

### Méthode de collecte (scraping via API)

La collecte repose sur une approche de **scraping au sens large**, via interrogation automatique d’une API :

- Appels réguliers à l’API **GTFS-RT**
- Collecte par **snapshots temps réel** toutes les **3 minutes** à l’aide d’un script que nous lançons et laissons s’exécuter sur une période donnée
- Sauvegarde des fichiers bruts (`.bin`) pour assurer la traçabilité
- Parsing et transformation en données structurées (CSV)

Chaque snapshot correspond à une **capture instantanée de l’état du réseau** et génère plusieurs observations après parsing.

---

### Volume des données

- Plusieurs centaines de **snapshots temps réel**
- Environ **1,2 million d’observations** finales
- **1 observation = passage d’un bus à un arrêt à un instant donné**


---

## 🧮 Reconstruction du retard

Le retard est recalculé de manière homogène selon la formule :

```
retard = heure réelle − heure théorique
```

Étapes principales :
- Conversion des horaires GTFS (gestion des heures > 24h)
- Conversion des timestamps Unix en heure locale (**Europe/Paris**)
- Fusion GTFS statique / GTFS-RT via `trip_id` et `stop_id`

Un retard positif correspond à un **retard**, un retard négatif à une **avance**.

---

## 📈 Analyse des données

L’application propose plusieurs analyses interactives :
- Distribution des retards et quantiles
- Tendances temporelles (heure de la journée)
- Analyse par ligne
- Analyse par arrêt
- Couverture temporelle des données

Ces analyses permettent de **contextualiser** les prédictions et de mieux comprendre
le comportement réel du réseau.

---

## 🤖 Modélisation Machine Learning

- **Type de problème** : régression supervisée
- **Variable cible** : `delay_minutes`
- **Features principales** :
  - heure, jour de la semaine
  - heures de pointe / week-end
  - ligne
  - arrêt (fréquence, position dans le trajet)
- **Modèles testés** :
  - baseline
  - Random Forest
  - Gradient Boosting
- **Métriques d’évaluation** :
  - MAE (erreur moyenne interprétable en minutes)
  - RMSE (sensibilité aux grosses erreurs)

Le modèle sélectionné est sauvegardé et réutilisé directement dans l’application.

---

## 🖥️ Application Streamlit

L’application permet :
- d’explorer les données de retard
- de filtrer par ligne, arrêt, heure et jour
- d’estimer un retard pour un cas utilisateur précis
- de contextualiser la prédiction via des indicateurs statistiques.

L’interface est pensée pour être **utilisable sans connaissance technique**.

---

## ⚠️ Limites du projet

Malgré les résultats obtenus, ce projet présente plusieurs limites qu’il est important de souligner.

### Couverture temporelle des données
La collecte des données temps réel repose sur l’exécution manuelle d’un script de collecte (scrape_gtfs_rt.py).
La période observée reste donc limitée à certaines plages horaires et à quelques jours, ce qui peut introduire un biais temporel dans les analyses et les prédictions.

### Contraintes liées aux périodes de vacances
Une partie des données temps réel collectées n’a pas pu être exploitée, car les **horaires théoriques correspondant aux périodes de vacances n’étaient pas disponibles** dans les données GTFS statiques au moment du projet.
Cela a conduit à l’exclusion de certains jours de collecte (4 jours précisément), afin de garantir la cohérence entre horaires théoriques et horaires réels lors du calcul des retards.

### Absence de certaines variables explicatives
Le modèle ne prend pas en compte des facteurs externes pouvant fortement influencer les retards,
tels que :
- les conditions météorologiques,
- le trafic routier,
- les incidents ou événements exceptionnels.
L’intégration de telles variables pourrait améliorer la performance prédictive du modèle.

---

# 📦 Données & modèles

Les données GTFS / GTFS-RT et les modèles entraînés
ne sont pas versionnés sur GitHub pour des raisons de taille.

---

## 👤 Auteurs

- **Hafsa Mousalli**
- **Imane Lemkhayer**
```

