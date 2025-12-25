
# 📘 GUIDE DU PROJET — FilBleu Predictor  
*(Document interne — explication simple du travail réalisé)*

---

## 🎯 Objectif du projet

Créer une application qui permet :

- d’**analyser les retards** sur le réseau Fil Bleu (Tours)
- de **prédire un retard (en minutes)** selon :
  - une ligne
  - un arrêt
  - une heure
  - un jour

Le projet suit un **pipeline data complet** :

```

Collecte temps réel
→ Reconstruction des retards
→ Préparation des données
→ Machine Learning
→ Application Streamlit

```

---

## 🧱 Vue d’ensemble du projet (ce qu’il fait vraiment)

- Les données **GTFS statiques** donnent les horaires théoriques
- Les données **GTFS-RT** donnent les horaires réels observés
- L’API **ne fournit pas les retards calculés**
👉 on les **reconstruit nous-mêmes**
- Ces retards servent ensuite :
  - à l’analyse (Data Viz)
  - à l’entraînement d’un modèle ML
  - à une application Streamlit interactive

---

## 📁 Structure du projet (simplifiée)

```

PROJET-ML-WEB-SCRAPING/
│
├── app/                  # Application Streamlit
│   └── app.py
│
├── src/
│   ├── scraping/         # Collecte + traitement des données
│   └── ml/               # Préparation dataset & entraînement ML
│
├── requirements.txt
├── README.md             # Documentation officielle (GitHub)
├── EXPLICATION.md        # Ce fichier (guide interne)
└── .gitignore

```

⚠️ Les dossiers `data/` et `models/` existent **en local**,  
mais **ne sont pas sur GitHub** (trop volumineux).

---

## 📊 Les données utilisées

### 1️⃣ GTFS statique (horaires théoriques)

📍 **Rôle** : savoir **quand un bus est censé passer**

- Arrêts (2 146)
- Lignes (44)
- Horaires programmés (~1,4 million)

Ces données servent de **référence théorique**.

---

### 2️⃣ GTFS-RT (temps réel)

📍 **Rôle** : savoir **quand le bus passe réellement**

- Données collectées via l’API Fil Bleu
- Format binaire `.bin` (Protocol Buffers)
- Chaque fichier = un **snapshot** du réseau à un instant donné

👉 Ces données sont **brutes** et **illisibles directement**.

---

## 🔧 Scripts principaux (expliqués simplement)

### `scrape_gtfs_rt.py` — Collecte temps réel

- Se connecte à l’API Fil Bleu
- Télécharge les horaires réels
- Sauvegarde des fichiers `.bin`

👉 Sert uniquement à **collecter la matière première**

---

### `parse_gtfs_rt.py` — Conversion `.bin → CSV`

Pourquoi ?
- Les fichiers `.bin` ne sont pas exploitables
- On les transforme en CSV lisible

Résultat :
- Un fichier avec :
  - trip_id
  - stop_id
  - heure réelle (timestamp)

---

### `calculate_delays.py` — ⭐ CŒUR DU PROJET !!!!

📌 **Problème de départ**  
L’API Fil Bleu fournit un champ `delay`, mais il vaut **toujours 0**.

📌 **Solution mise en place**
On calcule nous-mêmes :

```

retard (minutes) = heure réelle - heure théorique

````

Ce que fait le script :
1. Charge les horaires théoriques (GTFS statique)
2. Charge les horaires réels (GTFS-RT parsé)
3. Fusionne sur `trip_id` + `stop_id`
4. Calcule le retard !!!
5. Corrige le fuseau horaire (UTC → Europe/Paris)

📊 Résultat :
- Un dataset final `delays_calculated.csv`
- Retards positifs = retard
- Retards négatifs = avance

---

## 🤖 Machine Learning (ce qui a été fait)

### Pourquoi un problème de régression ?

L’objectif du projet est de **prédire un retard en minutes**.

Un retard :
- n’est pas une catégorie (petit / moyen / grand),
- mais une **valeur numérique continue**  
  (exemples : 1.5 min, 4.2 min, 12 min, -2 min).

➡️ Ce type de problème correspond à une **régression**  
(prédire un nombre réel), et non à une classification.

---

### Variable cible

La variable à prédire est : delay_minutes
Elle représente :
- un **retard positif** → le véhicule arrive en retard,
- un **retard négatif** → le véhicule arrive en avance.

Cette variable est directement exploitable d’un point de vue métier
(car exprimée en minutes).

---

### Features utilisées (variables explicatives)

Le retard dépend fortement du **contexte de circulation**.
Les principales variables utilisées sont :

- **heure** : le trafic varie fortement selon le moment de la journée
- **jour de la semaine** : semaine ≠ week-end
- **heure de pointe** : congestion plus forte
- **week-end** : comportement différent du réseau
- **ligne** : certaines lignes sont structurellement plus sensibles aux retards
- **arrêt** : localisation et fréquence influencent le retard

Ces variables permettent de décrire une situation réelle de passage d’un bus.

---

### Modèles testés

Plusieurs modèles ont été évalués :

- **Baseline**  
  → prédiction simple servant de point de comparaison

- **Random Forest / Gradient Boosting**  
  → modèles non linéaires capables de capturer :
  - effets d’heures de pointe
  - différences entre lignes
  - interactions entre variables

Ces modèles sont bien adaptés aux données tabulaires
et aux phénomènes non linéaires.

---

### Métrique choisie : MAE

La métrique principale est la **MAE (Mean Absolute Error)**.

Pourquoi ?
- Elle s’exprime en **minutes**
- Elle est **facile à interpréter**
- Une MAE de 3 signifie :
  > “En moyenne, la prédiction se trompe de 3 minutes”

C’est une métrique directement compréhensible pour un usage métier.

---

Le modèle retenu est le **Gradient Boosting**.

Même si les Random Forest sont souvent efficaces sur des données tabulaires,
le Gradient Boosting obtient ici de **meilleures performances sur le jeu de test** :

- MAE plus faible
- RMSE plus faible
- R² plus élevé

Cela indique une meilleure capacité à prédire précisément
le retard en minutes.

Le choix du modèle est donc basé sur les **résultats observés**
et non sur un choix théorique.

CONCLUSION : On a testé plusieurs modèles.
Le Gradient Boosting a été retenu car il obtient la plus faible erreur moyenne en minutes sur le jeu de test.
Le choix du modèle est donc basé sur les résultats observés, et non sur un choix théorique.

---

## 📊 Application Streamlit

L’application permet :

- une page **Data Visualization**
  - tendances horaires
  - lignes les plus en retard
  - arrêts les plus impactés
- une page **Prédiction**
  - choix ligne / arrêt / heure / jour
  - estimation du retard
  - indicateur de risque 🟢🟡🔴

👉 C’est la **mise en valeur finale** du travail data + ML.

---

## 📦 Données & GitHub (point important)

Les dossiers suivants **ne sont pas sur GitHub** :
- `data/`
- `models/`

Pourquoi ?
- Trop volumineux
- Mauvaise pratique professionnelle

👉 Les données sont **reconstruites via les scripts** :
```powershell
python src/scraping/scrape_gtfs_rt.py
python src/ml/prepare_dataset.py
python src/ml/train_model.py
````

---

## ✅ Ce qui a été fait (résumé clair)

✔️ Collecte GTFS-RT
✔️ Parsing Protocol Buffers
✔️ Reconstruction des retards
✔️ Dataset exploitable
✔️ Modélisation ML
✔️ Application Streamlit
✔️ Repo GitHub propre (code only)

👉 Le projet couvre **toute la chaîne data**.

---

## 🧠 Ce que le projet démontre

* Compréhension des données temps réel
* Manipulation de formats complexes
* Raisonnement data (pas juste appliquer un modèle)
* Logique métier (retard en minutes)
* Capacité à livrer une application fonctionnelle

---

## 📌 Point clé à retenir

> Le cœur du projet n’est PAS le modèle ML
> 👉 c’est la **reconstruction fiable du retard**

Sans cette étape :

* pas d’analyse
* pas de prédiction
* pas de valeur métier

---




