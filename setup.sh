#!/bin/bash
# =============================================================
# setup.sh — Installation automatique du projet
# Usage : bash setup.sh
# =============================================================

set -e  # Arrêter si une commande échoue

echo "============================================"
echo "   INSTALLATION — Gestion Étudiants"
echo "============================================"

# -------------------------------------------------------------
# 1. Vérifier Python
# -------------------------------------------------------------
echo ""
echo "[ 1/6 ] Vérification de Python..."
python3 --version || { echo "Python3 non installé"; exit 1; }

# -------------------------------------------------------------
# 2. Créer l'environnement virtuel
# -------------------------------------------------------------
echo ""
echo "[ 2/6 ] Création de l'environnement virtuel..."
python3 -m venv venv
echo "       OK — venv créé"

# -------------------------------------------------------------
# 3. Installer les dépendances Python
# -------------------------------------------------------------
echo ""
echo "[ 3/6 ] Installation des dépendances Python..."
source venv/bin/activate
pip install --quiet fastapi uvicorn psycopg2-binary python-dotenv pydantic
echo "       OK — dépendances installées"

# -------------------------------------------------------------
# 4. Vérifier le fichier .env
# -------------------------------------------------------------
echo ""
echo "[ 4/6 ] Vérification du fichier .env..."
if [ ! -f ".env" ]; then
    echo "       Création du fichier .env par défaut..."
    cat > .env << 'ENVEOF'
DB_HOST=localhost
DB_PORT=5432
DB_NAME=gestion_etudiants
DB_USER=postgres
DB_PASSWORD=postgres
ENVEOF
    echo "       OK — .env créé (modifiez les valeurs si besoin)"
else
    echo "       OK — .env existe déjà"
fi

# -------------------------------------------------------------
# 5. Créer la base de données PostgreSQL
# -------------------------------------------------------------
echo ""
echo "[ 5/6 ] Création de la base de données..."
sudo -u postgres psql -c "CREATE DATABASE gestion_etudiants;" 2>/dev/null \
    && echo "       OK — base créée" \
    || echo "       INFO — base déjà existante"

# Exécuter le schema
cp schema.sql /tmp/schema_gest.sql
chmod 644 /tmp/schema_gest.sql
sudo -u postgres psql -d gestion_etudiants -f /tmp/schema_gest.sql > /dev/null 2>&1
echo "       OK — tables créées"

# -------------------------------------------------------------
# 6. Importer les données
# -------------------------------------------------------------
echo ""
echo "[ 6/6 ] Import des données CSV..."
cd backend
python import_csv.py
cd ..

echo ""
echo "============================================"
echo "   INSTALLATION TERMINÉE !"
echo "   Lancez : bash run.sh"
echo "============================================"
