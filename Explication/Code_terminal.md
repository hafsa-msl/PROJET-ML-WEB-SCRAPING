📋 Fiche de procédure : Exécution du Projet

# Se placer dans le répertoire du projet
cd "C:\Users\pc\Cours\M2\S1\Module 2\Webscraping\PROJET-ML-WEB-SCRAPING"

# Étape 1 : Collecte des données (Scraping)
python src/scraping/scrape_gtfs_rt.py

Résultat attendu : Des fichiers bruts apparaissent dans data/raw/gtfs_rt/

# Étape 2 : Transfo des fichiers .bin en .csv

python src/scraping/parse_gtfs_rt.py

Résultat attendu : Des fichiers CSV apparaissent dans data/processed/gtfs_rt/

# Étape 3 : Analyser et Calcul des Retards

python src/scraping/calculate_delays.py

Résultat attendu : Un fichier delays.csv apparaît dans data/processed/gtfs_rt/

# Étape 4 : Visualisation des Données statiques

python src/scraping/explore_gtfs.py

# Etape 5 : Préparation des Données pour le Modèle

python src/ml/prepare_dataset.py

# Étape 6 : Entraînement du Modèle

python src/ml/train_model.py

# Etape 7: App

Streamlit run app/app.py
