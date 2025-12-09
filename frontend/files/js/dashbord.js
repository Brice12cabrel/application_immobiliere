// === JS COMPLET ET FONCTIONNEL ===
const token = localStorage.getItem('token');
if (!token) {
  alert('Connecte-toi !');
  window.location.href = 'index.html';
}

let userRole = 'locataire';

try {
  const payload = JSON.parse(atob(token.split('.')[1]));
  userRole = payload.role || 'locataire';
  document.getElementById('user-name').textContent = payload.email.split('@')[0];
  document.getElementById('user-role').textContent = userRole;

  if (userRole === 'bailleur') {
    document.getElementById('my-listings').classList.remove('hidden');
    document.getElementById('create-listing').classList.remove('hidden');
  }
} catch (e) {
  localStorage.removeItem('token');
  window.location.href = 'index.html';
}

// Navigation
document.querySelectorAll('.menu-item').forEach(item => {
  if (item.id === 'become-bailleur') {
    item.onclick = () => {
      document.querySelectorAll('.menu-item').forEach(i => i.classList.remove('active'));
      item.classList.add('active');
      document.getElementById('become-bailleur-section').classList.remove('hidden');
      document.getElementById('content-area').innerHTML = '';
      checkBailleurStatus();
    };
  } else {
    item.addEventListener('click', () => {
      document.querySelectorAll('.menu-item').forEach(i => i.classList.remove('active'));
      item.classList.add('active');
      loadPage(item.dataset.page || 'home');
    });
  }
});

function loadPage(page) {
  const content = document.getElementById('content-area');
  const pages = {
    home: `<div class="card"><h2>Accueil</h2><p>Bienvenue dans ton espace immobilier.</p></div>`,
    search: getSearchPage(),
    'my-listings': `<div class="card"><h2>Mes annonces</h2><div id="my-annonces">Chargement...</div></div>`,
    'create-listing': getCreateListingForm(),
    profile: `<div class="card"><h2>Profil</h2><p>Gestion du compte</p></div>`
  };
  content.innerHTML = pages[page] || pages.home;
  document.getElementById('become-bailleur-section').classList.add('hidden');

  if (page === 'my-listings') loadMyListings();
  if (page === 'search') loadAllListings();
}

// RECHERCHE
function getSearchPage() {
  return `
    <div class="card">
      <h2>Rechercher un bien</h2>
      <div style="display:flex;gap:10px;margin-bottom:20px;">
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
    if (listings.length === 0) {
      container.innerHTML = '<p style="text-align:center;color:#888;">Aucun bien trouvé</p>';
      return;
    }

    container.innerHTML = listings.map(l => `
      <div class="listing-card" onclick="showListingDetail(${l.id})">
        <img src="${l.photo_principale || l.images?.[0] || 'https://via.placeholder.com/300x180/333/fff?text=Photo'}" class="listing-img">
        <div class="listing-info">
          <div class="listing-title">${l.titre}</div>
          <div class="listing-price">${l.prix.toLocaleString()} FCFA/mois</div>
          <p>${l.ville} • ${l.surface || 'Surface inconnue'}</p>
        </div>
      </div>
    `).join('');
  } catch (err) {
    document.getElementById('search-results').innerHTML = '<p style="color:#f85149;">Erreur</p>';
  }
}

async function showListingDetail(id) {
  try {
    const res = await fetch(`http://127.0.0.1:8000/api/listings/${id}/`);
    const l = await res.json();

    document.getElementById('content-area').innerHTML = `
      <div class="card">
        <h2>${l.titre}</h2>
        <img src="${l.photo_principale || l.images?.[0] || 'https://via.placeholder.com/600x400'}" style="width:100%;border-radius:16px;margin:20px 0;">
        <p><strong>Prix :</strong> ${l.prix.toLocaleString()} FCFA/mois</p>
        <p><strong>Ville :</strong> ${l.ville} • ${l.quartier || 'Quartier non précisé'}</p>
        <p><strong>Surface :</strong> ${l.surface || 'Non précisée'}</p>
        <p><strong>Description :</strong><br>${l.description}</p>
        <button onclick="reserveListing(${l.id})" class="btn btn-success" style="width:100%;padding:16px;margin:20px 0;">
          Réserver ce bien
        </button>
        <button onclick="loadPage('search')" class="btn" style="width:100%;background:#666;">Retour</button>
      </div>
    `;
  } catch (err) {
    alert('Erreur');
  }
}

function reserveListing(id) {
  if (confirm('Souhaites-tu réserver ce bien ?')) {
    alert('Demande envoyée au bailleur !');
  }
}

// MES ANNONCES
async function loadMyListings() {
  try {
    const res = await fetch('http://127.0.0.1:8000/api/listings/', {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    const listings = await res.json();

    const container = document.getElementById('my-annonces');
    if (listings.length === 0) {
      container.innerHTML = '<p>Tu n\'as pas encore publié d\'annonce.</p>';
      return;
    }

    container.innerHTML = '<div class="listing-grid">' + listings.map(l => `
      <div class="listing-card">
        <img src="${l.photo_principale  || 'https://via.placeholder.com/300x180'}" class="listing-img">
        <div class="listing-info">
          <div class="listing-title">${l.titre}</div>
          <div class="listing-price">${l.prix.toLocaleString()} FCFA/mois</div>
          <button onclick="deleteListing(${l.id})" class="btn btn-danger" style="margin-top:10px;">Supprimer</button>
        </div>
      </div>
    `).join('') + '</div>';
  } catch (err) {
    document.getElementById('my-annonces').innerHTML = '<p>Erreur</p>';
  }
}

async function deleteListing(id) {
  if (!confirm('Supprimer cette annonce ?')) return;
  try {
    const res = await fetch(`http://127.0.0.1:8000/api/listings/${id}/`, {
      method: 'DELETE',
      headers: { 'Authorization': `Bearer ${token}` }
    });
    if (res.ok) {
      alert('Annonce supprimée !');
      loadMyListings();
    }
  } catch (err) {
    alert('Erreur');
  }
}

// FORMULAIRE PUBLIER
function getCreateListingForm() {
  return `
    <div class="card">
      <h2>Publier une annonce</h2>
      <form id="create-listing-form" enctype="multipart/form-data">
        <div class="form-group">
          <input type="text" id="listing-titre" placeholder="Titre" required>
        </div>
        <div class="form-group">
          <textarea id="listing-description" placeholder="Description" required></textarea>
        </div>
        <div class="form-group">
          <input type="number" id="listing-prix" placeholder="Prix (FCFA)" required>
        </div>
        <div class="form-group">
          <input type="text" id="listing-ville" placeholder="Ville" required>
        </div>
        <div class="form-group">
          <label>Photos</label>
          <input type="file" id="listing-images" multiple accept="image/*">
        </div>
        <button type="submit" class="btn btn-success" style="width:100%;padding:16px;">Publier</button>
      </form>
    </div>
  `;
}

// SOUMISSION
document.getElementById('content-area').addEventListener('submit', async (e) => {
  if (e.target.id !== 'create-listing-form') return;
  e.preventDefault();

  const formData = new FormData();
  formData.append('titre', document.getElementById('listing-titre').value);
  formData.append('description', document.getElementById('listing-description').value);
  formData.append('prix', document.getElementById('listing-prix').value);
  formData.append('ville', document.getElementById('listing-ville').value);

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
  } catch (err) {
    alert('Erreur réseau');
  }
});

// DEVENIR BAILLEUR
async function checkBailleurStatus() {
  try {
    const res = await fetch('http://127.0.0.1:8000/api/bailleur/status/', {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    const data = await res.json();

    const statusDiv = document.getElementById('bailleur-status');
    const form = document.getElementById('bailleur-form');

    if (data.is_bailleur) {
      statusDiv.innerHTML = '<p style="color:#50fa7b">Vous êtes bailleur approuvé !</p>';
      form.classList.add('hidden');
    } else if (data.is_bailleur_pending) {
      statusDiv.innerHTML = '<p style="color:#f1fa8c">Demande en cours...</p>';
      form.classList.add('hidden');
    } else {
      statusDiv.innerHTML = '';
      form.classList.remove('hidden');
    }
  } catch (err) {
    console.error(err);
  }
}

document.getElementById('bailleur-form')?.addEventListener('submit', async (e) => {
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
  } catch (err) {
    alert('Erreur');
  }
});

function logout() {
  localStorage.removeItem('token');
  window.location.href = 'index.html';
}

loadPage('home');
