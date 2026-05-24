# =============================================================
# routes/stats.py — Routes statistiques
# Préfixe : /api/v1
# =============================================================

from fastapi import APIRouter
from database import get_connection, get_cursor

router = APIRouter()


# -------------------------------------------------------------
# Route : GET /api/v1/stats/globales
# Indicateurs globaux (KPI) pour le dashboard
# -------------------------------------------------------------
@router.get("/stats/globales")
def get_stats_globales():
    conn = get_connection()
    cursor = get_cursor(conn)

    try:
        # Total étudiants
        cursor.execute("SELECT COUNT(*) AS total FROM etudiants")
        total = cursor.fetchone()["total"]

        # Total en base (non archivés)
        cursor.execute(
            "SELECT COUNT(*) AS total FROM etudiants WHERE archive = FALSE"
        )
        total_actifs = cursor.fetchone()["total"]

        # Total archivés
        cursor.execute(
            "SELECT COUNT(*) AS total FROM etudiants WHERE archive = TRUE"
        )
        total_archives = cursor.fetchone()["total"]

        # Moyenne générale globale
        cursor.execute(
            "SELECT ROUND(AVG(moyenne_generale), 2) AS moy FROM etudiants WHERE archive = FALSE"
        )
        moyenne_globale = cursor.fetchone()["moy"]

        return {
            "total_etudiants":   total,
            "total_actifs":      total_actifs,
            "total_archives":    total_archives,
            "moyenne_globale":   float(moyenne_globale) if moyenne_globale else 0.0,
            "source_db":         total_actifs,
            "source_json":       0,  # complété dynamiquement par le frontend
        }

    finally:
        cursor.close()
        conn.close()


# -------------------------------------------------------------
# Route : GET /api/v1/stats/classes
# Statistiques par classe
# -------------------------------------------------------------
@router.get("/stats/classes")
def get_stats_classes():
    conn = get_connection()
    cursor = get_cursor(conn)

    try:
        cursor.execute("""
            SELECT
                c.nom                              AS classe,
                COUNT(e.id)                        AS total,
                ROUND(AVG(e.moyenne_generale), 2)  AS moyenne,
                MAX(e.moyenne_generale)            AS meilleure,
                MIN(e.moyenne_generale)            AS plus_basse
            FROM classes c
            LEFT JOIN etudiants e
                ON e.classe_id = c.id AND e.archive = FALSE
            GROUP BY c.nom
            ORDER BY c.nom
        """)
        rows = cursor.fetchall()

        return [
            {
                "classe":       row["classe"],
                "total":        row["total"],
                "moyenne":      float(row["moyenne"]) if row["moyenne"] else 0.0,
                "meilleure":    float(row["meilleure"]) if row["meilleure"] else 0.0,
                "plus_basse":   float(row["plus_basse"]) if row["plus_basse"] else 0.0,
            }
            for row in rows
        ]

    finally:
        cursor.close()
        conn.close()


# -------------------------------------------------------------
# Route : GET /api/v1/stats/top-moyennes
# Top 10 des meilleures moyennes
# -------------------------------------------------------------
@router.get("/stats/top-moyennes")
def get_top_moyennes(limit: int = 10):
    conn = get_connection()
    cursor = get_cursor(conn)

    try:
        cursor.execute("""
            SELECT
                e.prenom, e.nom, c.nom AS classe,
                e.moyenne_generale
            FROM etudiants e
            LEFT JOIN classes c ON c.id = e.classe_id
            WHERE e.archive = FALSE
            ORDER BY e.moyenne_generale DESC
            LIMIT %s
        """, (limit,))
        rows = cursor.fetchall()

        return [
            {
                "prenom":           row["prenom"],
                "nom":              row["nom"],
                "classe":           row["classe"] or "",
                "moyenne_generale": float(row["moyenne_generale"]) if row["moyenne_generale"] else 0.0,
            }
            for row in rows
        ]

    finally:
        cursor.close()
        conn.close()


# -------------------------------------------------------------
# Route : GET /api/v1/stats/matieres
# Moyenne par matière (toutes classes confondues)
# -------------------------------------------------------------
@router.get("/stats/matieres")
def get_stats_matieres():
    conn = get_connection()
    cursor = get_cursor(conn)

    try:
        cursor.execute("""
            SELECT
                m.nom                              AS matiere,
                ROUND(AVG(m.moyenne), 2)           AS moyenne,
                MAX(m.moyenne)                     AS meilleure,
                MIN(m.moyenne)                     AS plus_basse
            FROM matieres m
            JOIN etudiants e ON e.id = m.etudiant_id
            WHERE e.archive = FALSE
            GROUP BY m.nom
            ORDER BY m.nom
        """)
        rows = cursor.fetchall()

        return [
            {
                "matiere":    row["matiere"],
                "moyenne":    float(row["moyenne"]) if row["moyenne"] else 0.0,
                "meilleure":  float(row["meilleure"]) if row["meilleure"] else 0.0,
                "plus_basse": float(row["plus_basse"]) if row["plus_basse"] else 0.0,
            }
            for row in rows
        ]

    finally:
        cursor.close()
        conn.close()