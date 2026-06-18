import os
import re
import glob
from datetime import datetime

import mysql.connector
from dotenv import load_dotenv

load_dotenv()

PATTERN = re.compile(
    r"(\d{4}-\d{2}-\d{2}) (\d{2}:\d{2}:\d{2}) - Température: (\d+)°C - Vibration: (\d+,\d+)"
)


def extraire_mesures(fichier: str) -> list[dict]:
    """Extrait les mesures d'un fichier texte de cage laminoir."""
    mesures = []
    with open(fichier, "r", encoding="utf-8") as f:
        for ligne in f:
            match = PATTERN.search(ligne)
            if match:
                date_str, heure_str, temp_str, vib_str = match.groups()
                mesures.append({
                    "fichier": fichier,
                    "datetime": datetime.strptime(f"{date_str} {heure_str}", "%Y-%m-%d %H:%M:%S"),
                    "temperature": int(temp_str),
                    "vibration": float(vib_str.replace(",", ".")),
                })
    return mesures


def etl_cages(fichiers: list[str]) -> dict[str, list[dict]]:
    """Traite une liste de fichiers de cages et retourne les mesures par cage."""
    resultats = {}
    for fichier in fichiers:
        mesures = extraire_mesures(fichier)
        resultats[fichier] = mesures
        print(f"{fichier} : {len(mesures)} mesures extraites.")
    return resultats


def get_connection():
    """Ouvre une connexion MySQL à partir des informations du fichier .env."""
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
    )


def charger_mesures(connection, toutes_mesures: dict[str, list[dict]]) -> int:
    """Insère les mesures extraites dans la table `mesures`. Retourne le nombre de lignes insérées."""
    cursor = connection.cursor()
    cursor.execute("SELECT id, nom FROM cages")
    cage_ids = {nom: id_ for id_, nom in cursor.fetchall()}

    requete = """
        INSERT IGNORE INTO mesures (cage_id, date_mesure, temperature, vibration)
        VALUES (%s, %s, %s, %s)
    """

    total_insere = 0
    for fichier, mesures in toutes_mesures.items():
        nom_cage = os.path.splitext(os.path.basename(fichier))[0]
        cage_id = cage_ids.get(nom_cage)
        if cage_id is None:
            print(f"Cage inconnue pour le fichier {fichier}, ignoré.")
            continue

        valeurs = [
            (cage_id, m["datetime"], m["temperature"], m["vibration"])
            for m in mesures
        ]
        cursor.executemany(requete, valeurs)
        total_insere += cursor.rowcount

    connection.commit()
    cursor.close()
    return total_insere


if __name__ == "__main__":
    fichiers = sorted(glob.glob("cage*.txt"))
    print(f"Fichiers détectés : {fichiers}\n")

    toutes_mesures = etl_cages(fichiers)

    total = sum(len(m) for m in toutes_mesures.values())
    print(f"\nTotal : {total} mesures extraites sur {len(fichiers)} fichiers.")

    connection = get_connection()
    inserees = charger_mesures(connection, toutes_mesures)
    connection.close()
    print(f"{inserees} nouvelles mesures insérées en base.")
