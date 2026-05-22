# Gestion Étudiants — Application Web Complète

Application web professionnelle de gestion des données étudiants, construite avec **FastAPI**, **PostgreSQL** et **JavaScript vanilla**.

---

## Stack technique

| Couche | Technologie |
|--------|-------------|
| Backend | Python, FastAPI, Pydantic |
| Base de données | PostgreSQL, psycopg2, SQL manuel |
| Frontend | HTML, CSS, JavaScript (fetch) |
| Visualisation | Chart.js |
| Système | Linux, Bash |
| Versioning | Git, GitHub |

---

## Structure du projet

```
gestion_etudiants/
├── backend/
│   ├── main.py          # Point d'entrée FastAPI
│   ├── database.py      # Connexion PostgreSQL
│   ├── models.py        # Classes Python (POO)
│   ├── schemas.py       # Schémas Pydantic
│   └── routes/
│       ├── etudiants.py # Routes CRUD étudiants
│       └── stats.py     # Routes statistiques
├── frontend/
│   ├── index.html       # Interface principale
│   ├── dashboard.html   # Dashboard Chart.js
│   ├── style.css
│   └── app.js
├── data/
│   └── valides.json     # Données initiales (source secondaire)
├── schema.sql           # Script de création de la base
├── requirements.txt
├── .env                 # Variables d'environnement (non versionné)
└── .gitignore
```

---

## Installation

### Prérequis

- Python 3.10+
- PostgreSQL 14+
- Git

### 1. Cloner le dépôt

```bash
git clone https://github.com/<utilisateur>/gestion_etudiants.git
cd gestion_etudiants
```

### 2. Créer l'environnement virtuel

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Configurer la base de données

```bash
# Créer la base PostgreSQL
createdb gestion_etudiants

# Exécuter le script SQL
psql -d gestion_etudiants -f schema.sql
```

### 4. Configurer les variables d'environnement

Créer un fichier `.env` à la racine :

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=gestion_etudiants
DB_USER=postgres
DB_PASSWORD=votre_mot_de_passe
```

### 5. Lancer l'application

```bash
cd backend
uvicorn main:app --reload
```

L'API est disponible sur : `http://localhost:8000`  
Documentation interactive : `http://localhost:8000/docs`

---

## Fonctionnalités

### Gestion des données
- Affichage paginé (5 lignes par défaut)
- Recherche par numéro, code, nom/prénom
- Filtrage par classe et par source (DB / JSON)
- Ajout et modification inline (données DB uniquement)
- Archivage et restauration

### Sources de données
- **DB** : données provenant de PostgreSQL (modifiables)
- **JSON** : données provenant de `valides.json` (lecture seule)
- Import JSON → PostgreSQL avec détection des doublons

### Dashboard
- Indicateurs globaux (KPI)
- Répartition par classe et par source
- Moyenne générale par classe
- Top 10 des meilleures moyennes (Chart.js)

---

## API REST — Principales routes

| Méthode | Route | Description |
|---------|-------|-------------|
| GET | `/health` | Vérification du serveur |
| GET | `/etudiants` | Liste paginée des étudiants |
| GET | `/etudiants/{id}` | Détail d'un étudiant |
| POST | `/etudiants` | Ajouter un étudiant |
| PUT | `/etudiants/{id}` | Modifier un étudiant |
| PATCH | `/etudiants/{id}/archiver` | Archiver un étudiant |
| POST | `/etudiants/import-json` | Importer depuis JSON |
| GET | `/stats` | Statistiques globales |

---

## Auteur

Projet réalisé dans le cadre du cours **DEV DATA P8**.
