"""
Script de téléchargement des données GTFS statiques de Fil Bleu
"""

import requests
import zipfile
import os
from pathlib import Path

def download_gtfs():
    """
    Télécharge et extrait les données GTFS de Fil Bleu
    """
    print("🚀 Début du téléchargement des données GTFS Fil Bleu...")
    
    # URL des données GTFS (à vérifier sur transport.data.gouv.fr)
    url = "https://data.tours-metropole.fr/api/datasets/1.0/toursmetropole-transport-filbleu-gtfs/attachments/filbleu_gtfs_zip/"
    
    # Dossier de destination
    output_dir = Path("data/raw/gtfs")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    zip_path = output_dir / "filbleu_gtfs.zip"
    
    try:
        # Téléchargement
        print(f"📥 Téléchargement depuis : {url}")
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        # Sauvegarde du fichier ZIP
        with open(zip_path, 'wb') as f:
            f.write(response.content)
        
        print(f"✅ Fichier téléchargé : {zip_path}")
        
        # Extraction
        print("📂 Extraction des fichiers...")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(output_dir)
        
        print(f"✅ Fichiers extraits dans : {output_dir}")
        
        # Liste des fichiers extraits
        print("\n📋 Fichiers GTFS disponibles :")
        for file in sorted(output_dir.glob("*.txt")):
            print(f"  - {file.name}")
        
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Erreur lors du téléchargement : {e}")
        return False
    except zipfile.BadZipFile:
        print(f"❌ Erreur : Le fichier téléchargé n'est pas un ZIP valide")
        return False
    except Exception as e:
        print(f"❌ Erreur inattendue : {e}")
        return False

if __name__ == "__main__":
    success = download_gtfs()
    if success:
        print("\n Téléchargement terminé avec succès !")
    else:
        print("\n Le téléchargement a échoué. Vérifiez l'URL ou votre connexion.")