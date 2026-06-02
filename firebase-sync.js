// ── Firebase Sync — Mes Menus ─────────────────────────────────
// Chargé APRÈS le script principal : accède aux variables globales
// Remplace le stub fbSync par les vraies fonctions Firebase

(function () {

  firebase.initializeApp({
    apiKey: "AIzaSyAO_ySwaNvN9WDbeYjl-i1Ay9bc4_1nLbU",
    authDomain: "menu-v2-1833b.firebaseapp.com",
    projectId: "menu-v2-1833b",
    storageBucket: "menu-v2-1833b.firebasestorage.app",
    messagingSenderId: "1096544907617",
    appId: "1:1096544907617:web:138b49eb1637d2f30a9520"
  });

  const _db = firebase.firestore();

  // Persistance hors-ligne : fonctionne même sans réseau
  _db.enablePersistence({ synchronizeTabs: true }).catch(err => {
    if (err.code !== 'failed-precondition' && err.code !== 'unimplemented')
      console.warn('[FB] Persistence:', err.code);
  });

  // Référence d'un document d'état
  const _ref = key => _db.collection('etat').doc('cordedda_' + key);

  // ── Écriture : localStorage + Firestore ────────────────────
  // On écrit dans les deux : localStorage pour la réactivité immédiate,
  // Firestore pour la synchro entre appareils
  fbSync = {
    saveActiveMeals(d) {
      try { localStorage.setItem('activeMeals', JSON.stringify(d)); } catch(e) {}
      _ref('activeMeals').set({ v: JSON.stringify(d) });
    },
    saveMealPersons(d) {
      try { localStorage.setItem('mealPersons', JSON.stringify(d)); } catch(e) {}
      _ref('mealPersons').set({ v: JSON.stringify(d) });
    },
    saveChecked(d) {
      try { localStorage.setItem('coursesChecked', JSON.stringify(d)); } catch(e) {}
      _ref('checked').set({ v: JSON.stringify(d) });
    },
    savePrixUser(d) {
      try { localStorage.setItem('prixUser', JSON.stringify(d)); } catch(e) {}
      _ref('prix').set({ v: JSON.stringify(d) });
    },
    saveAnnexe(d) {
      try { localStorage.setItem('annexeItems', JSON.stringify(d)); } catch(e) {}
      _ref('annexe').set({ v: JSON.stringify(d) });
    },
    saveCustomMeals(d) {
      try { localStorage.setItem('customMeals', JSON.stringify(d)); } catch(e) {}
      _ref('customMeals').set({ v: JSON.stringify(d) });
    },
    saveHistorique(entry) {
      _db.collection('historique').doc(entry.date).set({
        date:  entry.date,
        label: entry.label,
        v:     JSON.stringify(entry.noms)
      });
    },
  };

  // ── Listeners temps réel ────────────────────────────────────
  // hasPendingWrites = true → write local pas encore confirmé → on ignore
  // hasPendingWrites = false → donnée confirmée par le serveur → on applique
  // (évite les double-renders sur les writes locaux)
  function _listen(key, onData) {
    _ref(key).onSnapshot(snap => {
      if (!snap.exists || snap.metadata.hasPendingWrites) return;
      try { onData(JSON.parse(snap.data().v)); } catch(e) {}
    });
  }

  _listen('activeMeals', v => {
    activeMeals = v;
    renderPlanning();
    renderCourses();
    renderResume();
  });

  _listen('mealPersons', v => {
    mealPersons = v;
    renderPlanning();
    renderCourses();
    renderCouts();
  });

  _listen('checked', v => {
    checked = v;
    renderCourses();
  });

  _listen('prix', v => {
    prixUser = { ...prixDefaut, ...v };
    renderCouts();
    renderCourses();
  });

  _listen('annexe', v => {
    annexeItems = v;
    annexeNextId = Math.max(...v.map(i => i.id), 20) + 1;
    renderAnnexe();
  });

  _listen('customMeals', v => {
    customMeals = v;
    renderPlanning();
    renderResume();
  });

  // Historique — chargement unique (pas de listener temps réel)
  _db.collection('historique')
    .orderBy('date', 'desc')
    .limit(6)
    .get()
    .then(snap => {
      const items = [];
      snap.forEach(doc => {
        try {
          const d = doc.data();
          items.push({ date: d.date, label: d.label, noms: JSON.parse(d.v || '[]') });
        } catch(e) {}
      });
      if (items.length) {
        historique = items;
        typeof renderHistoriqueInfos === 'function' && renderHistoriqueInfos();
      }
    })
    .catch(e => console.warn('[FB] Historique:', e));

  console.log('[Firebase] Synchronisation active — famille Cordedda');

})();
