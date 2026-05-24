# =============================================================
# schemas.py — Schémas Pydantic pour validation des données
# Pydantic valide automatiquement les types et formats
# =============================================================

from pydantic import BaseModel
from typing import Optional
from datetime import date


# -------------------------------------------------------------
# Schéma : Note de devoir
# -------------------------------------------------------------
class NoteDevoir(BaseModel):
    note: float                        # Note entre 0 et 20


# -------------------------------------------------------------
# Schéma : Matière avec ses notes
# -------------------------------------------------------------
class Matiere(BaseModel):
    nom: str                           # Ex: Math, Francais
    note_examen: float                 # Note de l'examen
    moyenne: float                     # Moyenne calculée
    notes_devoir: list[NoteDevoir] = []  # Liste des devoirs


# -------------------------------------------------------------
# Schéma de base : champs communs à tous les schémas étudiant
# -------------------------------------------------------------
class EtudiantBase(BaseModel):
    numero: str                        # Identifiant unique métier
    code: str                          # Code de l'étudiant
    prenom: str
    nom: str
    date_naissance: Optional[date] = None
    classe: str                        # Ex: 6emeA, 3emeB
    moyenne_generale: Optional[float] = None


# -------------------------------------------------------------
# Schéma : Création d'un étudiant (avec ses matières)
# Utilisé pour POST /etudiants
# -------------------------------------------------------------
class EtudiantCreate(EtudiantBase):
    matieres: list[Matiere] = []


# -------------------------------------------------------------
# Schéma : Réponse API (ce que le serveur retourne)
# Inclut l'id, l'état d'archivage et la source des données
# -------------------------------------------------------------
class EtudiantResponse(EtudiantBase):
    id: int
    archive: bool
    source: str = "DB"                 # DB ou JSON

    class Config:
        from_attributes = True         # Compatibilité avec les objets Python


# -------------------------------------------------------------
# Schéma : Réponse paginée
# Utilisé pour GET /etudiants?page=1&par_page=5
# -------------------------------------------------------------
class PaginationResponse(BaseModel):
    total: int                         # Nombre total d'étudiants
    page: int                          # Page actuelle
    par_page: int                      # Lignes par page
    total_pages: int                   # Nombre total de pages
    data: list[EtudiantResponse]       # Liste des étudiants