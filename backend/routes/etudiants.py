# =============================================================
# routes/etudiants.py — Routes CRUD pour les étudiants
# Logique source : JSON (lecture seule) / DB (modifiable)
# =============================================================

from fastapi import APIRouter, HTTPException, Query
from database import get_connection, get_cursor
from schemas import EtudiantCreate, PaginationResponse
import math

router = APIRouter()


# -------------------------------------------------------------
# Route : GET /api/v1/etudiants
# Liste paginée avec filtres + source DB/JSON
# -------------------------------------------------------------
@router.get("/etudiants", response_model=PaginationResponse)
def get_etudiants(
    page: int = Query(1, ge=1),
    par_page: int = Query(5, ge=1, le=100),
    search: str = Query("", description="Recherche nom/prenom/numero/code"),
    classe: str = Query("", description="Filtrer par classe"),
    source: str = Query("", description="Filtrer par source : DB ou JSON"),
):
    conn = get_connection()
    cursor = get_cursor(conn)

    try:
        conditions = ["e.archive = FALSE"]
        params = []

        if search:
            conditions.append("""
                (e.nom ILIKE %s OR e.prenom ILIKE %s
                 OR e.numero ILIKE %s OR e.code ILIKE %s)
            """)
            terme = f"%{search}%"
            params.extend([terme, terme, terme, terme])

        if classe:
            conditions.append("c.nom = %s")
            params.append(classe)

        # Filtre source DB / JSON
        if source in ("DB", "JSON"):
            conditions.append("e.source = %s")
            params.append(source)

        where = " AND ".join(conditions)

        # Compter le total
        cursor.execute(f"""
            SELECT COUNT(*) AS total
            FROM etudiants e
            LEFT JOIN classes c ON c.id = e.classe_id
            WHERE {where}
        """, params)
        total = cursor.fetchone()["total"]

        total_pages = max(1, math.ceil(total / par_page))
        offset = (page - 1) * par_page

        # Récupérer les données
        cursor.execute(f"""
            SELECT
                e.id, e.numero, e.code, e.prenom, e.nom,
                e.date_naissance, c.nom AS classe,
                e.moyenne_generale, e.archive, e.source
            FROM etudiants e
            LEFT JOIN classes c ON c.id = e.classe_id
            WHERE {where}
            ORDER BY e.nom, e.prenom
            LIMIT %s OFFSET %s
        """, params + [par_page, offset])

        rows = cursor.fetchall()

        etudiants = []
        for row in rows:
            etudiants.append({
                "id":               row["id"],
                "numero":           row["numero"],
                "code":             row["code"],
                "prenom":           row["prenom"],
                "nom":              row["nom"],
                "date_naissance":   row["date_naissance"],
                "classe":           row["classe"] or "",
                "moyenne_generale": row["moyenne_generale"],
                "archive":          row["archive"],
                "source":           row["source"] or "JSON",
            })

        return {
            "total":       total,
            "page":        page,
            "par_page":    par_page,
            "total_pages": total_pages,
            "data":        etudiants,
        }

    finally:
        cursor.close()
        conn.close()


# -------------------------------------------------------------
# Route : GET /api/v1/etudiants/{id}
# Détail d'un étudiant avec ses matières et notes
# -------------------------------------------------------------
@router.get("/etudiants/{etudiant_id}")
def get_etudiant(etudiant_id: int):
    conn = get_connection()
    cursor = get_cursor(conn)

    try:
        cursor.execute("""
            SELECT
                e.id, e.numero, e.code, e.prenom, e.nom,
                e.date_naissance, c.nom AS classe,
                e.moyenne_generale, e.archive, e.source
            FROM etudiants e
            LEFT JOIN classes c ON c.id = e.classe_id
            WHERE e.id = %s
        """, (etudiant_id,))

        etudiant = cursor.fetchone()
        if not etudiant:
            raise HTTPException(status_code=404, detail="Étudiant non trouvé")

        cursor.execute("""
            SELECT id, nom, note_examen, moyenne
            FROM matieres
            WHERE etudiant_id = %s
            ORDER BY nom
        """, (etudiant_id,))
        matieres = cursor.fetchall()

        matieres_list = []
        for mat in matieres:
            cursor.execute("""
                SELECT note FROM notes_devoir
                WHERE matiere_id = %s ORDER BY id
            """, (mat["id"],))
            devoirs = cursor.fetchall()
            matieres_list.append({
                "nom":          mat["nom"],
                "note_examen":  mat["note_examen"],
                "moyenne":      mat["moyenne"],
                "notes_devoir": [{"note": d["note"]} for d in devoirs],
            })

        return {
            "id":               etudiant["id"],
            "numero":           etudiant["numero"],
            "code":             etudiant["code"],
            "prenom":           etudiant["prenom"],
            "nom":              etudiant["nom"],
            "date_naissance":   etudiant["date_naissance"],
            "classe":           etudiant["classe"] or "",
            "moyenne_generale": etudiant["moyenne_generale"],
            "archive":          etudiant["archive"],
            "source":           etudiant["source"] or "JSON",
            "matieres":         matieres_list,
        }

    finally:
        cursor.close()
        conn.close()


# -------------------------------------------------------------
# Route : POST /api/v1/etudiants
# Ajouter un étudiant — toujours source DB
# -------------------------------------------------------------
@router.post("/etudiants", status_code=201)
def create_etudiant(etudiant: EtudiantCreate):
    conn = get_connection()
    cursor = get_cursor(conn)

    try:
        cursor.execute(
            "SELECT 1 FROM etudiants WHERE numero = %s", (etudiant.numero,)
        )
        if cursor.fetchone():
            raise HTTPException(
                status_code=400,
                detail=f"Numéro {etudiant.numero} déjà existant"
            )

        cursor.execute("SELECT id FROM classes WHERE nom = %s", (etudiant.classe,))
        classe = cursor.fetchone()
        if not classe:
            cursor.execute(
                "INSERT INTO classes (nom) VALUES (%s) RETURNING id",
                (etudiant.classe,)
            )
            classe_id = cursor.fetchone()["id"]
        else:
            classe_id = classe["id"]

        cursor.execute("""
            INSERT INTO etudiants
                (numero, code, prenom, nom, date_naissance,
                 classe_id, moyenne_generale, source)
            VALUES (%s, %s, %s, %s, %s, %s, %s, 'DB')
            RETURNING id
        """, (
            etudiant.numero, etudiant.code, etudiant.prenom, etudiant.nom,
            etudiant.date_naissance, classe_id, etudiant.moyenne_generale
        ))
        etudiant_id = cursor.fetchone()["id"]

        for mat in etudiant.matieres:
            cursor.execute("""
                INSERT INTO matieres (etudiant_id, nom, note_examen, moyenne)
                VALUES (%s, %s, %s, %s) RETURNING id
            """, (etudiant_id, mat.nom, mat.note_examen, mat.moyenne))
            matiere_id = cursor.fetchone()["id"]
            for devoir in mat.notes_devoir:
                cursor.execute(
                    "INSERT INTO notes_devoir (matiere_id, note) VALUES (%s, %s)",
                    (matiere_id, devoir.note)
                )

        conn.commit()
        return {"message": "Étudiant créé avec succès", "id": etudiant_id}

    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()


# -------------------------------------------------------------
# Route : POST /api/v1/etudiants/{id}/confirmer
# Passer un étudiant JSON → DB (import confirmé)
# -------------------------------------------------------------
@router.post("/etudiants/{etudiant_id}/confirmer")
def confirmer_etudiant(etudiant_id: int):
    conn = get_connection()
    cursor = get_cursor(conn)

    try:
        cursor.execute(
            "UPDATE etudiants SET source = 'DB' WHERE id = %s AND source = 'JSON' RETURNING id",
            (etudiant_id,)
        )
        if not cursor.fetchone():
            raise HTTPException(
                status_code=404,
                detail="Étudiant non trouvé ou déjà en DB"
            )
        conn.commit()
        return {"message": "Étudiant confirmé en DB"}

    finally:
        cursor.close()
        conn.close()


# -------------------------------------------------------------
# Route : PUT /api/v1/etudiants/{id}
# Modifier — uniquement les étudiants source DB
# -------------------------------------------------------------
@router.put("/etudiants/{etudiant_id}")
def update_etudiant(etudiant_id: int, etudiant: EtudiantCreate):
    conn = get_connection()
    cursor = get_cursor(conn)

    try:
        cursor.execute(
            "SELECT source FROM etudiants WHERE id = %s", (etudiant_id,)
        )
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Étudiant non trouvé")
        if row["source"] == "JSON":
            raise HTTPException(
                status_code=403,
                detail="Cet étudiant est en lecture seule (JSON). Confirmez-le d'abord."
            )

        cursor.execute("SELECT id FROM classes WHERE nom = %s", (etudiant.classe,))
        classe = cursor.fetchone()
        if not classe:
            cursor.execute(
                "INSERT INTO classes (nom) VALUES (%s) RETURNING id",
                (etudiant.classe,)
            )
            classe_id = cursor.fetchone()["id"]
        else:
            classe_id = classe["id"]

        cursor.execute("""
            UPDATE etudiants
            SET code = %s, prenom = %s, nom = %s,
                date_naissance = %s, classe_id = %s,
                moyenne_generale = %s
            WHERE id = %s
        """, (
            etudiant.code, etudiant.prenom, etudiant.nom,
            etudiant.date_naissance, classe_id,
            etudiant.moyenne_generale, etudiant_id
        ))

        conn.commit()
        return {"message": "Étudiant modifié avec succès"}

    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()


# -------------------------------------------------------------
# Route : PATCH /api/v1/etudiants/{id}/archiver
# -------------------------------------------------------------
@router.patch("/etudiants/{etudiant_id}/archiver")
def archiver_etudiant(etudiant_id: int):
    conn = get_connection()
    cursor = get_cursor(conn)

    try:
        cursor.execute(
            "UPDATE etudiants SET archive = TRUE WHERE id = %s RETURNING id",
            (etudiant_id,)
        )
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Étudiant non trouvé")
        conn.commit()
        return {"message": "Étudiant archivé avec succès"}
    finally:
        cursor.close()
        conn.close()


# -------------------------------------------------------------
# Route : PATCH /api/v1/etudiants/{id}/restore
# -------------------------------------------------------------
@router.patch("/etudiants/{etudiant_id}/restore")
def restore_etudiant(etudiant_id: int):
    conn = get_connection()
    cursor = get_cursor(conn)

    try:
        cursor.execute(
            "UPDATE etudiants SET archive = FALSE WHERE id = %s RETURNING id",
            (etudiant_id,)
        )
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Étudiant non trouvé")
        conn.commit()
        return {"message": "Étudiant restauré avec succès"}
    finally:
        cursor.close()
        conn.close()


# -------------------------------------------------------------
# Route : GET /api/v1/archives
# -------------------------------------------------------------
@router.get("/archives")
def get_archives():
    conn = get_connection()
    cursor = get_cursor(conn)

    try:
        cursor.execute("""
            SELECT
                e.id, e.numero, e.code, e.prenom, e.nom,
                e.date_naissance, c.nom AS classe,
                e.moyenne_generale, e.archive, e.source
            FROM etudiants e
            LEFT JOIN classes c ON c.id = e.classe_id
            WHERE e.archive = TRUE
            ORDER BY e.nom, e.prenom
        """)
        rows = cursor.fetchall()

        return [
            {
                "id":               row["id"],
                "numero":           row["numero"],
                "code":             row["code"],
                "prenom":           row["prenom"],
                "nom":              row["nom"],
                "date_naissance":   row["date_naissance"],
                "classe":           row["classe"] or "",
                "moyenne_generale": row["moyenne_generale"],
                "archive":          row["archive"],
                "source":           row["source"] or "JSON",
            }
            for row in rows
        ]

    finally:
        cursor.close()
        conn.close()

