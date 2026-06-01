# =============================================================
# routes/invalides.py — Routes pour les données invalides
# Préfixe : /api/v1
# =============================================================

from fastapi import APIRouter, HTTPException
from database import get_connection, get_cursor
import ast
from datetime import datetime

router = APIRouter()


# -------------------------------------------------------------
# Route : GET /api/v1/invalides
# Liste des étudiants invalides
# -------------------------------------------------------------
@router.get("/invalides")
def get_invalides():
    conn = get_connection()
    cursor = get_cursor(conn)

    try:
        cursor.execute("""
            SELECT id, numero, code, prenom, nom,
                   date_naissance, classe, erreurs, corrige
            FROM invalides
            ORDER BY corrige, nom, prenom
        """)
        rows = cursor.fetchall()

        return [
            {
                "id":             row["id"],
                "numero":         row["numero"],
                "code":           row["code"],
                "prenom":         row["prenom"],
                "nom":            row["nom"],
                "date_naissance": str(row["date_naissance"]) if row["date_naissance"] else None,
                "classe":         row["classe"],
                "erreurs":        row["erreurs"],
                "corrige":        row["corrige"],
            }
            for row in rows
        ]

    finally:
        cursor.close()
        conn.close()


# -------------------------------------------------------------
# Route : PUT /api/v1/invalides/{id}
# Corriger un étudiant invalide
# -------------------------------------------------------------
@router.put("/invalides/{invalide_id}")
def corriger_invalide(invalide_id: int, data: dict):
    conn = get_connection()
    cursor = get_cursor(conn)

    try:
        cursor.execute("""
            UPDATE invalides
            SET numero = %s, code = %s, prenom = %s, nom = %s,
                date_naissance = %s, classe = %s, corrige = TRUE
            WHERE id = %s
        """, (
            data.get("numero"),
            data.get("code"),
            data.get("prenom"),
            data.get("nom"),
            data.get("date_naissance"),
            data.get("classe"),
            invalide_id,
        ))
        conn.commit()
        return {"message": "Étudiant corrigé avec succès"}

    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()


# -------------------------------------------------------------
# Route : POST /api/v1/invalides/{id}/transferer
# Transférer un invalide corrigé vers la table etudiants
# -------------------------------------------------------------
@router.post("/invalides/{invalide_id}/transferer")
def transferer_invalide(invalide_id: int):
    conn = get_connection()
    cursor = get_cursor(conn)

    try:
        # Récupérer l'invalide
        cursor.execute("SELECT * FROM invalides WHERE id = %s", (invalide_id,))
        inv = cursor.fetchone()

        if not inv:
            raise HTTPException(status_code=404, detail="Invalide non trouvé")

        # Vérifier doublon dans etudiants
        cursor.execute(
            "SELECT 1 FROM etudiants WHERE numero = %s", (inv["numero"],)
        )
        if cursor.fetchone():
            raise HTTPException(
                status_code=400,
                detail=f"Un étudiant avec le numéro {inv['numero']} existe déjà"
            )

        # Récupérer ou créer la classe
        cursor.execute("SELECT id FROM classes WHERE nom = %s", (inv["classe"],))
        classe = cursor.fetchone()
        if not classe:
            cursor.execute(
                "INSERT INTO classes (nom) VALUES (%s) RETURNING id",
                (inv["classe"],)
            )
            classe_id = cursor.fetchone()["id"]
        else:
            classe_id = classe["id"]

        # Calculer moyenne générale depuis les notes
        moyenne_generale = None
        try:
            notes_dict = ast.literal_eval(inv["notes"])
            moyennes = [v["moyenne"] for v in notes_dict.values()]
            moyenne_generale = round(sum(moyennes) / len(moyennes), 2)
        except Exception:
            pass

        # Insérer dans etudiants
        cursor.execute("""
            INSERT INTO etudiants
                (numero, code, prenom, nom, date_naissance,
                 classe_id, moyenne_generale)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            inv["numero"], inv["code"], inv["prenom"], inv["nom"],
            inv["date_naissance"], classe_id, moyenne_generale,
        ))
        etudiant_id = cursor.fetchone()["id"]

        # Insérer les matières et notes
        try:
            notes_dict = ast.literal_eval(inv["notes"])
            for nom_mat, data in notes_dict.items():
                cursor.execute("""
                    INSERT INTO matieres (etudiant_id, nom, note_examen, moyenne)
                    VALUES (%s, %s, %s, %s) RETURNING id
                """, (
                    etudiant_id, nom_mat,
                    float(data.get("examen", 0)),
                    float(data.get("moyenne", 0))
                ))
                matiere_id = cursor.fetchone()["id"]
                for note in data.get("devoirs", []):
                    cursor.execute(
                        "INSERT INTO notes_devoir (matiere_id, note) VALUES (%s, %s)",
                        (matiere_id, float(note))
                    )
        except Exception:
            pass

        # Marquer comme corrigé et transféré
        cursor.execute(
            "UPDATE invalides SET corrige = TRUE WHERE id = %s",
            (invalide_id,)
        )

        conn.commit()
        return {"message": "Étudiant transféré avec succès", "id": etudiant_id}

    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()