"""
Script de scraping GTFS-RT (temps réel) de Fil Bleu
Collecte les retards et positions des véhicules
"""

import requests
import pandas as pd
from datetime import datetime
from pathlib import Path
import time

def scrape_trip_updates():
    """
    Récupère les retards en temps réel (trip_updates)
    """
    url = "https://data.filbleu.fr/ws-tr/gtfs-rt/opendata/trip-updates"
    
    try:
        print(f"Requête vers l'API GTFS-RT Updates")
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        print(f" Réponse reçue : {response.status_code}")
        print(f"Taille : {len(response.content)} bytes")
        print(f"Content-Type : {response.headers.get('Content-Type')}")
        
        # Sauvegarder la réponse brute
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = Path("data/raw/gtfs_rt")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        output_file = output_dir / f"trip_updates_{timestamp}.bin"
        
        with open(output_file, 'wb') as f:
            f.write(response.content)
        
        print(f"Données sauvegardées : {output_file}")
        
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"Erreur lors de la requête : {e}")
        return False
    except Exception as e:
        print(f"Erreur inattendue : {e}")
        return False

def scrape_vehicle_positions():
    """
    Récupère les positions des véhicules en temps réel
    """
    url = "https://data.filbleu.fr/ws-tr/gtfs-rt/opendata/vehicle-positions"
    
    try:
        print(f"\nRequête positions véhicules...")
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        print(f"Réponse reçue : {response.status_code}")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = Path("data/raw/gtfs_rt")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        output_file = output_dir / f"vehicle_positions_{timestamp}.bin"
        
        with open(output_file, 'wb') as f:
            f.write(response.content)
        
        print(f" Données sauvegardées : {output_file}")
        
        return True
        
    except requests.exceptions.RequestException as e:
        print(f" Erreur : {e}")
        return False

def collecte_continue(duree_minutes=5, intervalle_secondes=60):
    """
    Collecte en continu pendant une durée donnée
    
    Args:
        duree_minutes: Durée totale de collecte en minutes
        intervalle_secondes: Intervalle entre chaque collecte
    """
    print("="*60)
    print(" DÉBUT DE LA COLLECTE CONTINUE")
    print("="*60)
    print(f" Durée : {duree_minutes} minutes")
    print(f"Intervalle : {intervalle_secondes} secondes")
    print(f" Début : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    debut = time.time()
    fin = debut + (duree_minutes * 60)
    collecte_num = 1
    
    while time.time() < fin:
        print(f"\n\n{'='*60}")
        print(f" COLLECTE #{collecte_num}")
        print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print('='*60)
        
        # Collecter les retards
        success1 = scrape_trip_updates()
        
        # Collecter les positions
        success2 = scrape_vehicle_positions()
        
        if success1 and success2:
            print(f"\n Collecte #{collecte_num} réussie !")
        else:
            print(f"\n Collecte #{collecte_num} partiellement réussie")
        
        collecte_num += 1
        
        # Attendre avant la prochaine collecte
        temps_restant = fin - time.time()
        if temps_restant > intervalle_secondes:
            print(f"\n Pause de {intervalle_secondes} secondes...")
            time.sleep(intervalle_secondes)
        else:
            break
    
    print("\n\n" + "="*60)
    print(" COLLECTE TERMINÉE")
    print("="*60)
    print(f"Nombre de collectes : {collecte_num - 1}")
    print(f" Fin : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    print("\n TEST DE CONNEXION À L'API GTFS-RT\n")
    
    # Test simple
    print("Test 1 : Récupération des retards (trip_updates)")
    scrape_trip_updates()
    
    print("\n" + "="*60 + "\n")
    
    print("Test 2 : Récupération des positions (vehicle_positions)")
    scrape_vehicle_positions()
    
    print("\n\n" + "="*60)
    print(" Tests terminés !")
    print("="*60)
    print("\nPour lancer une collecte continue :")
    print("  Décommente la ligne 'collecte_continue()' en bas du fichier")
    print("  Ou lance : collecte_continue(duree_minutes=10, intervalle_secondes=60)")
    
collecte_continue(duree_minutes=503, intervalle_secondes=180)
