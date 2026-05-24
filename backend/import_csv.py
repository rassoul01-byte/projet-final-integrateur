
import csv
import ast
import sys
from datetime import datetime
from database import get_connection, get_cursor

CSV_PATH = "../data/donnees_propres.csv"

def parse_date(date_str):
    if not date_str:
        return None
    for fmt in ("%d/%m/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(date_str.strip(), fmt).date()
        except ValueError:
            continue
    return None

def get_or_create_classe(cursor, nom_classe):
    cursor.execute("SELECT id FROM classes WHERE nom = %s", (nom_classe,))
    row = cursor.fetchone()
    if row:
        return row["id"]
    cursor.execute("INSERT INTO classes (nom) VALUES (%s) RETURNING id", (nom_classe,))
    return cursor.fetchone()["id"]

def etudiant_existe(cursor, numero):
    cursor.execute("SELECT 1 FROM etudiants WHERE numero = %s", (numero,))
    return cursor.fetchone() is not None

def inserer_etudiant(cursor, row):
    notes_dict = ast.literal_eval(row["notes"])
    matieres = []
    for nom_mat, data in notes_dict.items():
        matieres.append({
            "nom": nom_mat,
            "note_examen": float(data.get("examen", 0)),
            "moyenne": float(data.get("moyenne", 0)),
            "devoirs": [float(n) for n in data.get("devoirs", [])],
        })
    moyenne_generale = round(sum(m["moyenne"] for m in matieres) / len(matieres), 2) if matieres else 0.0
    classe_id = get_or_create_classe(cursor, row["classe"].strip())
    cursor.execute("""
        INSERT INTO etudiants (numero, code, prenom, nom, date_naissance, classe_id, moyenne_generale)
        VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id
    """, (row["numero"].strip(), row["code"].strip(), row["prenom"].strip(),
          row["nom"].strip(), parse_date(row.get("date_naissance", "")), classe_id, moyenne_generale))
    etudiant_id = cursor.fetchone()["id"]
    for mat in matieres:
        cursor.execute("""
            INSERT INTO matieres (etudiant_id, nom, note_examen, moyenne)
            VALUES (%s, %s, %s, %s) RETURNING id
        """, (etudiant_id, mat["nom"], mat["note_examen"], mat["moyenne"]))
        matiere_id = cursor.fetchone()["id"]
        for note in mat["devoirs"]:
            cursor.execute("INSERT INTO notes_devoir (matiere_id, note) VALUES (%s, %s)", (matiere_id, note))

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
                    print(f"  [SKIP] {numero}")
                    ignores += 1
                    continue
                try:
                    inserer_etudiant(cursor, row)
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
    print(f"  Inseres  : {inseres}")
    print(f"  Ignores  : {ignores}")
    print(f"  Erreurs  : {erreurs}")
    print("=" * 40)

if __name__ == "__main__":
    importer()
