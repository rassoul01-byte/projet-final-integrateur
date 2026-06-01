# =============================================================
# import_invalides.py — Import des données invalides
# depuis donnees_sales.csv vers PostgreSQL
# =============================================================

import csv
import sys
from datetime import datetime
from database import get_connection, get_cursor

CSV_PATH = "../data/donnees_sales.csv"

def parse_date(date_str):
    if not date_str:
        return None
    for fmt in ("%d/%m/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(date_str.strip(), fmt).date()
        except ValueError:
            continue
    return None

def etudiant_existe(cursor, numero):
    cursor.execute("SELECT 1 FROM invalides WHERE numero = %s", (numero,))
    return cursor.fetchone() is not None

def importer():
    conn = get_connection()
    cursor = get_cursor(conn)
    inseres = 0
    ignores = 0
    erreurs = 0

    try:
        with open(CSV_PATH, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                numero = row.get("numero", "").strip()
                if not numero:
                    ignores += 1
                    continue

                if etudiant_existe(cursor, numero):
                    print(f"  [SKIP] {numero} — déjà en base")
                    ignores += 1
                    continue

                try:
                    cursor.execute("""
                        INSERT INTO invalides
                            (numero, code, prenom, nom, date_naissance,
                             classe, notes, erreurs)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        numero,
                        row.get("code", "").strip(),
                        row.get("prenom", "").strip(),
                        row.get("nom", "").strip(),
                        parse_date(row.get("date_naissance", "")),
                        row.get("classe", "").strip(),
                        row.get("notes", ""),
                        row.get("erreurs", ""),
                    ))
                    inseres += 1
                    print(f"  [OK]   {numero} — {row['prenom']} {row['nom']}")
                except Exception as e:
                    print(f"  [ERR]  {numero} — {e}")
                    erreurs += 1
                    conn.rollback()

        conn.commit()
    except FileNotFoundError:
        print(f"Fichier introuvable : {CSV_PATH}")
        sys.exit(1)
    finally:
        cursor.close()
        conn.close()

    print()
    print("=" * 40)
    print(f"  Insérés  : {inseres}")
    print(f"  Ignorés  : {ignores}")
    print(f"  Erreurs  : {erreurs}")
    print("=" * 40)

if __name__ == "__main__":
    importer()