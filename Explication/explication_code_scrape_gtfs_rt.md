# 1️⃣ Les "Outils" (Imports)

📍 Rôle : Préparer les accessoires nécessaires au script.
- requests : bibliothèque standard en Python pour communiquer avec le monde extérieur via internet. Il va chercher les données sur le web.
- pandas : Importer et transformer les données
- datetime / time : La montre et le chrono. Pour savoir l'heure et gérer les pauses.

- pathlib : Pour créer les dossiers et ranger les fichiers au bon endroit.

# 📍 Scrapping données de trajets = trip_updates 
## Création d'une fonction pour aller chercher les données

- def scrape_trip_updates()= fonction principale qui va chercher les données de trajets en temps réel= arrets et horaires de passage 
ex: le bus 20 est passé à l'arrêt X à 14h30

- url= "https://data.filbleu.fr/ws-tr/gtfs-rt/opendata/trip-updates" = adresse web où se trouvent les données de trajets en temps réel.

- try: =permet au code de tester quelque chose
    print(f"Requête vers l'API GTFS-RT Updates")
    response = requests.get(url, timeout=10)= permet au code de tester quelque chose
    response.raise_for_status()= Cette ligne vérifie si le serveur de Tours a bien donné l'accès. Si le serveur répond "Erreur" ou "Accès refusé", cette ligne le détecte immédiatement pour éviter de travailler avec un fichier vide.

## Etape de vérification de la réponse du serveur

- print(f" Réponse reçue : {response.status_code}")= Si ça affiche 200, c'est "Vert" : la connexion a réussi. Si ça affiche 429 (ton erreur de tout à l'heure), c'est "Rouge" : le serveur te demande d'arrêter car tu as fait trop de requêtes.

- print(f"Taille : {len(response.content)} bytes")= la taille du fichier reçu. Ça permet de vérifier si le fichier contient vraiment des données. Si la taille est de 0 bytes, c'est que le fichier est vide (il y a eu un problème). Si elle est de plusieurs milliers de bytes, c'est qu'on a bien récupéré les données des bus.

- print(f"Content-Type : {response.headers.get('Content-Type')}")= Ça confirme la nature du fichier. Pour Fil Bleu, il doit t'afficher quelque chose qui contient x-protobuf

Ces trois lignes sont tes outils de contrôle. Elles ne servent pas à collecter la donnée, mais à vérifier la qualité de ce qui vient d'arriver sur ton ordinateur

## Etape du stockage des données

- timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")= demande à l'ordinateur l'heure exacte à la seconde près. Le format bizarre (%Y%m%d...) permet d'écrire la date comme ceci : 20251226_125030 (26 décembre 2025 à 12h 50min 30s)

- output_dir = Path("data/raw/gtfs_rt")= chemin où le fichier sera stocké. Ici, on crée un dossier "data", puis un sous-dossier "raw", puis un sous-sous-dossier "gtfs_rt"

- output_dir.mkdir(parents=True, exist_ok=True)= vérifie si le dossier existe déjà. Si ce n'est pas le cas, il le crée. parents=True permet de créer aussi les dossiers parents s'ils n'existent pas (data et raw). exist_ok=True évite de générer une erreur si le dossier existe déjà.
        
- output_file = output_dir / f"trip_updates_{timestamp}.bin" = nom du fichier. Il sera nommé "trip_updates_20251226_125030.bin" par exemple.
        
- with open(output_file, 'wb') as f:= ouvre le fichier en mode écriture binaire (wb = write binary). Le mode binaire est nécessaire car les données sont au format protobuf, qui n'est pas du texte classique.
    f.write(response.content)= écrit les données reçues dans le fichier. 
        
- print(f"Données sauvegardées : {output_file}")= affiche un message de confirmation avec le chemin complet du fichier sauvegardé.
        
- return True= indique que la fonction s'est bien déroulée jusqu'au bout.

- except requests.exceptions.RequestException as e:= capture les erreurs liées à la requête HTTP (problème de connexion, timeout, etc.)

- print(f"Erreur lors de la requête : {e}")= affiche un message d'erreur détaillé.
    return False= indique que la fonction a rencontré un problème.

-except Exception as e:= capture toute autre erreur inattendue.
    print(f"Erreur inattendue : {e}")
    return False

## Conclusion code
- La fonction scrape_trip_updates() est conçue pour aller chercher les données de trajets en temps réel depuis l'API GTFS-RT de Fil Bleu, vérifier la qualité de la réponse, et sauvegarder les données dans un fichier local avec un nom horodaté. Elle gère également les erreurs potentielles lors de la requête HTTP.

# 📍Scraping données de positions = vehicle_positions
## Création d'une fonction pour aller chercher les données

- def scrape_vehicle_positions()= fonction principale qui va chercher les données de positions en temps réel= position géographique des bus 
ex: le bus 20 est à tel endroit à 14h30

- url= "https://data.filbleu.fr/ws-tr/gtfs-rt/opendata/vehicle-positions" = adresse web où se trouvent les données de positions en temps réel.

- try: =permet au code de tester quelque chose
    print(f"Requête vers l'API GTFS-RT Vehicle Positions")
    response = requests.get(url, timeout=10)= permet au code de tester quelque chose
    response.raise_for_status()= Cette ligne vérifie si le serveur de Tours a bien donné l'accès. Si le serveur répond "Erreur" ou "Accès refusé", cette ligne le détecte immédiatement pour éviter de travailler avec un fichier vide.

## Etape de vérification de la réponse du serveur

- print(f" Réponse reçue : {response.status_code}")= Si ça affiche 200, c'est "Vert" : la connexion a réussi. Si ça affiche 429 (ton erreur de tout à l'heure), c'est "Rouge" : le serveur te demande d'arrêter car tu as fait trop de requêtes.

- print(f"Taille : {len(response.content)} bytes")= la taille du fichier reçu. Ça permet de vérifier si le fichier contient vraiment des données. Si la taille est de 0 bytes, c'est que le fichier est vide (il y a eu un problème). Si elle est de plusieurs milliers de bytes, c'est qu'on a bien récupéré les données des bus.

- print(f"Content-Type : {response.headers.get('Content-Type')}")= Ça confirme la nature du fichier. Pour Fil Bleu, il doit t'afficher quelque chose qui contient x-protobuf

Ces trois lignes sont tes outils de contrôle. Elles ne servent pas à collecter la donnée, mais à vérifier la qualité de ce qui vient d'arriver sur ton ordinateur

## Etape du stockage des données

- timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")= demande à l'ordinateur l'heure exacte à la seconde près. Le format bizarre (%Y%m%d...) permet d'écrire la date comme ceci : 20251226_125030 (26 décembre 2025 à 12h 50min 30s)

- output_dir = Path("data/raw/gtfs_rt")= chemin où le fichier sera stocké. Ici, on crée un dossier "data", puis un sous-dossier "raw", puis un sous-sous-dossier "gtfs_rt"

- output_dir.mkdir(parents=True, exist_ok=True)= vérifie si le dossier existe déjà. Si ce n'est pas le cas, il le crée. parents=True permet de créer aussi les dossiers parents s'ils n'existent pas (data et raw). exist_ok=True évite de générer une erreur si le dossier existe déjà.

- output_file = output_dir / f"vehicle_positions_{timestamp}.bin" = nom du fichier. Il sera nommé "vehicle_positions_20251226_125030.bin" par exemple.

- with open(output_file, 'wb') as f:= ouvre le fichier en mode écriture binaire (wb = write binary). Le mode binaire est nécessaire car les données sont au format protobuf, qui n'est pas du texte classique.
    f.write(response.content)= écrit les données reçues dans le fichier.
- print(f"Données sauvegardées : {output_file}")= affiche un message de confirmation avec le chemin complet du fichier sauvegardé.
- return True= indique que la fonction s'est bien déroulée jusqu'au bout.
- except requests.exceptions.RequestException as e:= capture les erreurs liées à la requête HTTP (problème de connexion, timeout, etc.)
    print(f"Erreur lors de la requête : {e}")= affiche un message d'erreur détaillé.
    return False= indique que la fonction a rencontré un problème.
-except Exception as e:= capture toute autre erreur inattendue.
    print(f"Erreur inattendue : {e}")
    return False

## Conclusion code
- La fonction scrape_vehicle_positions() est conçue pour aller chercher les données de positions en temps réel depuis l'API GTFS-RT de Fil Bleu, vérifier la qualité de la réponse, et sauvegarder les données dans un fichier local avec un nom horodaté. Elle gère également les erreurs potentielles lors de la requête HTTP.



## Création d'une fonction pour collecter les données de manière continue

- def collecte_continue(duree_minutes=5, intervalle_secondes=60):= fonction qui permet de collecter les données de manière continue pendant une durée définie (duree_minutes) avec un intervalle entre chaque collecte (intervalle_secondes).

- print("="*60)= affiche une ligne de séparation pour la lisibilité dans la console.

- print(" DÉBUT DE LA COLLECTE CONTINUE")= affiche un message indiquant le début de la collecte continue.

- print("="*60)= affiche une ligne de séparation pour la lisibilité dans la console.

- print(f" Durée : {duree_minutes} minutes")= affiche la durée totale de la collecte continue.

- print(f"Intervalle : {intervalle_secondes} secondes")= affiche l'intervalle entre chaque collecte.

-print(f" Début : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")= affiche l'heure de début de la collecte.

- print("="*60)= affiche une ligne de séparation pour la lisibilité dans la console.
    
- debut = time.time()= enregistre le temps de début de la collecte en secondes depuis l'époque (1er janvier 1970).

- fin = debut + (duree_minutes * 60)= calcule le temps de fin de la collecte en ajoutant la durée totale (en secondes) au temps de début.

- collecte_num = 1 = initialise un compteur pour le nombre de collectes effectuées.
    
- while time.time() < fin: = boucle qui continue tant que le temps actuel est inférieur au temps de fin.
        
- print(f"\n\n{'='*60}")= affiche une ligne de séparation pour la lisibilité dans la console.

- print(f" COLLECTE #{collecte_num}")= affiche le numéro de la collecte en cours.

- print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")= affiche l'heure actuelle.

- print('='*60) = affiche une ligne de séparation pour la lisibilité dans la console.
        

## Collecter les retards

- success1 = scrape_trip_updates()= appelle la fonction scrape_trip_updates() pour collecter les données de trajets et stocke le résultat (True ou False) dans la variable success1.
        
## Collecter les positions

- success2 = scrape_vehicle_positions()= appelle la fonction scrape_vehicle_positions() pour collecter les données de positions et stocke le résultat (True ou False) dans la variable success2.

        
- if success1 and success2: = vérifie si les deux collectes ont réussi.

- print(f"\n Collecte #{collecte_num} réussie !") = affiche un message indiquant que la collecte a réussi.

- else:

- if not success1 and not success2: = vérifie si les deux collectes ont échoué.

- print(f"\n Collecte #{collecte_num} échouée !") = affiche un message indiquant que la collecte a échoué.
        else:
            print(f"\n Collecte #{collecte_num} partiellement réussie")
        
collecte_num += 1

## Attendre avant la prochaine collecte

- temps_restant = fin - time.time() = calcule le temps restant avant la fin de la collecte continue.

- if temps_restant > intervalle_secondes: = vérifie si le temps restant est supérieur à l'intervalle défini.

- print(f"\n Pause de {intervalle_secondes} secondes...") = affiche un message indiquant la pause avant la prochaine collecte.
        
- time.sleep(intervalle_secondes) = met le script en pause pendant l'intervalle défini.
        else:
            break
    
- print("\n\n" + "="*60)  = affiche une ligne de séparation pour la lisibilité dans la console.
    
- print(" COLLECTE TERMINÉE") = affiche un message indiquant la fin de la collecte continue.

- print("="*60) = affiche une ligne de séparation pour la lisibilité dans la console.

- print(f"Nombre de collectes : {collecte_num - 1}") = affiche le nombre total de collectes effectuées.

- print(f" Fin : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}") = affiche l'heure de fin de la collecte.

## Test des fonctions de scrapping

- if __name__ == "__main__": = permet d'exécuter le code suivant uniquement si le script est exécuté directement (et non importé comme module).

- print("\n TEST DE CONNEXION À L'API GTFS-RT\n") = affiche un message indiquant le début des tests de connexion à l'API GTFS-RT.
    
- print("Test 1 : Récupération des retards (trip_updates)")
    scrape_trip_updates()
    
- print("\n" + "="*60 + "\n")
    
- print("Test 2 : Récupération des positions (vehicle_positions)")
    scrape_vehicle_positions()
    
- print("\n\n" + "="*60)
- print(" Tests terminés !")
- print("="*60)
- print("\nPour lancer une collecte continue :")
- print("  Décommente la ligne 'collecte_continue()' en bas du fichier")
- print("  Ou lance : collecte_continue(duree_minutes=10, intervalle_secondes=60)")
    
- 
collecte_continue(duree_minutes=503, intervalle_secondes=180)
