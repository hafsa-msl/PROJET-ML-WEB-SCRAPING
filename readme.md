# 🚍 Prédiction des Retards - Réseau Fil Bleu Tours

Projet de Machine Learning appliqué aux transports en commun.

## 📋 Objectif

Prédire les retards sur le réseau Fil Bleu (Tours) pour aider les usagers à mieux planifier leurs trajets.

## 📊 Données

- **Source** : API GTFS-RT Fil Bleu
- **Méthode** : Web scraping temps réel
- **Format** : Protocol Buffers → CSV

## 🛠️ Technologies

- Python 3.8+
- Pandas, NumPy
- Scikit-learn, XGBoost
- Streamlit (application web)

## 🚀 Installation
```bash
pip install -r requirements.txt
```

## 📁 Structure
```
MACHINE LEARNING/
├── app/              # Application Streamlit
├── data/             # Données
│   ├── raw/          # Données brutes
│   ├── processed/    # Données nettoyées
│   └── final/        # Dataset ML
├── src/              # Code source
│   ├── scraping/     # Scripts de collecte
│   └── ml/           # Scripts ML
└── test/             # Tests
```



## Méthodologie de collecte

### Approche hybride retenue

**Contraintes identifiées :**
- Collecte continue 24/7 nécessite infrastructure serveur
- Délai projet : 3 semaines
- Volume de données : besoin de milliers d'exemples pour le ML

**Solution mise en place :**

1. **Collecte temps réel ponctuelle (validation)**
   - 10 collectes réparties sur 2 jours
   - Heures de pointe : 7h-9h et 17h-19h
   - Objectif : observer les patterns réels de retards

2. **Base de données GTFS statique**
   - 1 469 821 horaires théoriques
   - Structure complète du réseau (2 146 arrêts, 44 lignes)

3. **Simulation calibrée**
   - Génération de retards basée sur les observations réelles
   - Paramètres : heure, jour, ligne, arrêt
   - Dataset final : 50 000+ passages avec retards simulés

**Justification :**
Cette approche permet de :
- Démontrer la maîtrise du web scraping API (GTFS-RT)
- Obtenir un dataset exploitable dans les délais
- Valider les simulations par des données réelles
- Approche utilisée en industrie (data augmentation)
- 
## 👤 Auteur

Hafsa Mousalli
Imane Lemkhayer
