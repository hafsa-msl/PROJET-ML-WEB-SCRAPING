# 📘 GUIDE DU PROJET - Prédiction des Retards Fil Bleu


## 🎯 Objectif du Projet

Créer une application qui prédit les retards des bus/trams de Fil Bleu (Tours) en utilisant le Machine Learning.

**Pipeline complet :**
```
Collecte données → Calcul des retards → Préparation → ML → Application Streamlit
```

---

## 📁 Structure du Projet
```
Machine Learning/
│
├── README.md                    # Documentation officielle (pour le rapport)
├── EXPLICATION.md               # Ce fichier (guide pour nous)
├── requirements.txt             # Bibliothèques Python nécessaires
│
├── data/
│   ├── raw/                     # ⚠️ NE JAMAIS MODIFIER CES FICHIERS !
│   │   ├── gtfs/                # Horaires théoriques du réseau
│   │   │   ├── stops.txt        # 2 146 arrêts
│   │   │   ├── routes.txt       # 44 lignes
│   │   │   ├── stop_times.txt   # 1 469 821 horaires programmés
│   │   │   └── ...
│   │   │
│   │   └── gtfs_rt/             # Données temps réel collectées
│   │       ├── trip_updates_20251212_223805.bin  (160 fichiers)
│   │       └── ...
│   │
│   ├── processed/               # Données transformées
│   │   ├── gtfs_rt_parsed.csv         # Données .bin converties en CSV
│   │   └── delays_calculated.csv      # 🎯 Dataset final avec retards calculés
│   │
│   └── final/                   # Dataset ML prêt (à créer)
│
├── src/
│   ├── scraping/                # Scripts de collecte
│   │   ├── download_gtfs.py           # Télécharge GTFS statique
│   │   ├── explore_gtfs.py            # Explore les données GTFS
│   │   ├── scrape_gtfs_rt.py          # Collecte API temps réel
│   │   ├── parse_gtfs_rt.py           # Convertit .bin → CSV
│   │   └── calculate_delays.py        # 🔥 CALCULE LES RETARDS RÉELS
│   │
│   └── ml/                      # Scripts ML (à créer)
│
└── app/                         # Application Streamlit (à créer)
```

---

## 📊 Les Données Collectées

### GTFS Statique (horaires théoriques)

**Où :** `data/raw/gtfs/`  
**Format :** Fichiers .txt (CSV)  
**Ce que c'est :** Les horaires "normaux" affichés aux arrêts

**Fichiers importants :**
- `stops.txt` : Liste des 2 146 arrêts avec coordonnées GPS
- `routes.txt` : Liste des 44 lignes (Tram A, Bus 1-70, etc.)
- `stop_times.txt` : 1 469 821 horaires programmés (qui passe où et quand)
- `trips.txt` : Informations sur les trajets

---

### GTFS-RT (temps réel)

**Où :** `data/raw/gtfs_rt/`  
**Format :** Fichiers .bin (Protocol Buffers - format binaire)  
**Ce que c'est :** L'heure RÉELLE de passage des bus (collectée en direct)

**Collecte effectuée :**
- **Samedi 13/12** : 155 fichiers (12h40 → 21h00)
- **Lundi 15/12** : 3 fichiers (18h33)
- **Vendredi 12/12** : 2 fichiers (22h38, 23h02)
- **Total : 160 fichiers = 291 699 passages**

**Nom des fichiers :**
```
trip_updates_20251213_150053.bin
             ^^^^^^^^  ^^^^^^
             Date      Heure (15h00:53)
```

---

## 🔧 Les Scripts et leur Rôle

### 1. `explore_gtfs.py` - Explorer le réseau

**Ce qu'il fait :**
- Charge les fichiers GTFS statiques
- Affiche combien de lignes, arrêts, trajets
- Liste toutes les lignes du réseau

**Comment l'utiliser :**
```powershell
python src\scraping\explore_gtfs.py
```

**Résultat :**
```
🚏 Nombre d'arrêts : 2146
🚌 Nombre de lignes : 44
📍 Liste des lignes : Tram A, Bus 1, Bus 2...
```

---

### 2. `scrape_gtfs_rt.py` - Collecter les données temps réel

**Ce qu'il fait :**
- Se connecte à l'API Fil Bleu
- Récupère les horaires temps réel
- Sauvegarde dans `data/raw/gtfs_rt/`

**Test simple (1 collecte) :**
```powershell
python src\scraping\scrape_gtfs_rt.py
```

**Collecte continue (déjà faite) :**
- Samedi : collecte automatique pendant 8h
- Lundi : 3 collectes manuelles

---

### 3. `parse_gtfs_rt.py` - Convertir .bin en CSV

**Pourquoi ce script ?**

Les fichiers `.bin` sont **illisibles** :
```
��������trip_id��stop_id��...  ❌
```

Le parser les convertit en **CSV exploitable** :
```csv
trip_id,stop_id,arrival_time_unix,...  ✅
```

**Comment l'utiliser :**
```powershell
python src\scraping\parse_gtfs_rt.py
```

**Résultat :**
- Crée `data/processed/gtfs_rt_parsed.csv`
- 291 699 passages lisibles en CSV

---

### 4. `calculate_delays.py` - 🔥 CALCULER LES RETARDS

**⚠️ SCRIPT CRUCIAL !**

**Pourquoi il existe :**

L'API Fil Bleu envoie :
- ✅ Heure théorique (prévue) : `22:30:00`
- ✅ Heure réelle (actuelle) : `22:35:00`
- ❌ Mais PAS le retard calculé (toujours à `0`)

**→ On doit calculer nous-mêmes : Retard = Heure réelle - Heure théorique**

**Ce que fait le script :**
1. Charge GTFS statique (horaires théoriques)
2. Charge GTFS-RT parsé (horaires réels)
3. Fusionne les deux sur `trip_id` + `stop_id`
4. Calcule : `retard = heure_réelle - heure_théorique`
5. Corrige le fuseau horaire (UTC → Europe/Paris)

**Comment l'utiliser :**
```powershell
python src\scraping\calculate_delays.py
```

**Résultat :**
```
📊 STATISTIQUES DES RETARDS :
  Retard moyen : 4.93 minutes
  Retard médian : 1.92 minutes
  Retard max : 150.92 minutes
  Retard min : -19.08 minutes (en avance)
  
💾 Données sauvegardées : data/processed/delays_calculated.csv
```

---

## ✅ Ce Qui a Été Fait (État Actuel)

**Phase 1 : Collecte et traitement des données ✅ TERMINÉE**

- [x] Structure du projet créée
- [x] Bibliothèques Python installées (`pip install -r requirements.txt`)
- [x] Données GTFS statiques téléchargées (1.4M d'horaires)
- [x] Script d'exploration créé et testé
- [x] 160 fichiers temps réel collectés (291 699 passages)
- [x] Parser créé : .bin → CSV
- [x] **Retards calculés** : fusion GTFS + GTFS-RT
- [x] **Dataset final prêt** : `delays_calculated.csv`

**→ Progression : 40% du projet**

---

## 🚀 Prochaines Étapes

### Phase 2 : Préparation des données ML (À FAIRE)

**Objectif :** Transformer `delays_calculated.csv` en dataset exploitable pour le ML

**Tâches :**
1. **Feature engineering** :
   - Extraire l'heure (8h, 18h...)
   - Extraire le jour de la semaine (lundi, samedi...)
   - Créer variable "est_heure_pointe" (7h-9h, 17h-19h)
   - Encoder les variables catégorielles (ligne, arrêt)

2. **Nettoyage** :
   - Supprimer les retards aberrants (> 60 min = incidents)
   - Gérer les valeurs manquantes

3. **Split train/test** :
   - 80% entraînement
   - 20% test

---

### Phase 3 : Machine Learning (À FAIRE)

**Modèles à tester :**
1. Régression linéaire (baseline)
2. Random Forest
3. XGBoost

**Métriques :**
- MAE (erreur moyenne en minutes)
- RMSE
- R²

---

### Phase 4 : Application Streamlit (À FAIRE)

**Interface utilisateur :**
- Sélectionner ligne, arrêt, heure
- Afficher prédiction du retard
- Indicateur de risque (fluide / modéré / élevé)

---

## 💡 Commandes Utiles

**Voir la structure des dossiers :**
```powershell
tree /F
```

**Installer les bibliothèques (si pas fait) :**
```powershell
pip install -r requirements.txt
```

**Lancer un script :**
```powershell
python src\scraping\nom_du_script.py
```

**Voir les données collectées :**
```powershell
import pandas as pd
df = pd.read_csv('data/processed/delays_calculated.csv')
print(df.head())
```

---

## 🎓 Points Importants pour le Rapport

### Justification de l'approche

**Problème rencontré :**
L'API GTFS-RT de Fil Bleu ne fournit pas les retards calculés (champ `delay` toujours à `0`).

**Solution implémentée :**
Calcul manuel des retards en fusionnant :
- Horaires théoriques (GTFS statique `stop_times.txt`)
- Horaires réels (GTFS-RT `arrival_time_unix`)
- Gestion du fuseau horaire Europe/Paris (+1h par rapport à UTC)

**Résultat :**
- 291 699 passages avec retards calculés
- Retard moyen : 4.93 minutes
- Distribution réaliste (médiane 1.92 min, max 150 min)

**Compétences démontrées :**
- Web scraping API temps réel
- Parsing de formats complexes (Protocol Buffers)
- Fusion de datasets hétérogènes
- Calculs temporels avec fuseaux horaires

---

## ⚠️ Points d'Attention

1. **Ne JAMAIS modifier `data/raw/`** : Ce sont les données originales
2. **Les timestamps sont en UTC** : Toujours convertir en Europe/Paris
3. **Le champ `delay` de l'API est inutile** : Toujours à 0, on calcule nous-mêmes
4. **Les retards > 60 min sont souvent des incidents** : À filtrer pour le ML

---

## 📊 Statistiques Finales

**Données collectées :**
- 160 snapshots temporels
- 291 699 passages enregistrés
- Sur 2 jours (samedi + lundi)

**Retards calculés :**
- Retard moyen : 4.93 min
- Retard médian : 1.92 min
- 95% des retards entre -2 et +15 min

---

**État actuel : 40% du projet terminé**  
**Prochaine étape : Feature engineering + ML**  
**Deadline : Début janvier 2025**