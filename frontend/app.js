// =============================================================
// app.js — Logique JavaScript de l'application
// Gestion des étudiants : affichage, recherche, CRUD
// Source DB = modifiable / Source JSON = lecture seule
// =============================================================

const API = "http://localhost:8000/api/v1";

// État global de l'application
let state = {
  page: 1,
  par_page: 5,
  search: "",
  classe: "",
  source: "",
  total: 0,
  total_pages: 0,
};

// -------------------------------------------------------------
// Initialisation au chargement de la page
// -------------------------------------------------------------
document.addEventListener("DOMContentLoaded", () => {
  chargerClasses();
  chargerEtudiants();

  // Recherche en temps réel (délai 400ms)
  let timer;
  document.getElementById("search").addEventListener("input", (e) => {
    clearTimeout(timer);
    timer = setTimeout(() => {
      state.search = e.target.value;
      state.page = 1;
      chargerEtudiants();
    }, 400);
  });

  // Filtre classe
  document.getElementById("filter-classe").addEventListener("change", (e) => {
    state.classe = e.target.value;
    state.page = 1;
    chargerEtudiants();
  });

  // Filtre source DB / JSON
  document.getElementById("filter-source").addEventListener("change", (e) => {
    state.source = e.target.value;
    state.page = 1;
    chargerEtudiants();
  });

  // Nombre de lignes par page
  document.getElementById("par-page").addEventListener("change", (e) => {
    state.par_page = parseInt(e.target.value);
    state.page = 1;
    chargerEtudiants();
  });

  // Sélectionner tout
  document.getElementById("select-all").addEventListener("change", (e) => {
    document.querySelectorAll(".row-check").forEach(cb => {
      cb.checked = e.target.checked;
    });
  });
});

// -------------------------------------------------------------
// Charger les classes pour les filtres et le formulaire
// -------------------------------------------------------------
async function chargerClasses() {
  try {
    const res  = await fetch(`${API}/stats/classes`);
    const data = await res.json();

    const filterClasse = document.getElementById("filter-classe");
    const addClasse    = document.getElementById("add-classe");

    data.forEach(c => {
      filterClasse.innerHTML += `<option value="${c.classe}">${c.classe}</option>`;
      addClasse.innerHTML    += `<option value="${c.classe}">${c.classe}</option>`;
    });
  } catch (e) {
    console.error("Erreur chargement classes:", e);
  }
}

// -------------------------------------------------------------
// Charger les étudiants depuis l'API
// -------------------------------------------------------------
async function chargerEtudiants() {
  const loader = document.getElementById("loader");
  const tbody  = document.getElementById("tbody");

  loader.style.display = "block";
  tbody.innerHTML = "";

  try {
    const params = new URLSearchParams({
      page:     state.page,
      par_page: state.par_page,
      search:   state.search,
      classe:   state.classe,
      source:   state.source,
    });

    const res  = await fetch(`${API}/etudiants?${params}`);
    const data = await res.json();

    state.total       = data.total;
    state.total_pages = data.total_pages;

    afficherEtudiants(data.data);
    afficherPagination();

    document.getElementById("table-title").textContent =
      `📋 Liste des étudiants (${data.total} au total)`;

  } catch (e) {
    tbody.innerHTML = `<tr><td colspan="9" style="text-align:center;color:red;padding:20px;">
      Erreur de connexion à l'API</td></tr>`;
  } finally {
    loader.style.display = "none";
  }
}

// -------------------------------------------------------------
// Afficher les étudiants dans le tableau
// -------------------------------------------------------------
function afficherEtudiants(etudiants) {
  const tbody = document.getElementById("tbody");

  if (etudiants.length === 0) {
    tbody.innerHTML = `<tr><td colspan="9" style="text-align:center;
      color:#64748b;padding:30px;">Aucun étudiant trouvé</td></tr>`;
    return;
  }

  tbody.innerHTML = etudiants.map(e => {
    const estJSON = e.source === "JSON";

    // Cellules : éditables uniquement si source DB
    const cellPrenom = estJSON
      ? `<td>${e.prenom}</td>`
      : `<td class="editable" ondblclick="editCell(this, ${e.id}, 'prenom')">${e.prenom}</td>`;

    const cellNom = estJSON
      ? `<td>${e.nom}</td>`
      : `<td class="editable" ondblclick="editCell(this, ${e.id}, 'nom')">${e.nom}</td>`;

    const cellClasse = estJSON
      ? `<td>${e.classe}</td>`
      : `<td class="editable" ondblclick="editCell(this, ${e.id}, 'classe')">${e.classe}</td>`;

    // Boutons selon la source
    const boutons = estJSON ? `
      <button class="btn btn-primary btn-sm" onclick="voirDetail(${e.id})" title="Voir détail">👁️</button>
      <button class="btn btn-success btn-sm" onclick="confirmerEtudiant(${e.id})" title="Importer en DB">
        ✅ Confirmer
      </button>
    ` : `
      <button class="btn btn-primary btn-sm" onclick="voirDetail(${e.id})" title="Voir détail">👁️</button>
      <button class="btn btn-danger btn-sm" onclick="archiverEtudiant(${e.id})" title="Archiver">🗄️</button>
    `;

    return `
      <tr id="row-${e.id}" style="${estJSON ? 'background:#fffbeb;' : ''}">
        <td><input type="checkbox" class="row-check" value="${e.id}" /></td>
        <td>${e.numero}</td>
        <td>${e.code}</td>
        ${cellPrenom}
        ${cellNom}
        ${cellClasse}
        <td><strong>${e.moyenne_generale ?? "—"}</strong></td>
        <td>
          <span class="badge badge-${e.source.toLowerCase()}">${e.source}</span>
        </td>
        <td style="white-space:nowrap;">${boutons}</td>
      </tr>
    `;
  }).join("");
}

// -------------------------------------------------------------
// Afficher la pagination
// -------------------------------------------------------------
function afficherPagination() {
  const pagination = document.getElementById("pagination");
  const { page, total_pages, total } = state;

  if (total_pages <= 1) {
    pagination.innerHTML = "";
    return;
  }

  let html = `
    <button onclick="allerPage(${page - 1})" ${page === 1 ? "disabled" : ""}>◀ Précédent</button>
  `;

  const debut = Math.max(1, page - 2);
  const fin   = Math.min(total_pages, page + 2);

  if (debut > 1) html += `<button onclick="allerPage(1)">1</button><span>...</span>`;

  for (let i = debut; i <= fin; i++) {
    html += `<button class="${i === page ? 'active' : ''}" onclick="allerPage(${i})">${i}</button>`;
  }

  if (fin < total_pages) {
    html += `<span>...</span><button onclick="allerPage(${total_pages})">${total_pages}</button>`;
  }

  html += `
    <button onclick="allerPage(${page + 1})" ${page === total_pages ? "disabled" : ""}>Suivant ▶</button>
    <span class="info">Page ${page}/${total_pages} — ${total} étudiants</span>
  `;

  pagination.innerHTML = html;
}

// -------------------------------------------------------------
// Navigation entre les pages
// -------------------------------------------------------------
function allerPage(page) {
  if (page < 1 || page > state.total_pages) return;
  state.page = page;
  chargerEtudiants();
}

// -------------------------------------------------------------
// Confirmer un étudiant JSON → DB
// -------------------------------------------------------------
async function confirmerEtudiant(id) {
  if (!confirm("Confirmer cet étudiant ? Il passera de JSON → DB et deviendra modifiable.")) return;

  try {
    const res = await fetch(`${API}/etudiants/${id}/confirmer`, {
      method: "POST",
    });

    if (!res.ok) {
      const err = await res.json();
      showToast(err.detail || "Erreur confirmation", "error");
      return;
    }

    showToast("Étudiant confirmé en DB ✓", "success");
    chargerEtudiants();
  } catch (e) {
    showToast("Erreur connexion API", "error");
  }
}

// -------------------------------------------------------------
// Voir le détail d'un étudiant
// -------------------------------------------------------------
async function voirDetail(id) {
  try {
    const res = await fetch(`${API}/etudiants/${id}`);
    const e   = await res.json();

    const matieres = e.matieres.map(m => `
      <tr>
        <td><strong>${m.nom}</strong></td>
        <td>${m.notes_devoir.map(d => d.note).join(", ") || "—"}</td>
        <td>${m.note_examen}</td>
        <td><strong>${m.moyenne}</strong></td>
      </tr>
    `).join("");

    const sourceBadge = e.source === "JSON"
      ? `<span class="badge" style="background:#fef9c3;color:#92400e;">JSON — lecture seule</span>`
      : `<span class="badge badge-db">DB — modifiable</span>`;

    document.getElementById("detail-content").innerHTML = `
      <table style="width:100%;margin-bottom:16px;font-size:13px;">
        <tr><td style="color:#64748b;width:140px;">Numéro</td>
            <td><strong>${e.numero}</strong></td></tr>
        <tr><td style="color:#64748b;">Nom complet</td>
            <td>${e.prenom} ${e.nom}</td></tr>
        <tr><td style="color:#64748b;">Classe</td>
            <td>${e.classe}</td></tr>
        <tr><td style="color:#64748b;">Naissance</td>
            <td>${e.date_naissance ?? "—"}</td></tr>
        <tr><td style="color:#64748b;">Moyenne générale</td>
            <td><strong style="color:#2563eb;">${e.moyenne_generale}</strong></td></tr>
        <tr><td style="color:#64748b;">Source</td>
            <td>${sourceBadge}</td></tr>
      </table>
      <div class="card-title">📚 Notes par matière</div>
      <table style="width:100%;font-size:13px;">
        <thead>
          <tr style="background:#f1f5f9;">
            <th style="padding:8px;">Matière</th>
            <th style="padding:8px;">Devoirs</th>
            <th style="padding:8px;">Examen</th>
            <th style="padding:8px;">Moyenne</th>
          </tr>
        </thead>
        <tbody>${matieres}</tbody>
      </table>
      ${e.source === "JSON" ? `
        <div style="margin-top:16px;">
          <button class="btn btn-success" onclick="confirmerEtudiant(${e.id});closeModal('modal-detail')">
            ✅ Confirmer en DB
          </button>
        </div>
      ` : ""}
    `;

    openModal("modal-detail");
  } catch (e) {
    showToast("Erreur chargement détail", "error");
  }
}

// -------------------------------------------------------------
// Édition inline d'une cellule (double-clic) — DB uniquement
// -------------------------------------------------------------
function editCell(cell, id, champ) {
  const valeurActuelle = cell.textContent.trim();

  cell.innerHTML = `
    <input class="edit-input" value="${valeurActuelle}"
      onkeydown="saveCell(event, this, ${id}, '${champ}')" />
  `;
  cell.querySelector("input").focus();
}

async function saveCell(event, input, id, champ) {
  if (event.key === "Enter") {
    const nouvelleValeur = input.value.trim();
    if (!nouvelleValeur) return;

    try {
      const res     = await fetch(`${API}/etudiants/${id}`);
      const etudiant = await res.json();

      etudiant[champ] = nouvelleValeur;

      const resPut = await fetch(`${API}/etudiants/${id}`, {
        method:  "PUT",
        headers: { "Content-Type": "application/json" },
        body:    JSON.stringify(etudiant),
      });

      if (!resPut.ok) {
        const err = await resPut.json();
        showToast(err.detail || "Erreur modification", "error");
        chargerEtudiants();
        return;
      }

      showToast("Modification enregistrée ✓", "success");
      chargerEtudiants();
    } catch (e) {
      showToast("Erreur modification", "error");
    }
  }

  if (event.key === "Escape") {
    chargerEtudiants();
  }
}

// -------------------------------------------------------------
// Ajouter un étudiant — toujours source DB
// -------------------------------------------------------------
async function ajouterEtudiant() {
  const numero  = document.getElementById("add-numero").value.trim();
  const code    = document.getElementById("add-code").value.trim();
  const prenom  = document.getElementById("add-prenom").value.trim();
  const nom     = document.getElementById("add-nom").value.trim();
  const date    = document.getElementById("add-date").value;
  const classe  = document.getElementById("add-classe").value;
  const moyenne = document.getElementById("add-moyenne").value;

  if (!numero || !code || !prenom || !nom || !classe) {
    showToast("Veuillez remplir tous les champs obligatoires", "error");
    return;
  }

  try {
    const res = await fetch(`${API}/etudiants`, {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify({
        numero, code, prenom, nom,
        date_naissance:   date || null,
        classe,
        moyenne_generale: moyenne ? parseFloat(moyenne) : null,
        matieres:         [],
      }),
    });

    if (!res.ok) {
      const err = await res.json();
      showToast(err.detail || "Erreur ajout", "error");
      return;
    }

    showToast("Étudiant ajouté en DB ✓", "success");
    closeModal("modal-ajout");
    chargerEtudiants();
  } catch (e) {
    showToast("Erreur connexion API", "error");
  }
}

// -------------------------------------------------------------
// Archiver un étudiant
// -------------------------------------------------------------
async function archiverEtudiant(id) {
  if (!confirm("Archiver cet étudiant ?")) return;

  try {
    await fetch(`${API}/etudiants/${id}/archiver`, { method: "PATCH" });
    showToast("Étudiant archivé ✓", "success");
    chargerEtudiants();
  } catch (e) {
    showToast("Erreur archivage", "error");
  }
}

// -------------------------------------------------------------
// Afficher les archives
// -------------------------------------------------------------
async function showArchives() {
  try {
    const res  = await fetch(`${API}/archives`);
    const data = await res.json();

    document.getElementById("table-title").textContent =
      `🗄️ Archives (${data.length} étudiants)`;

    const tbody = document.getElementById("tbody");
    if (data.length === 0) {
      tbody.innerHTML = `<tr><td colspan="9" style="text-align:center;
        color:#64748b;padding:30px;">Aucun étudiant archivé</td></tr>`;
      return;
    }

    tbody.innerHTML = data.map(e => `
      <tr>
        <td></td>
        <td>${e.numero}</td>
        <td>${e.code}</td>
        <td>${e.prenom}</td>
        <td>${e.nom}</td>
        <td>${e.classe}</td>
        <td>${e.moyenne_generale ?? "—"}</td>
        <td><span class="badge badge-${e.source.toLowerCase()}">${e.source}</span></td>
        <td>
          <button class="btn btn-success btn-sm"
            onclick="restaurerEtudiant(${e.id})">♻️ Restaurer</button>
        </td>
      </tr>
    `).join("");

    document.getElementById("pagination").innerHTML = `
      <button class="btn btn-primary btn-sm" onclick="chargerEtudiants()">
        ← Retour à la liste
      </button>
    `;
  } catch (e) {
    showToast("Erreur chargement archives", "error");
  }
}

// -------------------------------------------------------------
// Restaurer un étudiant archivé
// -------------------------------------------------------------
async function restaurerEtudiant(id) {
  try {
    await fetch(`${API}/etudiants/${id}/restore`, { method: "PATCH" });
    showToast("Étudiant restauré ✓", "success");
    chargerEtudiants();
  } catch (e) {
    showToast("Erreur restauration", "error");
  }
}

// -------------------------------------------------------------
// Ouvrir / fermer une modal
// -------------------------------------------------------------
function openModal(id)  { document.getElementById(id).classList.add("open"); }
function closeModal(id) { document.getElementById(id).classList.remove("open"); }

document.addEventListener("click", (e) => {
  if (e.target.classList.contains("modal-overlay")) {
    e.target.classList.remove("open");
  }
});

// -------------------------------------------------------------
// Notification toast
// -------------------------------------------------------------
function showToast(message, type = "success") {
  const toast = document.getElementById("toast");
  toast.textContent = message;
  toast.className   = `toast ${type} show`;
  setTimeout(() => toast.classList.remove("show"), 3000);
}