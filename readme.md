# 🚎 FilBleu Predictor — Prédiction des retards (Tours)

**FilBleu Predictor** est un projet de **Machine Learning & Data Visualisation**
appliqué aux transports en commun, basé sur les données **GTFS & GTFS-RT**
du réseau **Fil Bleu (Tours)**.

L’objectif est double :
- analyser les retards observés sur le réseau,
- prédire un **retard en minutes** selon une situation donnée  
  (ligne, arrêt, heure, jour).

---

## 🎯 Objectifs du projet

- Collecter des données temps réel (**GTFS-RT**) via web scraping
- Reconstruire les retards à partir des horaires théoriques (**GTFS statique**)
- Explorer les retards (tendances temporelles, lignes, arrêts)
- Entraîner un modèle de **régression**
- Proposer une **application Streamlit** interactive

---

## 📊 Données & collecte

### Sources
- **GTFS statique** : structure du réseau (lignes, arrêts, horaires)
- **GTFS-RT** : données temps réel (Protocol Buffers)

### Méthode
- Web scraping ponctuel de l’API GTFS-RT Fil Bleu
- Parsing des fichiers `.bin`
- Reconstruction du retard `delay_minutes` par comparaison :
  - horaire réel vs horaire théorique
- Gestion du fuseau horaire **Europe/Paris**

---

## 🧠 Méthodologie de collecte (approche hybride)

### Contraintes
- Collecte continue 24/7 → infrastructure serveur nécessaire
- Besoin d’un volume suffisant pour le Machine Learning

### Approche retenue

#### 1️⃣ Collecte temps réel (validation)
- Collectes ponctuelles sur plusieurs jours
- Observation des patterns réels de retard

#### 2️⃣ Base GTFS statique
- **1 469 821** horaires théoriques
- **2 146 arrêts**, **44 lignes**
- Couverture complète du réseau

#### 3️⃣ Simulation calibrée (data augmentation)
- Génération de retards basée sur les observations réelles
- Variables prises en compte :
  - heure
  - jour de la semaine
  - ligne
  - arrêt
- Dataset final : **50 000+ passages avec retard**

Cette approche est couramment utilisée en **industrie**
lorsque les données temps réel sont limitées.

---

## 🤖 Modélisation Machine Learning

- **Type** : régression (retard en minutes)
- **Features principales** :
  - heure, jour de la semaine
  - heure de pointe / week-end
  - ligne et type de ligne
  - fréquence et localisation des arrêts
- **Modèles testés** :
  - baseline
  - Random Forest / Gradient Boosting
- **Métrique principale** :
  - MAE (Mean Absolute Error)

---

## 📊 Application Streamlit

L’application permet :
- 📈 d’explorer les retards (tendances, lignes, arrêts)
- 🔍 de filtrer par heure, jour, ligne et arrêt
- 🔮 de prédire un retard avec un indicateur de risque 🟢🟡🔴
- 📌 de comparer prédiction et statistiques historiques

---

## 🛠️ Stack technique

- Python  
- Pandas, NumPy  
- Scikit-learn  
- Web scraping (GTFS-RT, Protocol Buffers)  
- Streamlit  
- Git & GitHub  

---

## 📦 Données & modèles
Les données GTFS / GTFS-RT et les modèles entraînés
ne sont pas versionnés sur GitHub pour des raisons de taille.


## 📁 Structure du projet
```
PROJET-ML-WEB-SCRAPING/
├── app/              # Application Streamlit
├── data/             # Données
│   ├── raw/          # Données brutes
│   ├── processed/    # Données nettoyées
│   └── final/        # Dataset ML
├── src/              # Code source
│   ├── scraping/     # Scripts de collecte
│   └── ml/           # Scripts ML
├── requirements.txt
├── README.md
└── .gitignore
```

👤 Auteurs
Hafsa Mousalli
Imane Lemkhayer