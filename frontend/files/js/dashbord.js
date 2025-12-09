// ===============================
//  AUTHENTIFICATION & PROFIL
// ===============================

const token = localStorage.getItem('token');
if (!token) {
  alert('Veuillez vous connecter !');
  window.location.href = 'index.html';
}

let userRole = 'locataire';

try {
  const payload = JSON.parse(atob(token.split('.')[1]));
  userRole = payload.role || 'locataire';

  const userNameEl = document.getElementById('user-name');
  const userRoleEl = document.getElementById('user-role');

  if (userNameEl) userNameEl.textContent = payload.email ? payload.email.split('@')[0] : 'Utilisateur';
  if (userRoleEl) userRoleEl.textContent = userRole;

  if (userRole === 'bailleur') {
    document.getElementById('my-listings')?.classList.remove('hidden');
    document.getElementById('create-listing')?.classList.remove('hidden');
  }
} catch (e) {
  localStorage.removeItem('token');
  window.location.href = 'index.html';
}

// ===============================
//  NAVIGATION
// ===============================

document.querySelectorAll('.menu-item').forEach(item => {
  if (item.id === 'become-bailleur') {
    item.onclick = () => {
      setActiveMenu(item);
      document.getElementById('become-bailleur-section')?.classList.remove('hidden');
      document.getElementById('content-area').innerHTML = '';
      checkBailleurStatus();
    };
  } else {
    item.addEventListener('click', () => {
      setActiveMenu(item);
      loadPage(item.dataset.page || 'home');
    });
  }
});

function setActiveMenu(item) {
  document.querySelectorAll('.menu-item').forEach(i => i.classList.remove('active'));
  item.classList.add('active');
}

// ===============================
//  PAGE LOADER
// ===============================

function loadPage(page) {
  const content = document.getElementById('content-area');
  if (!content) return;

  const pages = {
    home: `
      <div class="card">
        <h2>Accueil</h2>
        <p>Bienvenue dans ton espace immobilier.</p>
      </div>`,
    search: getSearchPage(),
    "my-listings": `
      <div class="card">
        <h2>Mes annonces</h2>
        <div id="my-annonces">Chargement...</div>
      </div>`,
    "create-listing": getCreateListingForm(),
    profile: `
      <div class="card">
        <h2>Profil</h2>
        <p>Gère ici les paramètres de ton compte.</p>
      </div>`
  };

  content.innerHTML = pages[page] || pages.home;
  document.getElementById('become-bailleur-section')?.classList.add('hidden');

  if (page === 'my-listings') loadMyListings();
  if (page === 'search') loadAllListings();
}

// ===============================
//  RECHERCHE
// ===============================

function getSearchPage() {
  return `
    <div class="card">
      <h2>Rechercher un bien</h2>
      <div style="display:flex; gap:10px; margin-bottom:20px;">
        <input type="text" id="search-ville" placeholder="Ville" style="flex:2">
        <input type="number" id="search-prix-min" placeholder="Prix min">
        <input type="number" id="search-prix-max" placeholder="Prix max">
        <button onclick="loadAllListings()" class="btn">Rechercher</button>
      </div>
      <div id="search-results" class="listing-grid"></div>
    </div>
  `;
}

async function loadAllListings() {
  const ville = document.getElementById('search-ville')?.value || '';
  const prixMin = document.getElementById('search-prix-min')?.value || '';
  const prixMax = document.getElementById('search-prix-max')?.value || '';

  let url = 'http://127.0.0.1:8000/api/listings/';
  const params = new URLSearchParams();

  if (ville) params.append('ville', ville);
  if (prixMin) params.append('prix_min', prixMin);
  if (prixMax) params.append('prix_max', prixMax);

  if (params.toString()) url += '?' + params.toString();

  try {
    const res = await fetch(url);
    const listings = await res.json();
    const container = document.getElementById('search-results');

    if (!Array.isArray(listings) || listings.length === 0) {
      if (container) container.innerHTML = '<p style="text-align:center; color:#888;">Aucun bien trouvé</p>';
      return;
    }

    if (container) {
      container.innerHTML = listings.map(l => `
        <div class="listing-card" onclick="showListingDetail(${l.id})">
        <img src="${(l.photos && l.photos[0] ? 'http://127.0.0.1:8000' + l.photos[0] : 'https://via.placeholder.com/300x180')}" class="listing-img">
            <div class="listing-title">${l.titre}</div>
            <div class="listing-price">${Number(l.prix).toLocaleString()} FCFA/mois</div>
            <p>${l.ville} • ${l.surface || 'Surface inconnue'}</p>
          </div>
        </div>
      `).join('');
    }

  } catch (err) {
    const container = document.getElementById('search-results');
    if (container) container.innerHTML = '<p style="color:#f85149;">Erreur de chargement</p>';
  }
}

// ===============================
//  DETAIL D’UNE ANNONCE
// ===============================

async function showListingDetail(id) {
  try {
    const res = await fetch(`http://127.0.0.1:8000/api/listings/${id}/`);
    const l = await res.json();

    const imgSrc = (l.photos && l.photos[0]) 
    ? 'http://127.0.0.1:8000' + l.photos[0] 
    : 'https://via.placeholder.com/600x400';


    document.getElementById('content-area').innerHTML = `
      <div class="card">
        <h2>${l.titre}</h2>
        <img src="${imgSrc}" style="width:100%; border-radius:16px; margin:20px 0;">
        <p><strong>Prix :</strong> ${Number(l.prix).toLocaleString()} FCFA/mois</p>
        <p><strong>Ville :</strong> ${l.ville} • ${l.quartier || ''}</p>
        <p><strong>Surface :</strong> ${l.surface || 'Non précisée'}</p>
        <p><strong>Description :</strong><br>${l.description}</p>
        <button onclick="reserveListing(${l.id})" class="btn btn-success" style="width:100%; padding:16px;">
          Réserver ce bien
        </button>
        <button onclick="loadPage('search')" class="btn" style="width:100%; background:#666;">Retour</button>
      </div>
    `;
  } catch {
    alert('Erreur lors du chargement.');
  }
}

function reserveListing(id) {
  if (confirm('Souhaites-tu réserver ce bien ?')) {
    alert('Demande envoyée au bailleur !');
  }
}

// ===============================
//  MES ANNONCES (BAILLEUR)
// ===============================

async function loadMyListings() {
  try {
    const res = await fetch('http://127.0.0.1:8000/api/listings/', {
      headers: { 'Authorization': `Bearer ${token}` }
    });

    const listings = await res.json();
    const container = document.getElementById('my-annonces');

    if (!Array.isArray(listings) || listings.length === 0) {
      if (container) container.innerHTML = "<p>Vous n'avez pas encore publié d'annonce.</p>";
      return;
    }

    if (container) {
      container.innerHTML = `
        <div class="listing-grid">
          ${listings.map(l => `
            <div class="listing-card">
              <img src="${(l.photos && l.photos[0] ? 'http://127.0.0.1:8000' + l.photos[0] : 'https://via.placeholder.com/300x180')}" class="listing-img">

              <div class="listing-info">
                <div class="listing-title">${l.titre}</div>
                <div class="listing-price">${Number(l.prix).toLocaleString()} FCFA/mois</div>
                <button onclick="deleteListing(${l.id})" class="btn btn-danger" style="margin-top:10px;">
                  Supprimer
                </button>
              </div>
            </div>
          `).join('')}
        </div>
      `;
    }

  } catch {
    const container = document.getElementById('my-annonces');
    if (container) container.innerHTML = '<p>Erreur.</p>';
  }
}

async function deleteListing(id) {
  if (!confirm('Supprimer cette annonce ?')) return;

  try {
    const res = await fetch(`http://127.0.0.1:8000/api/listings/${id}/`, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });

    if (res.status === 204) {
      alert('Annonce supprimée !');
      loadMyListings();  // Recharge la liste après suppression
    } else if (res.status === 403) {
      alert("Vous n'avez pas la permission de supprimer cette annonce.");
    } else {
      const data = await res.json();
      alert('Erreur lors de la suppression : ' + JSON.stringify(data));
    }
  } catch (err) {
    console.error(err);
    alert('Erreur réseau ou serveur.');
  }
}


// ===============================
//  CREATION D’ANNONCE
// ===============================

// … le reste du code (formulaire et submit) reste identique mais avec vérification existence des éléments



// ===============================
//  CREATION D’ANNONCE
// ===============================

function getCreateListingForm() {
  return `
    <div class="card">
      <h2>Publier une annonce</h2>

      <form id="create-listing-form" enctype="multipart/form-data">
        <!-- Infos principales -->
        <input type="text" id="listing-titre" placeholder="Titre" required>
        <textarea id="listing-description" placeholder="Description" required></textarea>

        <!-- Prix et caution -->
        <input type="number" id="listing-prix" placeholder="Prix (FCFA)" required>
        <input type="number" id="listing-caution" placeholder="Caution (optionnel)">

        <!-- Localisation -->
        <input type="text" id="listing-ville" placeholder="Ville" required>
        <input type="text" id="listing-quartier" placeholder="Quartier">
        <input type="text" id="listing-adresse" placeholder="Adresse complète (abonnés)" >

        <!-- Caractéristiques -->
        <input type="number" id="listing-surface" placeholder="Surface (m²)">
        <input type="number" id="listing-chambres" placeholder="Nombre de chambres">
        <input type="number" id="listing-salles-de-bain" placeholder="Salles de bain" value="1">
        <input type="number" id="listing-etage" placeholder="Étage">
        <input type="number" id="listing-annee" placeholder="Année de construction">

        <!-- Confort -->
        <label><input type="checkbox" id="listing-meuble"> Meublé</label>
        <label><input type="checkbox" id="listing-clim"> Climatisation</label>
        <label><input type="checkbox" id="listing-chauffage"> Chauffage</label>
        <label><input type="checkbox" id="listing-balcon"> Balcon</label>
        <label><input type="checkbox" id="listing-jardin"> Jardin</label>
        <label><input type="checkbox" id="listing-parking"> Parking</label>
        <label><input type="checkbox" id="listing-piscine"> Piscine</label>

        <!-- Équipements -->
        <label><input type="checkbox" id="listing-wifi"> WiFi</label>
        <label><input type="checkbox" id="listing-tv"> Télévision</label>
        <label><input type="checkbox" id="listing-lave-linge"> Machine à laver</label>
        <label><input type="checkbox" id="listing-cuisine"> Cuisine équipée</label>

        <!-- Photos -->
        <label>Photos</label>
        <input type="file" id="listing-images" multiple accept="image/*">

        <button type="submit" class="btn btn-success" style="width:100%; padding:16px;">
          Publier
        </button>
      </form>
    </div>
  `;
}


document.getElementById('content-area').addEventListener('submit', async e => {
  if (e.target.id !== 'create-listing-form') return;
  e.preventDefault();

  const formData = new FormData();

  // Champs texte / nombres
  formData.append('titre', document.getElementById('listing-titre').value);
  formData.append('description', document.getElementById('listing-description').value);
  formData.append('prix', document.getElementById('listing-prix').value);
  formData.append('caution', document.getElementById('listing-caution').value || 0);
  formData.append('ville', document.getElementById('listing-ville').value);
  formData.append('quartier', document.getElementById('listing-quartier').value);
  formData.append('adresse_complete', document.getElementById('listing-adresse').value);
  formData.append('surface', document.getElementById('listing-surface').value || '');
  formData.append('chambres', document.getElementById('listing-chambres').value || '');
  formData.append('salles_de_bain', document.getElementById('listing-salles-de-bain').value || 1);
  formData.append('etage', document.getElementById('listing-etage').value || '');
  formData.append('annee_construction', document.getElementById('listing-annee').value || '');

  // Cases à cocher
  formData.append('meuble', document.getElementById('listing-meuble').checked);
  formData.append('climatisation', document.getElementById('listing-clim').checked);
  formData.append('chauffage', document.getElementById('listing-chauffage').checked);
  formData.append('balcon', document.getElementById('listing-balcon').checked);
  formData.append('jardin', document.getElementById('listing-jardin').checked);
  formData.append('parking', document.getElementById('listing-parking').checked);
  formData.append('piscine', document.getElementById('listing-piscine').checked);
  formData.append('wifi', document.getElementById('listing-wifi').checked);
  formData.append('television', document.getElementById('listing-tv').checked);
  formData.append('machine_a_laver', document.getElementById('listing-lave-linge').checked);
  formData.append('cuisine_equipee', document.getElementById('listing-cuisine').checked);

  // Images
  const files = document.getElementById('listing-images').files;
  for (let file of files) formData.append('images', file);

  try {
    const res = await fetch('http://127.0.0.1:8000/api/listings/', {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${token}` },
      body: formData
    });

    if (res.ok) {
      alert('Annonce publiée !');
      loadPage('my-listings');
    } else {
      const data = await res.json();
      alert('Erreur : ' + JSON.stringify(data));
    }
  } catch {
    alert('Erreur réseau');
  }
});



// ===============================
//  BAILLEUR — DEMANDE
// ===============================

async function checkBailleurStatus() {
  try {
    const res = await fetch('http://127.0.0.1:8000/api/bailleur/status/', {
      headers: { 'Authorization': `Bearer ${token}` }
    });

    const data = await res.json();
    const statusDiv = document.getElementById('bailleur-status');
    const form = document.getElementById('bailleur-form');

    if (data.is_bailleur) {
      statusDiv.innerHTML = '<p style="color:#50fa7b">✔ Vous êtes bailleur approuvé !</p>';
      form.classList.add('hidden');
    } else if (data.is_bailleur_pending) {
      statusDiv.innerHTML = '<p style="color:#f1fa8c">⏳ Demande en cours…</p>';
      form.classList.add('hidden');
    } else {
      statusDiv.innerHTML = '';
      form.classList.remove('hidden');
    }
  } catch (err) {
    console.error(err);
  }
}

document.getElementById('bailleur-form')?.addEventListener('submit', async e => {
  e.preventDefault();

  const formData = new FormData();
  formData.append('cni', document.getElementById('cni').files[0]);
  formData.append('titre_foncier', document.getElementById('titre').files[0]);
  formData.append('adresse', document.getElementById('adresse').value);
  formData.append('ville', document.getElementById('ville').value);

  try {
    const res = await fetch('http://127.0.0.1:8000/api/bailleur/apply/', {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${token}` },
      body: formData
    });

    if (res.ok) {
      alert('Demande envoyée !');
      checkBailleurStatus();
    }
  } catch {
    alert('Erreur');
  }
});


// ===============================
//  LOGOUT
// ===============================

function logout() {
  localStorage.removeItem('token');
  window.location.href = 'index.html';
}

loadPage('home');
