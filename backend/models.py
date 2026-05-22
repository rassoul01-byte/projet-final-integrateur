from dataclasses import dataclass, field
from typing import Optional
from datetime import date


@dataclass
class NoteDevoir:
    note: float
    id: Optional[int] = None
    matiere_id: Optional[int] = None


@dataclass
class Matiere:
    nom: str
    note_examen: float
    moyenne: float
    notes_devoir: list[NoteDevoir] = field(default_factory=list)
    id: Optional[int] = None
    etudiant_id: Optional[int] = None


@dataclass
class Etudiant:
    numero: str
    code: str
    prenom: str
    nom: str
    classe: str
    matieres: list[Matiere] = field(default_factory=list)
    date_naissance: Optional[date] = None
    moyenne_generale: Optional[float] = None
    archive: bool = False
    id: Optional[int] = None

    def calculer_moyenne_generale(self) -> float:
        if not self.matieres:
            return 0.0
        return round(sum(m.moyenne for m in self.matieres) / len(self.matieres), 2)