import pandas as pd
from pathlib import Path

def explore_gtfs():
    """
    Charge et affiche un aperçu des données GTFS
    """
    print("Exploration des données GTFS Fil Bleu\n")
    gtfs_dir = Path("data/raw/gtfs")
    fichiers = {
        'stops': 'Arrêts',
        'routes': 'Lignes',
        'trips': 'Trajets',
        'stop_times': 'Horaires',
        'calendar': 'Calendrier'}
    for fichier, description in fichiers.items():
        filepath = gtfs_dir / f"{fichier}.txt" #ici on construit le chemin du fichier
        if filepath.exists():
            print(f"\n{'='*60}")
            print(f"{description.upper()} ({fichier}.txt)") #ici on affiche le nom du fichier et sa description
            print('='*60)
            df = pd.read_csv(filepath)
            print(f"\nNombre de lignes : {len(df)}")
            print(f"Colonnes : {', '.join(df.columns.tolist())}")
            print(f"\nAperçu des premières lignes :")
            print(df.head(3))
        else:
            print(f"❌ Fichier non trouvé : {filepath}")
    
    print(f"\n\n{'='*60}")
    print("RÉSUMÉ DU RÉSEAU FIL BLEU")
    print('='*60) #ligne de séparation
    
    stops = pd.read_csv(gtfs_dir / "stops.txt")
    routes = pd.read_csv(gtfs_dir / "routes.txt")
    trips = pd.read_csv(gtfs_dir / "trips.txt")
    stop_times = pd.read_csv(gtfs_dir / "stop_times.txt")
    
    print(f"\nNombre total d'arrêts : {len(stops)}")
    print(f"Nombre de lignes : {len(routes)}")
    print(f"Nombre de trajets : {len(trips)}")
    print(f"Nombre d'horaires : {len(stop_times)}")
    
    print(f"\nListe des lignes :")
    for _, route in routes.iterrows():
        print(f"  - {route['route_short_name']} : {route['route_long_name']}")

if __name__ == "__main__":
    explore_gtfs()