# Projet Cage Laminoir — ETL

## Contexte

Ce projet simule la collecte de données de surveillance (température et
vibration) issues des roulements des cages d'un train de laminage à chaud.
Chaque cage (`cage1.txt` à `cage6.txt`) génère un fichier de log brut, au
format suivant :

```
2026-05-21 11:38:30 - Température: 95°C - Vibration: 8,33
```

L'objectif du script `ETL.py` est d'**extraire** ces données depuis les
fichiers texte, de les **transformer** en types exploitables (datetime,
int, float), puis de les **charger** dans une base de données MySQL pour
permettre des analyses (datamarts, suivi en temps réel, etc.).

## Fonctionnement de l'ETL

### 1. Extraction (`extraire_mesures`)

- Une expression régulière (`PATTERN`) capture la date, l'heure, la
  température et la vibration de chaque ligne d'un fichier.
- Les lignes ne correspondant pas au format attendu sont silencieusement
  ignorées (logs corrompus, lignes vides, etc.).

### 2. Transformation

Chaque mesure valide est convertie dans un dictionnaire typé :

| Champ         | Type       | Origine                                    |
|---------------|------------|---------------------------------------------|
| `fichier`     | `str`      | nom du fichier source (traçabilité)         |
| `datetime`    | `datetime` | concaténation date + heure                  |
| `temperature` | `int`      | valeur en °C                                |
| `vibration`   | `float`    | virgule française convertie en point décimal |

### 3. Traitement multi-fichiers (`etl_cages`)

- La fonction prend en entrée une **liste de fichiers** et applique
  `extraire_mesures` à chacun.
- Elle retourne un dictionnaire `{ nom_fichier: [mesures] }`, ce qui permet
  de traiter un nombre quelconque de cages (6 actuellement, extensible à
  toute la ligne de laminage) sans dupliquer de code.
- Dans le bloc `__main__`, les fichiers sont détectés automatiquement via
  `glob.glob("cage*.txt")` : ajouter `cage7.txt` ne nécessite aucune
  modification du script.

### 4. Chargement (`charger_mesures`)

- Connexion à MySQL via `mysql.connector`, configurée par variables
  d'environnement (`.env`, voir ci-dessous).
- Le nom du fichier (sans extension, ex. `cage1`) sert à retrouver le
  `cage_id` correspondant dans la table `cages`.
- Les mesures sont insérées avec `INSERT IGNORE` : si une ligne existe déjà
  pour le couple `(cage_id, date_mesure)`, elle est ignorée. Cela rend le
  script **idempotent** : on peut le relancer plusieurs fois sur les mêmes
  fichiers sans créer de doublons, et seules les nouvelles mesures sont
  comptabilisées (`cursor.rowcount`).

## Format de la base de données

Voir [`init.sql`](init.sql) pour le script de création complet.

### Table `cages`

Table de référence listant les cages instrumentées.

| Colonne | Type         | Description              |
|---------|--------------|---------------------------|
| `id`    | `INT` (PK)   | identifiant auto-incrémenté |
| `nom`   | `VARCHAR(50)`| nom unique (`cage1`...`cage6`) |

Pré-remplie à l'initialisation pour que l'ETL puisse mapper directement un
nom de fichier vers un `cage_id`.

### Table `mesures`

Table de faits contenant l'ensemble des relevés.

| Colonne       | Type           | Description                              |
|---------------|----------------|--------------------------------------------|
| `id`          | `INT` (PK)     | identifiant auto-incrémenté                 |
| `cage_id`     | `INT` (FK)     | référence vers `cages.id`                   |
| `date_mesure` | `DATETIME`     | horodatage de la mesure                     |
| `temperature` | `INT`          | température en °C                           |
| `vibration`   | `DECIMAL(5,2)` | amplitude de vibration                      |

**Contraintes et index :**

- `fk_mesures_cage` : clé étrangère vers `cages(id)`, avec `ON DELETE
  CASCADE` (la suppression d'une cage supprime ses mesures).
- `uq_cage_date (cage_id, date_mesure)` : empêche les doublons et permet
  l'usage d'`INSERT IGNORE` lors du chargement.
- `idx_mesures_date` : accélère les requêtes filtrant/triant par date
  (suivi temps réel, agrégations par période).

## Configuration (`.env`)

Les identifiants de connexion à la base ne sont **jamais codés en dur**
dans `ETL.py` : ils sont chargés depuis un fichier `.env` (via
`python-dotenv`) à la racine du projet.

```
DB_HOST=localhost
DB_PORT=3307
DB_USER=root
DB_PASSWORD=monMotDePasse
DB_NAME=laminoir
```


## Utilisation

1. Créer la base et les tables :
   ```bash
   mysql -u root -p < init.sql
   ```
2. Renseigner les identifiants dans `.env`.
3. Installer les dépendances :
   ```bash
   pip install mysql-connector-python python-dotenv
   ```
4. Lancer l'ETL :
   ```bash
   python ETL.py
   ```

Le script affiche le nombre de mesures extraites par fichier, le total
extrait, puis le nombre de nouvelles lignes effectivement insérées en base.
