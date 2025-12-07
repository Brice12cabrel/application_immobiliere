// js/neu-auth.js — VERSION ULTIME AVEC SUPER ADMIN
const API_BASE = 'http://127.0.0.1:8000/api/auth';

document.addEventListener('DOMContentLoaded', () => {
  const auth = document.querySelector('.neu-auth');
  if (!auth) return;

  let currentUserId = null;

  const screens = ['login', 'signup', 'verify', 'forgot'];

  function show(screen) {
    screens.forEach(s => {
      const el = document.getElementById(s);
      if (el) el.classList.add('hidden');
    });
    const target = document.getElementById(screen);
    if (target) target.classList.remove('hidden');

    auth.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    const tab = auth.querySelector(`.tab[data-screen="${screen}"]`);
    if (tab) tab.classList.add('active');

    if (screen === 'verify') {
      setTimeout(() => auth.querySelector('.code-inputs input')?.focus(), 100);
    }
  }

  // Navigation
  auth.querySelectorAll('.tab').forEach(tab => {
    tab.addEventListener('click', () => show(tab.dataset.screen));
  });

  auth.addEventListener('click', e => {
    const link = e.target.closest('.link');
    if (!link) return;
    const action = link.dataset.action;
    if (action === 'forgot') show('forgot');
    if (action === 'back') show('login');
    if (action === 'resend') resendOTP();
  });

  // === INSCRIPTION ===
  auth.querySelector('#signup .neu-button')?.addEventListener('click', async () => {
    const email = document.getElementById('signup-email').value.trim();
    const pass = document.getElementById('signup-pass').value;
    const confirm = document.getElementById('signup-confirm').value;

    if (!email || !pass || !confirm) return alert('Tous les champs sont requis');
    if (pass !== confirm) {
      document.getElementById('pass-error').classList.remove('hidden');
      return;
    }
    document.getElementById('pass-error').classList.add('hidden');

    try {
      const res = await fetch(`${API_BASE}/register/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          nom: "Utilisateur",
          email,
          mot_de_passe: pass,
          phone_number: "",
          photo_profil: ""
        })
      });

      const data = await res.json();

      if (res.ok) {
        currentUserId = data.user_id;
        alert('Inscription réussie ! Regarde le terminal pour le code à 6 chiffres');
        show('verify');
      } else {
        alert(data.email?.[0] || data.mot_de_passe?.[0] || 'Erreur inscription');
      }
    } catch (err) {
      alert('Erreur réseau');
    }
  });

  // === VÉRIFICATION OTP ===
  auth.querySelector('#verify .neu-button')?.addEventListener('click', async () => {
    const code = Array.from(auth.querySelectorAll('.code-input'))
                     .map(i => i.value)
                     .join('');

    if (code.length !== 6 || !/^\d+$/.test(code)) {
      return alert('Code à 6 chiffres requis');
    }

    try {
      const res = await fetch(`${API_BASE}/verify-otp/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: currentUserId, code })
      });

      const data = await res.json();

      if (data.verified) {
        localStorage.setItem('token', data.token);
        alert('Compte vérifié ! Bienvenue !');
        redirectAfterLogin(data.token);
      } else {
        alert(data.error || 'Code incorrect');
      }
    } catch (err) {
      alert('Erreur de connexion');
    }
  });

  // === CONNEXION  ===
document.querySelector('#login .neu-button')?.addEventListener('click', async () => {
  const email = document.querySelector('#login input[type="email"]').value.trim();
  const password = document.querySelector('#login input[type="password"]').value;

  if (!email || !password) {
    alert('Email et mot de passe requis');
    return;
  }

  try {
    const res = await fetch('http://127.0.0.1:8000/api/auth/login/', {
      method: 'POST',
      headers: { 
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        email: email,
        password: password    // ← C'EST ÇA QUE TON BACKEND ATTEND
      })
    });

    // AFFICHE LA RÉPONSE BRUTE POUR DÉBUG
    const text = await res.text();
    console.log('Réponse brute du serveur:', text);

    let data;
    try {
      data = JSON.parse(text);
    } catch (e) {
      alert('Réponse invalide du serveur');
      return;
    }

    if (res.ok && data.token) {
      localStorage.setItem('token', data.token);
      alert('Connexion réussie !');

      // Redirection selon rôle
      const payload = JSON.parse(atob(data.token.split('.')[1]));
      if (payload.is_superuser) {
        window.location.href = 'super_admin_dashboard.html';
      } else if (payload.role === 'admin') {
        window.location.href = 'admin_dashboard.html';
      } else {
        window.location.href = 'dashboard.html';
      }
    } else {
      alert(data.error || data.detail || 'Identifiants incorrects');
    }
  } catch (err) {
    console.error(err);
    alert('Erreur réseau — serveur Django lancé ?');
  }
});
  // === FONCTION DE REDIRECTION SELON RÔLE ===
  function redirectAfterLogin(token) {
    try {
      const payload = JSON.parse(atob(token.split('.')[1]));

      // SUPER ADMIN (is_superuser) → dashboard spécial
      if (payload.is_superuser) {
        window.location.href = 'super_admin_dashboard.html';
      }
      // Admin normal
      else if (payload.role === 'admin') {
        window.location.href = 'admin_dashboard.html';
      }
      // Locataire ou bailleur
      else {
        window.location.href = 'dashboard.html';
      }
    } catch (e) {
      window.location.href = 'dashboard.html';
    }
  }

  // === MOT DE PASSE OUBLIÉ ===
  document.querySelector('#forgot .neu-button')?.addEventListener('click', async () => {
    const email = document.querySelector('#forgot input[type="email"]').value.trim();
    if (!email) return alert('Email requis');

    try {
      const res = await fetch(`${API_BASE}/forgot-password/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email })
      });

      const data = await res.json();

      if (res.ok) {
        currentUserId = data.user_id;
        alert('Code envoyé ! Regarde le terminal');
        show('verify');
      } else {
        alert(data.error || 'Email inconnu');
      }
    } catch (err) {
      alert('Erreur');
    }
  });

  // === Renvoyer OTP ===
  async function resendOTP() {
    if (!currentUserId) return alert('Aucun utilisateur');
    try {
      const res = await fetch(`${API_BASE}/send-otp/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: currentUserId })
      });
      if (res.ok) alert('Nouveau code dans le terminal !');
    } catch (err) {
      alert('Erreur');
    }
  }

  // Focus code
  auth.querySelectorAll('.code-input').forEach((input, i, arr) => {
    input.addEventListener('input', () => {
      input.value = input.value.replace(/[^0-9]/g, '');
      if (input.value && i < 5) arr[i + 1].focus();
    });
    input.addEventListener('keydown', e => {
      if (e.key === 'Backspace' && !input.value && i > 0) arr[i - 1].focus();
    });
  });

  show('login');
});