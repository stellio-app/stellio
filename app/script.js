const I18N = {
  // ✅ Lecture dynamique de la langue (getter) pour éviter les problèmes de timing
  _langCache: null,
  get lang() {
    if (this._langCache === null) {
      this._langCache = localStorage.getItem('stellio-lang') ||
        document.cookie.replace(/(?:(?:^|.*;\s*)stellio-lang\s*=\s*([^;]*).*$)|^.*$/, "$1") ||
        'fr';
    }
    return this._langCache;
  },
  set lang(value) {
    this._langCache = value;
    localStorage.setItem('stellio-lang', value);
    document.cookie = `stellio-lang=${value}; path=/; max-age=31536000; SameSite=Lax`;
  },
  fallback: 'fr',
  translations: {},
  isReady: false,
  _config: { folder: '/languages' },
  _supportedLangs: {
    fr: { code: 'fr', name: 'Français', native: 'Français', dir: 'ltr' },
    en: { code: 'en', name: 'English', native: 'English', dir: 'ltr' },
    es: { code: 'es', name: 'Español', native: 'Español', dir: 'ltr' },
    it: { code: 'it', name: 'Italian', native: 'Italiano', dir: 'ltr' },
    pt: { code: 'pt', name: 'Portuguese', native: 'Português', dir: 'ltr' },
    ja: { code: 'ja', name: 'Japanese', native: '日本語', dir: 'ltr' },
    de: { code: 'de', name: 'German', native: 'Deutsch', dir: 'ltr' }
  },
  async init(options = {}) {
    const { folder, autoApply = true, onReady = null } = options;
    if (folder) this._config.folder = folder.startsWith('/') ? folder : `/${folder}`;
    try {
      let serverLang = null;
      const baseUrl = window.location.origin;
      try {
        const res = await fetch(`${baseUrl}/api/settings`);
        if (res.ok) {
          const settings = await res.json();
          if (settings?.lang && this._supportedLangs[settings.lang]) {
            serverLang = settings.lang;
          }
        }
      } catch (e) {
        console.debug('[I18N] Backend indisponible, fallback localStorage');
      }
      this._langCache = serverLang || localStorage.getItem('stellio-lang') || document.cookie.replace(/(?:(?:^|.*;\s*)stellio-lang\s*=\s*([^;]*).*$)|^.*$/, "$1") || 'fr';
      await this._loadLang(this.lang);
      if (this.lang !== this.fallback) {
        await this._loadLang(this.fallback);
      }
      document.documentElement.lang = this.lang;
      document.documentElement.dir = this.translations[this.lang]?.__dir || 'ltr';
      if (autoApply) this.apply();
      this.isReady = true;
      if (typeof onReady === 'function') onReady(this.lang);
      document.dispatchEvent(new CustomEvent('i18n:ready', { detail: { lang: this.lang } }));
    } catch (err) {
      console.error('[I18N]  Erreur init:', err);
      this._handleError();
    }
  },
  async _loadLang(langCode) {
    const folder = this._config.folder.startsWith('/') ? this._config.folder : `/${this._config.folder}`;
    const res = await fetch(`${folder}/${langCode}.json`);
    if (!res.ok) throw new Error(`Fichier ${langCode}.json introuvable`);
    this.translations[langCode] = await res.json();
  },
  _handleError() {
    const minimal = { 'app.title': 'Stellio', 'app.loading': 'Loading...', 'app.error': 'Erreur' };
    this.translations[this.fallback] = { ...(this.translations[this.fallback] || {}), ...minimal };
    this.lang = this.fallback;
    document.documentElement.lang = this.fallback;
    document.documentElement.dir = 'ltr';
    this.apply();
    this.isReady = true;
  },
  t(key, params = {}) {
    if (!key) return '';
    const raw = this.translations[this.lang]?.[key] || this.translations[this.fallback]?.[key] || key;
    return this._interpolate(raw, params);
  },
  _interpolate(str, params) {
    if (!params || !Object.keys(params).length) return str;
    return str.replace(/\{\{\s*(\w+)\s*\}\}/g, (_, v) => params[v] !== undefined ? params[v] : `{{${v}}}`);
  },
  tp(key, count, params = {}) {
    const trans = this.translations[this.lang] || this.translations[this.fallback] || {};
    const plural = trans[`${key}_plural`];
    if (!plural) return this.t(key, { ...params, count });
    const forms = plural.split('|').map(s => s.trim());
    let idx = forms.length === 3 ? 2 : (count === 0 && forms[0]?.includes('zero') ? 0 : (count === 1 ? (forms[0]?.includes('zero') ? 1 : 0) : 1));
    return this._interpolate(forms[idx] || forms[forms.length - 1], { ...params, count });
  },
  apply(scope = document) {
    const applyAttr = (selector, attr, paramsAttr) => {
      document.querySelectorAll(selector, scope).forEach(el => {
        const key = el.dataset[attr];
        const params = this._parseParams(el.dataset[paramsAttr]);
        if (key) el[attr === 'i18n' ? 'textContent' : attr.replace('i18n-', '').toLowerCase()] = this.t(key, params);
      });
    };
    applyAttr('[data-i18n]', 'i18n', 'i18nParams');
    applyAttr('[data-i18n-placeholder]', 'i18n-placeholder', 'i18n-placeholderParams');
    applyAttr('[data-i18n-title]', 'i18n-title', 'i18n-titleParams');
    applyAttr('[data-i18n-aria]', 'i18n-aria', 'i18n-ariaParams');
    applyAttr('[data-i18n-html]', 'i18n-html', 'i18n-htmlParams');
    ['language-selector', 'language-selector-auth'].forEach(id => {
      const sel = document.getElementById(id);
      if (sel && sel.value !== this.lang) sel.value = this.lang;
    });
  },
  _parseParams(jsonStr) {
    if (!jsonStr) return {};
    try { return typeof jsonStr === 'string' ? JSON.parse(jsonStr) : jsonStr; }
    catch { return {}; }
  },
  async setLanguage(newLang) {
    if (newLang === this.lang) return;
    if (!this.isReady) {
      document.addEventListener('i18n:ready', () => this.setLanguage(newLang), { once: true });
      return;
    }
    if (!this._supportedLangs[newLang]) return console.warn(`[I18N] Langue "${newLang}" non supportée`);
    try {
      await this._loadLang(newLang);
      this.lang = newLang;
      localStorage.setItem('stellio-lang', newLang);
      document.documentElement.lang = newLang;
      document.documentElement.dir = this.translations[newLang]?.__dir || 'ltr';
      this.apply();
      const baseUrl = window.location.origin;
      fetch(`${baseUrl}/api/settings`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ lang: newLang })
      }).catch(e => console.debug('[I18N] Échec sauvegarde serveur:', e));
      document.dispatchEvent(new CustomEvent('i18n:changed', { detail: { lang: newLang } }));
      if (typeof loadFiles === 'function') loadFiles();
      this.showRestartPopup();
    } catch (err) {
      console.error('[I18N] ❌ Changement échoué:', err);
    }
  },
  showRestartPopup() {
    const title = this.t('settings.restart_required') || 'Redémarrage requis';
    const message = this.t('settings.restart_message') || 'Un redémarrage de l\'application est requis pour appliquer la nouvelle langue.';
    const btnText = this.t('actions.ok') || 'OK';
    const overlay = document.createElement('div');
    overlay.style.cssText = `position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.75); display: flex; align-items: center; justify-content: center; z-index: 100000; backdrop-filter: blur(5px);`;
    const popup = document.createElement('div');
    popup.style.cssText = `background: var(--bg-secondary, #1e2129); color: var(--text-primary, #e6e6e6); padding: 28px; border-radius: 14px; max-width: 380px; width: 90%; box-shadow: 0 12px 35px rgba(0,0,0,0.6); text-align: center; border: 1px solid var(--border, #2a2f3a); animation: popIn 0.25s ease;`;
    popup.innerHTML = `<h3 style="margin: 0 0 10px 0; font-size: 19px; font-weight: 600;">${title}</h3><p style="color: var(--text-muted, #9ca3af); margin: 0 0 24px 0; line-height: 1.5; font-size: 14px;">${message}</p><button id="restart-lang-btn" style="padding: 11px 28px; border: none; border-radius: 8px; background: var(--accent, #4ea1d3); color: #fff; font-weight: 600; cursor: pointer; transition: all 0.2s; font-size: 15px;">${btnText}</button>`;
    overlay.appendChild(popup);
    document.body.appendChild(overlay);
    if (!document.getElementById('restart-popup-style')) {
      const style = document.createElement('style');
      style.id = 'restart-popup-style';
      style.textContent = `@keyframes popIn { from { transform: scale(0.9); opacity: 0; } to { transform: scale(1); opacity: 1; } }`;
      document.head.appendChild(style);
    }
    document.getElementById('restart-lang-btn').addEventListener('click', () => {
      overlay.remove();
      location.reload();
    });
  },
  getAvailableLanguages() {
    return Object.values(this._supportedLangs).map(l => ({ code: l.code, name: l.name, native: l.native, dir: l.dir }));
  },
  has(key, lang = null) {
    const target = lang || this.lang;
    return !!(this.translations[target]?.[key] || this.translations[this.fallback]?.[key]);
  },
  async reload() {
    this.isReady = false;
    this._langCache = null;
    try {
      await this._loadLang(this.lang);
      this.isReady = true;
      this.apply();
    } catch (err) { console.error('[I18N] Reload échoué', err); this.isReady = true; }
  }
};
window.I18N = I18N;

// ============================================
// 🎬 INITIALISATION GLOBALE
// ============================================
const API = window.location.origin;
let allFiles = [];
let filteredFiles = [];
let currentSlicerFile = null;
let currentView = 'gallery';
let currentSort = 'name-asc';
let allTags = [];
let currentTagFile = null;
let activeTagFilters = new Set();
let activeTypeFilters = [];
let currentSizeFilter = null;
let favoriteFiles = new Set();
let showFavoritesOnly = false;
let autoScanInterval = null;
let lastKnownTimestamp = Date.now() / 1000;
let thumbRefreshInterval = null;
let isEditingAccount = false;
let editingAccountPlatform = null;
let tempPhoneCodeHash = null;
const analysisCache = {};
const pendingThumbRequests = new Set();
const pendingMetadataRequests = new Set();
const generatingThumbs = new Set();
let isSelectionMode = false;
let selectedFiles = new Set();
// 🚀 NOUVEAU: Throttle pour les événements hover
const hoverThrottle = new Map();
const HOVER_THROTTLE_MS = 2000;

function translateSortOptions() {
  const sortSelect = document.getElementById('sort-select');
  if (sortSelect) {
    sortSelect.querySelectorAll('option').forEach(opt => {
      if (opt.dataset.i18n) opt.textContent = I18N.t(opt.dataset.i18n);
    });
  }
}

function translateAuthFields() {
  const fields = [
    { id: 'login-username', key: 'auth.username' },
    { id: 'login-password', key: 'auth.password' },
    { id: 'reg-username', key: 'auth.username' },
    { id: 'reg-email', key: 'auth.email_placeholder' },
    { id: 'reg-password', key: 'auth.password' },
    { id: 'reg-password-confirm', key: 'auth.confirm_password' },
    { id: 'forgot-email', key: 'auth.email_placeholder_forgot' },
    { id: 'reset-email', key: 'auth.email_placeholder_recovery' }
  ];
  fields.forEach(field => {
    const el = document.getElementById(field.id);
    if (el && I18N.has(field.key)) el.placeholder = I18N.t(field.key);
  });
}

document.addEventListener('DOMContentLoaded', async () => {
  console.log('[Stellio] DOM chargé, initialisation...');
  await I18N.init({ folder: 'languages', autoApply: true });
  populateLanguageSelectors();
  translateSortOptions();
  translateAuthFields();
  checkAuth();
  setupEventListeners();
  setupDynamicAccountFields();
  initSettings();
  // 🚀 Initialiser la délégation d'événements pour les hover
  setupHoverDelegation();
});

// 🚀 NOUVELLE FONCTION: Délégation d'événements pour les hover (remplace onmouseenter inline)
function setupHoverDelegation() {
  const grid = document.getElementById('files-grid');
  if (!grid) return;
  
  grid.addEventListener('mouseenter', (e) => {
    const card = e.target.closest('.file-card');
    if (!card) return;
    
    const path = card.dataset.path;
    if (!path) return;
    
    // Throttle: éviter les appels répétés
    const now = Date.now();
    const last = hoverThrottle.get(path) || 0;
    if (now - last < HOVER_THROTTLE_MS) return;
    hoverThrottle.set(path, now);
    
    // Demande de miniature si nécessaire
    if (!card.dataset.thumbChecked) {
      const file = filteredFiles.find(f => f.path === path);
      if (file && !file.has_thumb) {
        requestThumbGeneration(path);
      }
      card.dataset.thumbChecked = 'true';
    }
    
    // Chargement métadonnées (non-bloquant)
    loadFileMetadata(path, (meta) => {
      if (!meta) return;
      const safeId = path.replace(/[^\w]/g, '-');
      const dimsEl = document.getElementById(`dims-${safeId}`);
      const weightEl = document.getElementById(`weight-${safeId}`);
      const timeEl = document.getElementById(`time-${safeId}`);
      if (dimsEl) dimsEl.textContent = `${meta.dimensions.x} × ${meta.dimensions.y} × ${meta.dimensions.z} mm`;
      if (weightEl) weightEl.textContent = `PLA: ${meta.weights.pla}g • PETG: ${meta.weights.petg}g`;
      if (timeEl) timeEl.textContent = `~${meta.estimated_time.formatted}`;
    });
  }, true);
}

function populateLanguageSelectors() {
  const selectors = [document.getElementById('language-selector'), document.getElementById('language-selector-auth')].filter(el => el);
  selectors.forEach(selector => {
    selector.innerHTML = '';
    I18N.getAvailableLanguages().forEach(lang => {
      const opt = document.createElement('option');
      opt.value = lang.code;
      opt.textContent = lang.native;
      if (lang.code === I18N.lang) opt.selected = true;
      selector.appendChild(opt);
    });
  });
}

document.addEventListener('i18n:changed', () => {
  translateSortOptions();
  translateAuthFields();
  const authSelector = document.getElementById('language-selector-auth');
  if (authSelector && authSelector.value !== I18N.lang) authSelector.value = I18N.lang;
  const activeBtn = document.querySelector('.nav-btn.active');
  if (activeBtn) {
    const titleKey = activeBtn.dataset.titleKey || 'app.title';
    const iconClass = activeBtn.dataset.icon || 'fa-layer-group';
    const headerTitle = document.getElementById('header-page-title');
    if (headerTitle) headerTitle.innerHTML = `<i class="fa-solid ${iconClass}"></i> ${I18N.t(titleKey)}`;
  }
  const searchInput = document.getElementById('global-search');
  if (searchInput) searchInput.placeholder = I18N.t('search.placeholder');
  I18N.apply();
});

// ============================================
// 🖼️ GÉNÉRATION MINIATURES
// ============================================
window.handleThumbnailError = function (img) {
    // Ne pas cacher si déjà chargée avec succès (évite le clignotement)
    if (img.dataset.loaded === 'true') return;
    
    img.style.display = 'none';
    const loader = img.nextElementSibling;
    if (loader && loader.classList.contains('file-loading')) {
        // Forcer l'affichage du loader
        loader.style.setProperty('display', 'flex', 'important');
        
        if (!loader.querySelector('.fallback-logo')) {
            // Supprimer l'icône cube FontAwesome
            const thumbIcon = loader.querySelector('.thumb-icon');
            if (thumbIcon) thumbIcon.remove();
            
            // Ajouter le logo Stellio
            const fallbackImg = document.createElement('img');
            fallbackImg.src = '/assets/logo-nom-stellio.png';
            fallbackImg.className = 'fallback-logo';
            fallbackImg.style.cssText = 'width:70%;height:70%;object-fit:contain;opacity:0.6;';
            fallbackImg.onerror = function () { this.style.display = 'none'; };
            loader.appendChild(fallbackImg);
        }
    }
};

async function generateThumbnailFrom3D(filePath, cardElement) {
  try {
    const thumbContainer = cardElement.querySelector('.file-thumb');
    if (!thumbContainer) return;
    thumbContainer.innerHTML = `<div class="file-loading"><i class="fa-solid fa-spinner fa-spin"></i></div>`;
    
    const canvas = document.createElement('canvas');
    const size = 400;
    canvas.width = size;
    canvas.height = size;
    
    const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true });
    renderer.setSize(size, size);
    renderer.setPixelRatio(window.devicePixelRatio);
    renderer.setClearColor(0x1a1d23, 1);
    
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(45, 1, 0.1, 10000);
    
    const ambientLight = new THREE.AmbientLight(0x404040, 2);
    scene.add(ambientLight);
    const dirLight1 = new THREE.DirectionalLight(0xffffff, 1.5);
    dirLight1.position.set(50, 50, 50);
    scene.add(dirLight1);
    const dirLight2 = new THREE.DirectionalLight(0x8899ff, 0.8);
    dirLight2.position.set(-50, -30, 30);
    scene.add(dirLight2);
    
    const encodedPath = encodeURIComponent(filePath);
    const response = await fetch(`${API}/api/file/data?path=${encodedPath}`);
    if (!response.ok) {
      if (response.status !== 404) console.warn(`[Thumbnail] Erreur (${response.status}): ${filePath}`);
      throw new Error(I18N.t('toast.file_not_found'));
    }
    
    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const ext = filePath.split('.').pop().toLowerCase();
    
    let geometry = null;
    let material = null;
    
    if (ext === 'stl') {
      const loader = new THREE.STLLoader();
      geometry = await new Promise((resolve, reject) => loader.load(url, resolve, undefined, reject));
    } else if (ext === 'obj') {
      const loader = new THREE.OBJLoader();
      const obj = await new Promise((resolve, reject) => loader.load(url, resolve, undefined, reject));
      obj.traverse(child => { if (child.isMesh) geometry = child.geometry; });
    } else {
      throw new Error(I18N.t('toast.invalid_format'));
    }
    
    if (!geometry) throw new Error(I18N.t('toast.empty_geometry'));
    
    geometry.computeBoundingBox();
    const center = new THREE.Vector3();
    geometry.boundingBox.getCenter(center);
    geometry.translate(-center.x, -center.y, -center.z);
    
    const size3D = new THREE.Vector3();
    geometry.boundingBox.getSize(size3D);
    const maxDim = Math.max(size3D.x, size3D.y, size3D.z);
    
    material = new THREE.MeshPhongMaterial({ color: 0x4ea1d3, specular: 0x111111, shininess: 200, flatShading: false });
    const mesh = new THREE.Mesh(geometry, material);
    scene.add(mesh);
    
    const fov = 45 * (Math.PI / 180);
    const distance = Math.abs(maxDim / 2 / Math.tan(fov / 2)) * 1.5;
    camera.position.set(distance, distance, distance);
    camera.lookAt(0, 0, 0);
    
    renderer.render(scene, camera);
    const imageData = canvas.toDataURL('image/png');
    
    thumbContainer.innerHTML = `<img src="${imageData}" alt="${filePath}" style="width:100%;height:100%;object-fit:cover;border-radius:8px;"><div class="file-overlay"><span class="file-ext">${ext.toUpperCase()}</span></div>`;
    
    // 🚀 Nettoyage mémoire THREE.js
    URL.revokeObjectURL(url);
    if (geometry) geometry.dispose();
    if (material) material.dispose();
    renderer.dispose();
    
  } catch (error) {
    if (error.message !== I18N.t('toast.file_not_found')) {
      console.error(`[Thumbnail] Erreur ${filePath}:`, error);
    }
    const thumbContainer = cardElement.querySelector('.file-thumb');
    if (thumbContainer) {
      thumbContainer.innerHTML = `<div class="thumb-fallback" style="display:flex;align-items:center;justify-content:center;width:100%;height:100%;background:var(--bg-tertiary,#2a2f3a);"><img src="assets/logo-nom-stellio.png" alt="${I18N.t('toast.corrupted_file')}" style="width:70%;height:70%;object-fit:contain;opacity:0.6;" onerror="window.handleThumbnailError(this)"></div>`;
    }
  }
}

function generateVisibleThumbnails() {
  const cards = document.querySelectorAll('.file-card');
  cards.forEach((card, index) => {
    const filePath = card.dataset.path;
    const thumbImg = card.querySelector('.file-thumb img');
    if (!thumbImg || !thumbImg.src || thumbImg.src.includes('data:image')) {
      setTimeout(() => generateThumbnailFrom3D(filePath, card), index * 100);
    }
  });
}

// ============================================
// 🎨 THÈME & APPEARANCE
// ============================================
(function applyThemeOnLoad() {
  const savedTheme = localStorage.getItem('stellio-theme') || 'dark';
  const savedFabricant = localStorage.getItem('stellio-fabricant') || 'stellio';
  if (savedTheme === 'auto') {
    const isLight = window.matchMedia && window.matchMedia('(prefers-color-scheme: light)').matches;
    document.documentElement.setAttribute('data-theme', isLight ? 'light' : 'dark');
  } else {
    document.documentElement.setAttribute('data-theme', savedTheme);
  }
  document.documentElement.setAttribute('data-fabricant', savedFabricant);
  console.log('[Theme] ✅ Appliqué:', savedTheme, savedFabricant);
})();

// ============================================
// 🔄 GESTION MINIATURES LAZY
// ============================================
window.requestThumbGeneration = async function (filePath) {
  if (generatingThumbs.has(filePath) || pendingThumbRequests.has(filePath)) return;
  pendingThumbRequests.add(filePath);
  generatingThumbs.add(filePath);
  try {
    const res = await fetch(`${API}/api/thumb/generate-now`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ path: filePath })
    });
    const data = await res.json();
    if (data.success && !data.cached) {
      setTimeout(() => {
        refreshFileThumbnail(filePath);
        generatingThumbs.delete(filePath);
        pendingThumbRequests.delete(filePath);
      }, 2500);
    } else if (data.cached) {
      refreshFileThumbnail(filePath);
      generatingThumbs.delete(filePath);
      pendingThumbRequests.delete(filePath);
    } else {
      generatingThumbs.delete(filePath);
      pendingThumbRequests.delete(filePath);
    }
  } catch (err) {
    console.error('[Thumb Gen] Erreur:', err);
    generatingThumbs.delete(filePath);
    pendingThumbRequests.delete(filePath);
  }
};

function refreshFileThumbnail(filePath) {
  const card = document.querySelector(`.file-card[data-path="${CSS.escape(filePath)}"]`);
  if (!card) return;
  const img = card.querySelector('.file-thumb img');
  const loader = card.querySelector('.file-loading');
  if (img) {
    const newSrc = `${API}/api/thumb?path=${encodeURIComponent(filePath)}&t=${Date.now()}`;
    const testImg = new Image();
    testImg.onload = () => {
      img.src = newSrc;
      img.style.display = 'block';
      if (loader) loader.style.display = 'none';
    };
    testImg.onerror = () => window.handleThumbnailError(img);
    testImg.src = newSrc;
  }
}

// ============================================
// 📊 MÉTADONNÉES 3D
// ============================================
window.requestMetadataAnalysis = async function (filePath, callback) {
  if (analysisCache[filePath]) {
    callback(analysisCache[filePath]);
    return;
  }
  if (pendingMetadataRequests.has(filePath)) return;
  pendingMetadataRequests.add(filePath);
  try {
    await fetch(`${API}/api/files/analyze-now`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ path: filePath })
    });
    setTimeout(async () => {
      try {
        const res = await fetch(`${API}/api/files/analyze`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ path: filePath })
        });
        const data = await res.json();
        if (data.success) {
          if (Object.keys(analysisCache).length > 100) {
            delete analysisCache[Object.keys(analysisCache)[0]];
          }
          analysisCache[filePath] = data.metadata;
          callback(data.metadata);
        } else callback(null);
      } catch (err) {
        console.error('[Metadata] Erreur:', err);
        callback(null);
      }
      pendingMetadataRequests.delete(filePath);
    }, 1500);
  } catch (err) {
    console.error('[Metadata Gen] Erreur:', err);
    callback(null);
    pendingMetadataRequests.delete(filePath);
  }
};

// ============================================
//  FAVORIS
// ============================================
async function loadFavorites() {
  try {
    const res = await fetch(`${API}/api/favorites`);
    if (res.ok) {
      favoriteFiles = new Set(await res.json());
      console.log('[Favoris] ✅ Chargés:', favoriteFiles.size);
      updateFavoritesCount();
    }
  } catch (err) {
    console.error('[Favoris] Erreur:', err);
  }
}

window.toggleFavorite = async function (filePath, event) {
  if (event) {
    event.preventDefault();
    event.stopPropagation();
  }
  try {
    const res = await fetch(`${API}/api/favorites`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ path: filePath })
    });
    if (res.ok) {
      const data = await res.json();
      if (data.favorited) {
        favoriteFiles.add(filePath);
        showToast(I18N.t('toast.favorites_added'), 'success');
      } else {
        favoriteFiles.delete(filePath);
        showToast(I18N.t('toast.favorites_removed'), 'info');
        if (favoriteFiles.size === 0 && showFavoritesOnly) {
          showFavoritesOnly = false;
          const navBtn = document.getElementById('nav-favorites-btn');
          if (navBtn) navBtn.classList.remove('active');
          const btn = document.getElementById('favorites-filter-btn');
          if (btn) btn.classList.remove('active');
          const headerTitle = document.getElementById('header-page-title');
          if (headerTitle) headerTitle.innerHTML = `<i class="fa-solid fa-layer-group"></i> ${I18N.t('nav.library')}`;
          showToast(I18N.t('toast.no_favorites'), 'info');
        }
      }
      renderFiles();
      updateFavoritesCount();
    }
  } catch (err) {
    console.error('[Favoris] Erreur:', err);
    showToast(I18N.t('toast.error'), 'error');
  }
  return false;
};

function updateFavoritesCount() {
  const countEl = document.getElementById('favorites-count');
  if (countEl) {
    const count = favoriteFiles.size;
    countEl.textContent = count;
    countEl.style.display = count > 0 ? 'inline-block' : 'none';
  }
}

function toggleFavoritesFilter(forceState = null) {
    console.group('[DEBUG] toggleFavoritesFilter()');
    console.log('  forceState =', forceState);
    console.log('  showFavoritesOnly =', showFavoritesOnly);
    
    if (forceState === null) {
        showFavoritesOnly = !showFavoritesOnly;
    } else {
        if (showFavoritesOnly === forceState) {
            console.log('  ⚠️ Déjà dans cet état');
            console.groupEnd();
            return;
        }
        showFavoritesOnly = forceState;
    }
    
    console.log('  Nouveau état :', showFavoritesOnly);
    
    // Mettre à jour les classes active des boutons
    document.querySelectorAll('.nav-btn').forEach(btn => {
        if (btn.id === 'nav-favorites-btn') {
            btn.classList.toggle('active', showFavoritesOnly);
        } else if (btn.dataset.page === 'library') {
            btn.classList.toggle('active', !showFavoritesOnly);
        } else {
            btn.classList.remove('active');
        }
    });
    
    // Mettre à jour le titre
    const headerTitle = document.getElementById('header-page-title');
    if (headerTitle) {
        const titleKey = showFavoritesOnly ? 'nav.favorites' : 'nav.library';
        const iconClass = showFavoritesOnly ? 'fa-star' : 'fa-layer-group';
        headerTitle.innerHTML = `<i class="fa-solid ${iconClass}"></i> ${I18N.t(titleKey)}`;
    }
    
    // Filtrer les fichiers
    if (showFavoritesOnly) {
        const beforeCount = filteredFiles.length;
        filteredFiles = allFiles.filter(f => favoriteFiles.has(f.path));
        console.log(`✅ Filtrage : ${beforeCount} → ${filteredFiles.length}`);
    } else {
        filteredFiles = [...allFiles];
    }
    
    applySorting();
    renderFiles();
    updateSidebarCounts(filteredFiles);
    updateFavoritesCount();
    
    console.groupEnd();
}

window.toggleFavoritesFilterFromNav = function () {
    console.log('[Favoris] Activation depuis navigation');
    
    // 1️⃣ Si on n'est pas sur la page Bibliothèque, y naviguer
    const libraryPage = document.getElementById('page-library');
    const currentPage = document.querySelector('.page.active');
    
    if (libraryPage && currentPage !== libraryPage) {
        // Cacher toutes les pages
        document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
        // Afficher la page Bibliothèque
        libraryPage.classList.add('active');
    }
    
    // 2️⃣ Mettre à jour les boutons actifs (TOUS désactivés sauf Favoris)
    document.querySelectorAll('.nav-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    
    const favBtn = document.getElementById('nav-favorites-btn');
    if (favBtn) favBtn.classList.add('active');
    
    // 3️ Mettre à jour le header
    const headerTitle = document.getElementById('header-page-title');
    if (headerTitle) {
        headerTitle.innerHTML = `<i class="fa-solid fa-star"></i> ${I18N.t('nav.favorites')}`;
    }
    
    // 4️⃣ Activer le filtre favoris (sans toggle)
    if (!showFavoritesOnly) {
        showFavoritesOnly = true;
        filteredFiles = allFiles.filter(f => favoriteFiles.has(f.path));
        applySorting();
        renderFiles();
        updateSidebarCounts(filteredFiles);
        updateFavoritesCount();
    }
};

// ============================================
// 🗜️ DÉCOMPRESSION
// ============================================
async function decompressFile(filePath, event) {
  if (event) {
    event.preventDefault();
    event.stopPropagation();
  }
  try {
    const res = await fetch(`${API}/api/files/decompress`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ file_path: filePath })
    });
    const data = await res.json();
    if (!res.ok) {
      showToast(`❌ ${data.error || I18N.t('toast.extraction_error')}`, 'error');
      return;
    }
    const archiveName = filePath.split('/').pop() || filePath;
    showDecompressConfirmToast(archiveName, data.found_3d_files?.length || 0, filePath, data.found_3d_files || []);
  } catch (err) {
    console.error('[Decompress] Erreur:', err);
    showToast(I18N.t('toast.server_error'), 'error');
  }
}

function showDecompressConfirmToast(archiveName, extractedCount, archivePath, extractedFiles) {
  const container = document.getElementById('toast-container');
  if (!container) return;
  const toast = document.createElement('div');
  toast.className = 'toast confirmation';
  toast.innerHTML = `<p class="toast-message">🗜️ ${I18N.t('toast.extract_success')}</p><p class="toast-submessage">${extractedCount} ${I18N.t('toast.extract_found')} "${escapeHtml(archiveName)}".<br>${I18N.t('toast.delete_source')}</p><div class="toast-actions"><button class="btn-cancel" onclick="dismissDecompressToast(this)">${I18N.t('actions.save')}</button><button class="btn-confirm" onclick="confirmArchiveCleanup('${escapeJs(archivePath)}', this)">🗑️ ${I18N.t('actions.delete')}</button></div>`;
  container.appendChild(toast);
  setTimeout(() => {
    if (toast.parentNode) {
      toast.style.opacity = '0';
      toast.style.transform = 'translateX(100%)';
      setTimeout(() => toast.remove(), 300);
    }
  }, 10000);
}

window.dismissDecompressToast = function (btn) {
  const toast = btn.closest('.toast');
  if (toast) {
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(100%)';
    setTimeout(() => toast.remove(), 300);
  }
  showToast(I18N.t('toast.extract_keep'), 'info');
};

window.confirmArchiveCleanup = async function (archivePath, btn) {
  const toast = btn.closest('.toast');
  const buttons = toast.querySelectorAll('button');
  buttons.forEach(b => b.disabled = true);
  try {
    const res = await fetch(`${API}/api/files/cleanup-archive`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ archive_path: archivePath })
    });
    const data = await res.json();
    if (res.ok) {
      showToast(I18N.t('toast.archive_deleted'), 'success');
      loadFiles();
    } else {
      showToast(`❌ ${data.error || I18N.t('toast.archive_cleanup_error')}`, 'error');
    }
  } catch (err) {
    console.error('[Cleanup] Erreur:', err);
    showToast(I18N.t('toast.connection_error'), 'error');
  } finally {
    if (toast) {
      toast.style.opacity = '0';
      toast.style.transform = 'translateX(100%)';
      setTimeout(() => toast.remove(), 300);
    }
  }
};

// ============================================
// 🔐 AUTHENTIFICATION TELEGRAM
// ============================================
function showTelegramCodeModal() {
  return new Promise((resolve) => {
    const overlay = document.createElement('div');
    overlay.className = 'modal-overlay';
    overlay.style.cssText = `position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0, 0, 0, 0.7); display: flex; align-items: center; justify-content: center; z-index: 10000; animation: fadeIn 0.2s ease;`;
    const modal = document.createElement('div');
    modal.style.cssText = `background: var(--bg-secondary, #1e2129); border-radius: 16px; padding: 24px; max-width: 420px; width: 90%; box-shadow: 0 12px 40px rgba(0, 0, 0, 0.5); border: 1px solid var(--border, #2a2f3a); animation: slideIn 0.3s ease;`;
    modal.innerHTML = `<div style="display: flex; align-items: center; gap: 12px; margin-bottom: 20px;"><i class="fa-brands fa-telegram" style="font-size: 28px; color: #0088cc;"></i><h3 style="margin: 0; color: var(--text-primary, #e6e6e6); font-size: 18px;">${I18N.t('auth.code_placeholder')}</h3></div><p style="color: var(--text-muted, #9ca3af); margin-bottom: 20px; line-height: 1.5;">${I18N.t('toast.telegram_code_sent')}<br>${I18N.t('modal.telegram_tip_5')}</p><input type="text" id="telegram-code-input" placeholder="${I18N.t('auth.code_placeholder')}" maxlength="10" style="width: 100%; padding: 14px 16px; border: 2px solid var(--border, #2a2f3a); border-radius: 10px; background: var(--bg-primary, #15181e); color: var(--text-primary, #e6e6e6); font-size: 18px; letter-spacing: 4px; text-align: center; margin-bottom: 20px; transition: border-color 0.2s;" autofocus><div style="display: flex; gap: 12px; justify-content: flex-end;"><button id="telegram-cancel-btn" style="padding: 12px 24px; border: none; border-radius: 10px; background: var(--bg-tertiary, #2a2f3a); color: var(--text-primary, #e6e6e6); cursor: pointer; font-weight: 500; transition: background 0.2s;">${I18N.t('actions.cancel')}</button><button id="telegram-verify-btn" style="padding: 12px 24px; border: none; border-radius: 10px; background: var(--accent, #4ea1d3); color: white; cursor: pointer; font-weight: 500; transition: background 0.2s;">${I18N.t('auth.reset')}</button></div>`;
    overlay.appendChild(modal);
    document.body.appendChild(overlay);
    if (!document.getElementById('telegram-modal-styles')) {
      const style = document.createElement('style');
      style.id = 'telegram-modal-styles';
      style.textContent = `@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } } @keyframes slideIn { from { transform: translateY(-20px); opacity: 0; } to { transform: translateY(0); opacity: 1; } }`;
      document.head.appendChild(style);
    }
    const input = modal.querySelector('#telegram-code-input');
    const verifyBtn = modal.querySelector('#telegram-verify-btn');
    const cancelBtn = modal.querySelector('#telegram-cancel-btn');
    const submitCode = () => {
      const code = input.value.trim();
      overlay.remove();
      resolve(code || null);
    };
    verifyBtn.addEventListener('click', submitCode);
    cancelBtn.addEventListener('click', () => { overlay.remove(); resolve(null); });
    input.addEventListener('keypress', (e) => { if (e.key === 'Enter') submitCode(); });
    overlay.addEventListener('click', (e) => { if (e.target === overlay) { overlay.remove(); resolve(null); } });
    setTimeout(() => input.focus(), 100);
  });
}

// ============================================
// ⚙️ CHAMPS DYNAMIQUES COMPTES
// ============================================
function setupDynamicAccountFields() {
  const platformSelect = document.getElementById('account-platform');
  const emailPassGroup = document.getElementById('auth-email-pass-group');
  const telegramGroup = document.getElementById('auth-telegram-group');
  if (!platformSelect || !emailPassGroup || !telegramGroup) {
    console.warn('[Setup Account Fields] Éléments manquants');
    return;
  }
  let apiKeyGroup = document.getElementById('auth-api-key-group');
  if (!apiKeyGroup) {
    apiKeyGroup = document.createElement('div');
    apiKeyGroup.id = 'auth-api-key-group';
    apiKeyGroup.className = 'input-group';
    apiKeyGroup.style.display = 'none';
    apiKeyGroup.innerHTML = `<label>${I18N.t('form.password')}</label><input type="password" id="account-api-key" placeholder="ct_xxxxxxxxxxxxxxxx" autocomplete="off"><small style="color: var(--text-muted); margin-top: 4px; display: block;" id="api-key-help">${I18N.t('form.telegram_help')} <a href="https://cults3d.com/fr/compte/api" target="_blank" style="color: var(--accent); text-decoration: none;">cults3d.com/fr/compte/api</a></small>`;
    telegramGroup.parentNode.insertBefore(apiKeyGroup, telegramGroup);
  }
  const emailInput = document.getElementById('account-email');
  const emailLabel = document.getElementById('account-email-label');
  const phoneInput = document.getElementById('account-phone');
  const passwordInput = document.getElementById('account-password');
  const apiKeyInput = document.getElementById('account-api-key');
  const tgApiIdInput = document.getElementById('account-telegram-api-id');
  const tgApiHashInput = document.getElementById('account-telegram-api-hash');
  const apiKeyHelp = document.getElementById('api-key-help');
  
  function toggleFields() {
    const platform = platformSelect.value;
    emailPassGroup.style.display = 'none';
    telegramGroup.style.display = 'none';
    apiKeyGroup.style.display = 'none';
    [emailInput, passwordInput, phoneInput, apiKeyInput, tgApiIdInput, tgApiHashInput].forEach(el => { if (el) el.required = false; });
    if (apiKeyHelp) apiKeyHelp.innerHTML = `${I18N.t('form.telegram_help')} <a href="https://cults3d.com/fr/compte/api" target="_blank" style="color: var(--accent); text-decoration: none;">cults3d.com/fr/compte/api</a>`;
    
    if (platform === 'telegram') {
      telegramGroup.style.display = 'block';
      if (phoneInput) { phoneInput.required = true; phoneInput.type = 'tel'; }
      if (tgApiIdInput) tgApiIdInput.required = true;
      if (tgApiHashInput) tgApiHashInput.required = true;
    } else if (platform === 'cults') {
      apiKeyGroup.style.display = 'block';
      if (apiKeyInput) { apiKeyInput.required = true; apiKeyInput.placeholder = 'ct_xxxxxxxxxxxxxxxx'; }
    } else if (platform === 'thingiverse') {
      apiKeyGroup.style.display = 'block';
      if (apiKeyInput) { apiKeyInput.required = true; apiKeyInput.placeholder = '61b5cb9745ad95914be50e32f537590d'; }
      if (apiKeyHelp) apiKeyHelp.innerHTML = `${I18N.t('form.telegram_help')} <a href="https://www.thingiverse.com/apps/create" target="_blank" style="color: var(--accent); text-decoration: none;">thingiverse.com/apps/create</a>`;
    } else if (platform === 'printables') {
      // ✅ NOUVEAU : Printables - Pas de compte requis pour les modèles publics
      apiKeyGroup.style.display = 'block';
      if (apiKeyInput) { 
        apiKeyInput.required = false; 
        apiKeyInput.placeholder = 'Optionnel (pour modèles privés)'; 
      }
      if (apiKeyHelp) {
        apiKeyHelp.innerHTML = `
          <div style="padding: 8px; background: rgba(233, 91, 37, 0.1); border-left: 3px solid #e95b25; border-radius: 4px; margin-top: 4px;">
            <i class="fa-solid fa-circle-info" style="color: #e95b25;"></i>
            <small style="color: var(--text-secondary);">
              <strong>Printables</strong> : Aucun compte requis pour les modèles publics.<br>
              Laissez ce champ vide pour télécharger librement.<br>
              <a href="https://www.printables.com" target="_blank" style="color: var(--accent); text-decoration: none;">printables.com</a>
            </small>
          </div>
        `;
      }
	} else if (platform === 'printables') {
	  apiKeyGroup.style.display = 'block';
	  if (apiKeyInput) { 
		apiKeyInput.required = false; 
		apiKeyInput.placeholder = 'Optionnel (pour modèles privés)'; 
	  }
	  if (apiKeyHelp) {
		apiKeyHelp.innerHTML = `
		  <div style="padding: 8px; background: rgba(233, 91, 37, 0.1); border-left: 3px solid #e95b25; border-radius: 4px; margin-top: 4px;">
			<i class="fa-solid fa-circle-info" style="color: #e95b25;"></i>
			<small style="color: var(--text-secondary);">
			  <strong>Printables</strong> : Aucun compte requis pour les modèles publics.<br>
			  Laissez ce champ vide pour télécharger librement.<br>
			  <a href="https://www.printables.com" target="_blank" style="color: var(--accent); text-decoration: none;">printables.com</a>
			</small>
		  </div>
		`;
	  }
	} else if (platform === 'makerworld') {
	  // ✅ MakerWorld - Cookie de session requis pour les modèles privés
	  apiKeyGroup.style.display = 'block';
	  if (apiKeyInput) { 
		apiKeyInput.required = false; 
		apiKeyInput.placeholder = 'Cookie de session MakerWorld';
		apiKeyInput.type = 'text';
	  }
	  if (apiKeyHelp) {
		apiKeyHelp.innerHTML = `
		  <div style="padding: 8px; background: rgba(0, 150, 136, 0.1); border-left: 3px solid #009688; border-radius: 4px; margin-top: 4px;">
			<i class="fa-solid fa-circle-info" style="color: #009688;"></i>
			<small style="color: var(--text-secondary);">
			  <strong>MakerWorld</strong> : Cookie de session requis pour les modèles privés.<br>
			  <a href="https://www.makerworld.com" target="_blank" style="color: var(--accent); text-decoration: none;">makerworld.com</a>
			</small>
		  </div>
		`;
	  }
    } else if (platform) {
      emailPassGroup.style.display = 'block';
      if (emailInput) { emailInput.required = true; emailInput.type = 'email'; }
      if (emailLabel) emailLabel.textContent = I18N.t('form.email');
      if (passwordInput) passwordInput.required = true;
    }
  }
  
  platformSelect.addEventListener('change', toggleFields);
  toggleFields();
  
  window.openAccountModal = function (platform = null, editMode = false) {
      const modal = document.getElementById('modal-account');
      if (modal) {
          modal.classList.remove('hidden');
        
          // ✅ AJOUTER CETTE LIGNE : Charger le cookie MakerWorld
          loadMakerWorldCookie();
        
          setTimeout(() => {
              if (editMode && platform) {
                  loadAccountForEdit(platform);
              } else {
                  const platformSelect = document.getElementById('account-platform');
                  if (platformSelect) platformSelect.value = '';
                  if (typeof toggleFields === 'function') toggleFields();
                  if (typeof resetAccountForm === 'function') resetAccountForm();
                  isEditingAccount = false;
                  editingAccountPlatform = null;
              }
          }, 100);
      }
  };
}

async function saveMakerWorldCookie() {
    const cookie = document.getElementById('makerworld-cookie').value.trim();
    
    try {
        const res = await fetch(`${API}/api/settings/makerworld-cookie`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ cookie: cookie || null })
        });
        
        if (res.ok) {
            showToast('Cookie MakerWorld sauvegardé', 'success');
        } else {
            const data = await res.json();
            showToast(data.error || 'Erreur lors de la sauvegarde', 'error');
        }
    } catch (err) {
        showToast('Erreur de connexion', 'error');
    }
}

// ============================================
// 🍪 CHARGEMENT COOKIE MAKERWORLD
// ============================================
async function loadMakerWorldCookie() {
    try {
        const res = await fetch(`${API}/api/accounts/makerworld`);
        if (res.ok) {
            const data = await res.json();
            const cookieField = document.getElementById('account-makerworld-cookie');
            if (cookieField && data.cookie) {
                cookieField.value = data.cookie;
            }
        }
    } catch (err) {
        console.debug('[MakerWorld] Cookie non chargé:', err);
    }
}

function showMakerWorldCookieHelp() {
    const help = `
Pour obtenir votre cookie de session MakerWorld :

1. Ouvrez https://www.makerworld.com dans votre navigateur
2. Connectez-vous à votre compte
3. Appuyez sur F12 pour ouvrir les DevTools
4. Allez dans l'onglet "Application" → "Cookies" → "https://www.makerworld.com"
5. Trouvez le cookie nommé "sessionid" ou similaire
6. Copiez sa valeur (colonne "Value")
7. Collez-la dans le champ ci-dessus

OU

Copiez tout l'en-tête "Cookie" depuis l'onglet "Network" après avoir chargé une page MakerWorld.
    `;
    alert(help);
}

async function loadAccountForEdit(platform) {
  try {
    const res = await fetch(`${API}/api/accounts/${platform}`);
    if (!res.ok) throw new Error(I18N.t('toast.file_not_found'));
    const account = await res.json();
    isEditingAccount = true;
    editingAccountPlatform = platform;
    const platformSelect = document.getElementById('account-platform');
    platformSelect.value = platform;
    document.getElementById('account-email').value = account.email || '';
    document.getElementById('account-password').value = '';
    document.getElementById('account-api-key').value = '';
    document.getElementById('account-phone').value = '';
    document.getElementById('account-telegram-api-id').value = '';
    document.getElementById('account-telegram-api-hash').value = '';
    document.getElementById('account-platform')?.dispatchEvent(new Event('change'));
  } catch (err) {
    showToast(I18N.t('toast.error'), 'error');
    console.error('[loadAccountForEdit]', err);
    isEditingAccount = false;
  }
}

function resetAccountForm() {
  ['account-email', 'account-password', 'account-api-key', 'account-phone', 'account-telegram-api-id', 'account-telegram-api-hash'].forEach(id => { const el = document.getElementById(id); if (el) el.value = ''; });
}

// ============================================
// 🔐 AUTHENTIFICATION UTILISATEUR
// ============================================
async function checkAuth() {
  try {
    const firstLaunchRes = await fetch(`${API}/api/auth/first-launch`);
    const firstLaunchData = await firstLaunchRes.json();
    if (firstLaunchData.first_launch) {
      showPanel('register-panel');
      return;
    }
    showPanel('login-panel');
    try {
      const meRes = await fetch(`${API}/api/auth/me`);
      if (meRes.ok) {
        const userData = await meRes.json();
        const filesPromise = fetch(`${API}/api/files`).then(res => res.ok ? res.json() : null).catch(() => null);
        showApp(userData.user, filesPromise);
        return;
      }
    } catch (authErr) { /* Non authentifié */ }
  } catch (err) {
    console.error('[checkAuth] Erreur:', err);
    showPanel('login-panel');
  }
}

function showPanel(panelId) {
  document.querySelectorAll('.auth-panel').forEach(p => p.classList.add('hidden'));
  document.getElementById(panelId)?.classList.remove('hidden');
  document.querySelectorAll('[data-i18n-placeholder]').forEach(el => { el.placeholder = I18N.t(el.dataset.i18nPlaceholder); });
  I18N.apply();
  translateAuthFields();
}

function showApp(user, filesPromise = null) {
    document.getElementById('auth-screen').classList.add('hidden');
    document.getElementById('app-screen').classList.remove('hidden');
    document.getElementById('current-username').textContent = user.username;
    loadSources();
    loadAccounts();
    loadTags();
    loadFavorites();
    loadPrinters();
    checkAccountsStatusOnStartup();
    checkTelegramConnection();
    
    // ✅ Démarrer le monitoring de progression des miniatures
    startThumbProgressMonitor();
    
    if (filesPromise) {
        filesPromise.then(async (cachedFiles) => {
            if (cachedFiles && Array.isArray(cachedFiles)) {
                allFiles = cachedFiles;
                filteredFiles = [...allFiles];
                applySorting();
                renderFiles();
                startThumbnailGeneration();
                updateSidebarCounts(filteredFiles);
                updateFooterCounts();
            } else {
                loadFiles();
            }
        });
    } else {
        loadFiles();
    }
    startThumbAutoRefresh();
    startAutoFileMonitor();
}

function translateApiResponse(key, fallback) {
  return I18N.has(key) ? I18N.t(key) : fallback;
}

function showToast(message, type = 'info') {
  const translated = I18N.has(`toast.${message}`) ? I18N.t(`toast.${message}`) : message;
  const container = document.getElementById('toast-container');
  if (!container) return;
  const icons = { success: 'fa-check-circle', error: 'fa-exclamation-circle', info: 'fa-info-circle', warning: 'fa-exclamation-triangle' };
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.innerHTML = `<i class="fa-solid ${icons[type] || icons.info}"></i><span class="toast-message">${escapeHtml(translated)}</span>`;
  container.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(100%)';
    toast.style.transition = 'all 0.3s ease';
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}

// ============================================
// 📡 MONITORING & AUTO-SCAN
// ============================================
async function checkAccountsStatusOnStartup() {
  try {
    const res = await fetch(`${API}/api/accounts/status`);
    if (res.ok) {
      const status = await res.json();
      updateThingiverseFooterStatus(status.thingiverse, status.thingiverse ? null : I18N.t('settings.no_accounts'));
      updateCultsFooterStatus(status.cults, status.cults ? null : I18N.t('settings.no_accounts'));
      updateTelegramFooterStatus(status.telegram, status.telegram ? null : I18N.t('settings.no_accounts'));
      console.log('[Startup] ✅ Statuts récupérés');
    }
  } catch (err) {
    console.error('[Startup] ❌ Erreur statuts comptes:', err);
  }
}

async function checkTelegramConnection() {
  try {
    const res = await fetch(`${API}/api/telegram/status`);
    const data = await res.json();
    const statusEl = document.querySelector('.source-item[data-platform="telegram"] .tg-status');
    if (statusEl) {
      if (data.connected) {
        statusEl.innerHTML = `<span style="color: var(--success);">● ${I18N.t('toast.telegram_connected')}</span>`;
      } else {
        statusEl.innerHTML = `<span style="color: var(--danger);">● ${I18N.t('toast.connection_fail')}</span>`;
      }
    }
    updateTelegramFooterStatus(data.connected, data.error);
  } catch (err) {
    console.error("[Telegram Status] Erreur:", err);
    const statusEl = document.querySelector('.source-item[data-platform="telegram"] .tg-status');
    if (statusEl) statusEl.innerHTML = `<span style="color: var(--danger);">● ${I18N.t('toast.error')}</span>`;
    updateTelegramFooterStatus(false, I18N.t('toast.error'));
  }
}

function startAutoFileMonitor() {
  if (autoScanInterval) clearInterval(autoScanInterval);
  autoScanInterval = setInterval(async () => {
    try {
      const changesRes = await fetch(`${API}/api/files/changes?since=${lastKnownTimestamp}`);
      if (!changesRes.ok) return;
      const changesData = await changesRes.json();
      if (changesData.has_changes) {
        const tagParams = activeTagFilters.size > 0 ? `&tags=${encodeURIComponent([...activeTagFilters].join(','))}` : '';
        const filesRes = await fetch(`${API}/api/files?since=${lastKnownTimestamp}${tagParams}`);
        if (!filesRes.ok) return;
        const newFiles = await filesRes.json();
        const oldHash = allFiles.map(f => `${f.name}-${f.size}-${f.path}`).join('|');
        const newHash = newFiles.map(f => `${f.name}-${f.size}-${f.path}`).join('|');
        if (oldHash !== newHash) {
          allFiles = newFiles;
          filteredFiles = showFavoritesOnly ? allFiles.filter(f => favoriteFiles.has(f.path)) : [...allFiles];
          applySorting();
          renderFiles();
          startThumbnailGeneration();
          updateSidebarCounts(filteredFiles);
          updateFooterCounts();
        }
        lastKnownTimestamp = Date.now() / 1000;
      }
    } catch (err) {
      console.debug('[AutoScan] Vérification échouée');
    }
  }, 15000);
}

// ============================================
// 🔧 UTILITAIRES
// ============================================
function escapeHtml(str) {
  if (!str) return '';
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}

function escapeJs(str) {
  if (!str) return '';
  return str.replace(/\\/g, '\\\\').replace(/'/g, "\\'").replace(/"/g, '\\"');
}

function formatSize(bytes) {
  if (!bytes) return '—';
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}

function openModal(modalId) { document.getElementById(modalId)?.classList.remove('hidden'); }
function closeModal(modalId) { document.getElementById(modalId)?.classList.add('hidden'); }

// ============================================
// 📊 MÉTADONNÉES & TOOLTIPS
// ============================================
async function loadFileMetadata(filePath, callback) {
  if (analysisCache[filePath]) {
    callback(analysisCache[filePath]);
    return;
  }
  try {
    const res = await fetch(`${API}/api/files/analyze`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ path: filePath })
    });
    const data = await res.json();
    if (data.success) {
      if (Object.keys(analysisCache).length > 100) {
        delete analysisCache[Object.keys(analysisCache)[0]];
      }
      analysisCache[filePath] = data.metadata;
      callback(data.metadata);
    } else {
      await requestMetadataAnalysis(filePath, callback);
    }
  } catch (err) {
    console.error('[Metadata] Erreur:', err);
    callback(null);
  }
}

function renderMetadataTooltip(metadata) {
  if (!metadata) return '';
  const dims = metadata.dimensions;
  const weights = metadata.weights;
  const time = metadata.estimated_time.formatted;
  return `<div class="file-metadata-tooltip"><div class="meta-row"><i class="fa-solid fa-ruler-combined"></i><span>${dims.x} × ${dims.y} × ${dims.z} mm</span></div><div class="meta-row"><i class="fa-solid fa-weight-scale"></i><span>PLA: ${weights.pla}g • PETG: ${weights.petg}g</span></div><div class="meta-row"><i class="fa-solid fa-clock"></i><span>~${time}</span></div></div>`;
}

// ============================================
//  SOURCES DE FICHIERS
// ============================================
async function addSource(type, name, path, config) {
  try {
    const res = await fetch(`${API}/api/sources`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, type, path, config })
    });
    const data = await res.json();
    if (!res.ok) {
      showToast(data.error || I18N.t('toast.error'), 'error');
      throw new Error(data.error || I18N.t('toast.error'));
    }
    return true;
  } catch (err) {
    console.error('[addSource]', err);
    return false;
  }
}

async function loadSources() {
  try {
    const res = await fetch(`${API}/api/sources`);
    if (!res.ok) throw new Error(I18N.t('toast.connection_error'));
    renderSources(await res.json());
  } catch (err) {
    console.error('[loadSources]', err);
    document.getElementById('sources-list').innerHTML = `<div class="empty-state small"><p>${I18N.t('toast.connection_error')}</p></div>`;
  }
}

function renderSources(sources) {
  const container = document.getElementById('sources-list');
  if (!sources?.length) {
    container.innerHTML = `<div class="empty-state small"><p>${I18N.t('settings.no_sources')}</p></div>`;
    return;
  }
  const icons = { folder: 'fa-folder', file: 'fa-file', smb: 'fa-network-wired', nfs: 'fa-server' };
  container.innerHTML = sources.map(s => `<div class="source-item" data-id="${s.id}"><div class="source-info"><div class="source-icon"><i class="fa-solid ${icons[s.type] || 'fa-database'}"></i></div><div class="source-details"><div style="display: flex; align-items: center; gap: 8px;"><h4>${escapeHtml(s.name)}</h4><button class="btn btn-ghost btn-sm" onclick="editSourceName(${s.id}, '${escapeJs(s.name)}')" title="${I18N.t('modal.rename_source')}"><i class="fa-solid fa-pen"></i></button></div><p>${escapeHtml(s.path)}</p></div></div><button class="btn btn-ghost btn-sm" onclick="deleteSource(${s.id})" title="${I18N.t('actions.delete')}"><i class="fa-solid fa-trash"></i></button></div>`).join('');
  I18N.apply();
}

window.editSourceName = (id, currentName) => {
  document.getElementById('rename-source-id').value = id;
  document.getElementById('rename-source-name').value = currentName;
  openModal('modal-rename-source');
  setTimeout(() => {
    const input = document.getElementById('rename-source-name');
    input.focus();
    input.select();
  }, 100);
};

let confirmCallback = null;
function showConfirmModal(message, onConfirm) {
  document.getElementById('confirm-message').textContent = message;
  openModal('modal-confirm');
  confirmCallback = onConfirm;
  document.getElementById('confirm-ok-btn').onclick = () => {
    closeModal('modal-confirm');
    if (confirmCallback) { confirmCallback(); confirmCallback = null; }
  };
  document.getElementById('confirm-cancel-btn').onclick = () => {
    closeModal('modal-confirm');
    confirmCallback = null;
  };
}

async function deleteSource(id) {
  showConfirmModal(I18N.t('toast.delete_source'), async () => {
    try {
      const res = await fetch(`${API}/api/sources/${id}`, { method: 'DELETE' });
      if (res.ok) {
        showToast(I18N.t('toast.source_deleted'), 'success');
        loadSources();
        loadFiles();
      } else {
        const data = await res.json();
        showToast(data.error || I18N.t('toast.error'), 'error');
      }
    } catch (err) {
      showToast(I18N.t('toast.network_error'), 'error');
      console.error(err);
    }
  });
}

// ============================================
// 📋 CHARGEMENT & AFFICHAGE FICHIERS (SCAN PROGRESSIF)
// ============================================
let scanPollingInterval = null;
let scanBadgeElement = null;

async function loadFiles() {
  const authScreen = document.getElementById('auth-screen');
  const appScreen = document.getElementById('app-screen');
  if (authScreen && !authScreen.classList.contains('hidden')) return;
  if (appScreen && appScreen.classList.contains('hidden')) return;
  
  try {
    const tagParams = activeTagFilters.size > 0 ? `?tags=${encodeURIComponent([...activeTagFilters].join(','))}` : '';
    const res = await fetch(`${API}/api/files${tagParams}`);
    
    if (res.status === 401) return;
    if (!res.ok) {
      const errorText = await res.text();
      throw new Error(`${I18N.t('toast.server_error')}: ${res.status} - ${errorText.substring(0, 100)}`);
    }
    
    const data = await res.json();
    if (!Array.isArray(data)) throw new Error(I18N.t('toast.parse_error'));
    
    // ✅ 1. Afficher le cache INSTANTANÉMENT
    allFiles = data;
    filteredFiles = showFavoritesOnly ? allFiles.filter(f => favoriteFiles.has(f.path)) : [...allFiles];
    applySorting();
    renderFiles();
    setTimeout(() => generateVisibleThumbnails(), 200);
    updateSidebarCounts(filteredFiles);
    updateFooterCounts();
    
    console.log(`✅ ${allFiles.length} fichiers chargés depuis le cache`);
    
    // ✅ 2. Lancer le polling UNIQUEMENT s'il n'est pas déjà en cours
    if (!scanPollingInterval) {
      pollScanProgress();
    }
    
  } catch (err) {
    if (err.message?.includes('401')) return;
    console.error('❌ [loadFiles]', err);
    showToast(`${I18N.t('toast.error')}: ${err.message}`, 'error');
    document.getElementById('files-grid').innerHTML = `<div class="empty-state"><i class="fa-solid fa-triangle-exclamation"></i><p>${I18N.t('toast.connection_error')}</p><button onclick="loadFiles()" class="btn btn-primary" style="margin-top:10px;"><i class="fa-solid fa-rotate-right"></i> ${I18N.t('toast.refreshing')}</button></div>`;
  }
}

// ============================================
// 📡 POLLING SCAN PROGRESSIF (PAQUETS DE 50)
// ============================================
async function pollScanProgress() {
    if (scanPollingInterval) {
        clearInterval(scanPollingInterval);
        scanPollingInterval = null;
    }
    
    let lastFound = 0;
    let lastStatus = '';
    let noChangeCount = 0; // Compteur pour détecter si rien ne change

    showScanBadge("Vérification des nouveaux fichiers...");

    scanPollingInterval = setInterval(async () => {
        try {
            const res = await fetch(`${API}/api/scan/delta`);
            if (!res.ok) {
                clearInterval(scanPollingInterval);
                scanPollingInterval = null;
                hideScanBadge();
                return;
            }
            const data = await res.json();
            
            // Si le scan est terminé ou qu'il n'y a pas de changement après 5 essais, on arrête
            if (data.status === 'done' || data.status === 'idle') {
                noChangeCount++;
                if (noChangeCount >= 5 || data.found === 0) {
                    clearInterval(scanPollingInterval);
                    scanPollingInterval = null;
                    hideScanBadge();
                    return;
                }
            } else {
                noChangeCount = 0; // Reset si activité détectée
            }
            
            if (data.status === 'scanning' && (data.found !== lastFound || data.status !== lastStatus)) {
                lastFound = data.found;
                lastStatus = data.status;
                updateScanBadge(`Scan en cours... ${data.found} nouveau(x) fichier(s) trouvé(s)`);
                
                if (data.new_files && data.new_files.length > 0) {
                    allFiles = allFiles.concat(data.new_files);
                    filteredFiles = showFavoritesOnly
                        ? allFiles.filter(f => favoriteFiles.has(f.path))
                        : [...allFiles];
                    applySorting();
                    renderFiles();
                    generateVisibleThumbnails();
                    updateSidebarCounts(filteredFiles);
                    updateFooterCounts();
                }
            } else if (data.status === 'done') {
                clearInterval(scanPollingInterval);
                scanPollingInterval = null;
                
                if (data.found > 0) {
                    updateScanBadge(`✅ Scan terminé : ${data.found} nouveau(x) fichier(s)`, 'success');
                    setTimeout(() => hideScanBadge(), 4000);
                } else {
                    hideScanBadge();
                }
            }
        } catch (e) {
            console.debug('[Scan] Erreur polling:', e);
        }
    }, 1000);

    // Timeout de sécurité : 30 secondes max
    setTimeout(() => {
        if (scanPollingInterval) {
            clearInterval(scanPollingInterval);
            scanPollingInterval = null;
            hideScanBadge();
        }
    }, 30000); // Réduit à 30 secondes au lieu de 5 minutes
}

// ============================================
// 🏷️ MISE À JOUR DU BADGE (SANS RECRÉATION)
// ============================================
function updateScanBadge(text, type = 'info') {
    if (!scanBadgeElement) {
        showScanBadge(text, type);
        return;
    }
    
    // ✅ Mettre à jour uniquement le texte
    const span = scanBadgeElement.querySelector('span');
    if (span && span.textContent !== text) {
        span.textContent = text;
    }
    
    // Mettre à jour la couleur si nécessaire
    if (type === 'success' && scanBadgeElement.style.borderColor !== 'var(--success)') {
        scanBadgeElement.style.borderColor = 'var(--success)';
        const icon = scanBadgeElement.querySelector('i');
        if (icon) {
            icon.className = 'fa-solid fa-check-circle';
            icon.style.color = 'var(--success)';
        }
    }
}

// ============================================
// 🏷️ BADGE DE SCAN (UI)
// ============================================
function showScanBadge(text, type = 'info') {
    if (!scanBadgeElement) {
        scanBadgeElement = document.createElement('div');
        scanBadgeElement.id = 'scan-progress-badge';
        scanBadgeElement.style.cssText = `
            position: fixed; bottom: 20px; right: 20px;
            background: var(--bg-secondary);
            color: var(--text-primary);
            padding: 12px 18px; border-radius: 12px;
            font-size: 13px; font-weight: 500;
            box-shadow: 0 4px 20px rgba(0,0,0,0.4);
            display: flex; align-items: center; gap: 10px;
            z-index: 9999;
            border: 1px solid var(--accent);
            animation: slideUp 0.3s ease;
            max-width: 350px;
            transition: opacity 0.3s ease, transform 0.3s ease;
        `;
        document.body.appendChild(scanBadgeElement);
    }
    
    // ✅ Utiliser requestAnimationFrame pour éviter le flickering
    requestAnimationFrame(() => {
        const icon = type === 'success'
            ? '<i class="fa-solid fa-check-circle" style="color:var(--success);"></i>'
            : '<i class="fa-solid fa-radar fa-spin" style="color:var(--accent);"></i>';
        
        scanBadgeElement.innerHTML = `${icon} <span>${text}</span>`;
        scanBadgeElement.style.display = 'flex';
        scanBadgeElement.style.opacity = '1';
        scanBadgeElement.style.transform = 'translateY(0)';
        
        if (type === 'success') {
            scanBadgeElement.style.borderColor = 'var(--success)';
        } else {
            scanBadgeElement.style.borderColor = 'var(--accent)';
        }
    });
}

function hideScanBadge() {
  if (scanBadgeElement) {
    scanBadgeElement.style.opacity = '0';
    scanBadgeElement.style.transform = 'translateY(20px)';
    scanBadgeElement.style.transition = 'all 0.3s ease';
    setTimeout(() => {
      if (scanBadgeElement) {
        scanBadgeElement.remove();
        scanBadgeElement = null;
      }
    }, 300);
  }
}

function updateFooterCounts() {
  const countEl = document.getElementById('file-count-display');
  const updateEl = document.getElementById('last-update');
  if (countEl) {
    const count = filteredFiles.length;
    countEl.textContent = ` ${I18N.tp('common.file_count', count, { count })}`;
  }
  if (updateEl) {
    updateEl.textContent = `${I18N.t('footer.updated')} ${new Date().toLocaleTimeString(I18N.lang, { hour: '2-digit', minute: '2-digit' })}`;
  }
}

function applySorting() {
  if (currentSort.startsWith('tag')) {
    filteredFiles.sort((a, b) => {
      const tagA = (a.tags?.length > 0) ? a.tags[0].name.toLowerCase() : 'zzz';
      const tagB = (b.tags?.length > 0) ? b.tags[0].name.toLowerCase() : 'zzz';
      return currentSort === 'tag-asc' ? tagA.localeCompare(tagB) : tagB.localeCompare(tagA);
    });
  } else if (currentSort.startsWith('folder')) {
    filteredFiles.sort((a, b) => {
      const getFolder = p => (p.split('/').filter(Boolean).slice(0, -1).join('/') || '/');
      const folderA = getFolder(a.path);
      const folderB = getFolder(b.path);
      if (folderA !== folderB) return currentSort === 'folder-asc' ? folderA.localeCompare(folderB) : folderB.localeCompare(folderA);
      return currentSort === 'folder-asc' ? a.name.localeCompare(b.name) : b.name.localeCompare(a.name);
    });
  } else {
    filteredFiles.sort((a, b) => {
      switch (currentSort) {
        case 'name-asc': return a.name.localeCompare(b.name);
        case 'name-desc': return b.name.localeCompare(a.name);
        case 'size-asc': return (a.size || 0) - (b.size || 0);
        case 'size-desc': return (b.size || 0) - (a.size || 0);
        default: return 0;
      }
    });
  }
}

// ============================================
// 📊 PROGRESSION GÉNÉRATION MINIATURES
// ============================================
let thumbProgressInterval = null;
let thumbProgressCompleted = false;

function startThumbProgressMonitor() {
    if (thumbProgressInterval) clearInterval(thumbProgressInterval);
    
    const container = document.getElementById('thumb-progress-container');
    const progressBar = document.getElementById('thumb-progress-bar');
    const progressText = document.getElementById('thumb-progress-text');
    
    if (!container || !progressBar || !progressText) return;
    
    let lastProgress = -1;
    let lastPending = -1;
    
    // Polling toutes les 2 secondes
    thumbProgressInterval = setInterval(async () => {
        try {
            const res = await fetch(`${API}/api/thumb/progress`);
            if (!res.ok) return;
            
            const data = await res.json();
            
            // ✅ Ne mettre à jour que si les données ont changé
            if (data.progress === lastProgress && data.pending === lastPending) {
                // Si terminé et stable, arrêter le polling
                if (data.files_without_thumb === 0 && data.pending === 0) {
                    if (!container.classList.contains('completed')) {
                        container.classList.add('completed');
                        progressText.textContent = `${data.files_with_thumb}/${data.total} ✅`;
                        setTimeout(() => {
                            container.classList.add('hidden');
                        }, 5000);
                    }
                    clearInterval(thumbProgressInterval);
                    thumbProgressInterval = null;
                }
                return;
            }
            
            lastProgress = data.progress;
            lastPending = data.pending;
            
            // Afficher/masquer selon l'état
            if (data.is_generating || data.files_without_thumb > 0) {
                container.classList.remove('hidden');
                container.classList.remove('completed');
                
                // ✅ Utiliser requestAnimationFrame pour éviter le flickering
                requestAnimationFrame(() => {
                    progressBar.style.width = `${data.progress}%`;
                    progressText.textContent = `${data.files_with_thumb}/${data.total} (${data.pending} en attente)`;
                });
                
                // Si terminé
                if (data.files_without_thumb === 0 && data.pending === 0) {
                    container.classList.add('completed');
                    progressText.textContent = `${data.files_with_thumb}/${data.total} ✅`;
                    clearInterval(thumbProgressInterval);
                    thumbProgressInterval = null;
                    
                    // Masquer après 5 secondes
                    setTimeout(() => {
                        container.classList.add('hidden');
                    }, 5000);
                }
            } else {
                // Pas de génération en cours
                container.classList.add('hidden');
                clearInterval(thumbProgressInterval);
                thumbProgressInterval = null;
            }
        } catch (err) {
            console.debug('[ThumbProgress] Erreur:', err);
        }
    }, 2000);
}

// Arrêter le monitoring quand on quitte la page
function stopThumbProgressMonitor() {
    if (thumbProgressInterval) {
        clearInterval(thumbProgressInterval);
        thumbProgressInterval = null;
    }
}

// ============================================
// 🎴 RENDU CARTE FICHIER (SANS onmouseenter INLINE)
// ============================================
function renderFileCard(f, icons) {
  const ext = f.extension || '';
  const icon = icons[ext] || 'fa-file';
  const thumbUrl = `${API}/api/thumb?path=${encodeURIComponent(f.path)}&t=${Date.now()}`;
  const isFav = favoriteFiles.has(f.path);
  const isArchive = ['.zip', '.rar', '.7z', '.tar.gz', '.tgz'].includes(ext.toLowerCase());
  const isSelected = selectedFiles.has(f.path);
  
  const tooltipHtml = `<div class="file-metadata-tooltip" id="tooltip-${f.path.replace(/[^\w]/g, '-')}"><div class="meta-row"><i class="fa-solid fa-ruler-combined"></i><span id="dims-${f.path.replace(/[^\w]/g, '-')}">${I18N.t('library.loading')}</span></div><div class="meta-row"><i class="fa-solid fa-weight-scale"></i><span id="weight-${f.path.replace(/[^\w]/g, '-')}">PLA: -g • PETG: -g</span></div><div class="meta-row"><i class="fa-solid fa-clock"></i><span id="time-${f.path.replace(/[^\w]/g, '-')}">~--</span></div></div>`;
  
  const thumbContent = `<img src="${f.has_thumb ? thumbUrl : ''}" 
      data-loaded="${f.has_thumb ? 'pending' : 'false'}"
      onload="this.dataset.loaded='true'; this.style.display='block'; this.nextElementSibling?.style.setProperty('display','none','important');" 
      onerror="window.handleThumbnailError(this)" 
      style="width:100%; height:100%; object-fit:cover; display:${f.has_thumb ? 'block' : 'none'};">
  <div class="file-loading" style="display:${f.has_thumb ? 'none' : 'flex'}; align-items:center; justify-content:center;">
      <i class="fa-solid ${icon} thumb-icon" style="font-size:48px; color:var(--text-muted);"></i>
  </div>`;
  const checkboxHtml = isSelectionMode ? `<div class="file-checkbox" onclick="event.stopPropagation(); toggleFileSelection('${escapeJs(f.path)}', event)" title="${isSelected ? I18N.t('actions.cancel') : I18N.t('actions.select')}"><i class="fa-solid ${isSelected ? 'fa-check-square' : 'fa-square'}"></i></div>` : '';
  
  // 🚀 Suppression de onmouseenter inline - géré par setupHoverDelegation()
  const viewerClick = `onclick="open3DViewer('${escapeJs(f.name)}', '${escapeJs(f.path)}')" style="cursor:pointer;"`;
  const selectedClass = isSelected ? ' selected' : '';
  
  if (currentView === 'details') {
    return `<div class="file-card${selectedClass}" data-name="${escapeHtml(f.name)}" data-path="${escapeJs(f.path)}" ${viewerClick}><div class="file-thumb">${checkboxHtml}${thumbContent}</div><div class="file-info"><div class="file-name" title="${escapeHtml(f.name)}">${escapeHtml(f.name)}</div><div class="file-meta">${f.subdir ? `<span><i class="fa-solid fa-folder-open"></i> ${escapeHtml(f.subdir)}</span>` : ''}<span><i class="fa-solid fa-folder"></i> ${escapeHtml(f.path.split('/').slice(0, -1).join('/')) || I18N.t('source.local_folder')}</span><span><i class="fa-solid fa-weight-hanging"></i> ${formatSize(f.size || 0)}</span></div>${f.tags?.length ? `<div class="file-tags">${f.tags.map(t => `<span class="file-tag" style="background:${t.color}20;color:${t.color};border-color:${t.color}">${escapeHtml(t.name)}</span>`).join('')}</div>` : ''}<div class="file-actions"><button type="button" class="btn btn-primary btn-sm" onclick="event.stopPropagation(); sendToSlicer('${escapeJs(f.path)}', '${escapeJs(f.name)}')"><i class="fa-solid fa-scissors"></i> ${I18N.t('settings.slicer_config')}</button>${isArchive ? `<button type="button" class="btn btn-ghost btn-sm" onclick="event.stopPropagation(); decompressFile('${escapeJs(f.path)}', event)" title="${I18N.t('toast.extract_success')}"><i class="fa-solid fa-file-zipper"></i></button>` : ''}<button type="button" class="btn-favorite-details ${isFav ? 'favorited' : ''}" onclick="toggleFavorite('${escapeJs(f.path)}', event)" title="${isFav ? I18N.t('toast.favorites_removed') : I18N.t('toast.favorites_added')}"><i class="${isFav ? 'fa-solid' : 'fa-regular'} fa-star"></i></button></div></div>${tooltipHtml}</div>`;
  }
  
  return `<div class="file-card${selectedClass}" data-name="${escapeHtml(f.name)}" data-path="${escapeJs(f.path)}" ${viewerClick}><div class="file-thumb" style="position:relative;">${checkboxHtml}${thumbContent}${tooltipHtml}<span class="file-ext-badge">${ext.replace('.', '')}</span>${isArchive ? `<span class="file-archive-badge">️ ${I18N.t('toast.extract_success')}</span>` : ''}<button type="button" class="file-slicer-btn" onclick="event.stopPropagation(); sendToSlicer('${escapeJs(f.path)}', '${escapeJs(f.name)}')"><i class="fa-solid fa-scissors"></i> ${I18N.t('settings.slicer_config')}</button>${isArchive ? `<button type="button" class="file-decompress-btn" onclick="event.stopPropagation(); decompressFile('${escapeJs(f.path)}', event)" title="${I18N.t('toast.extract_success')}"><i class="fa-solid fa-file-zipper"></i> ${I18N.t('actions.add')}</button>` : ''}<button type="button" class="file-favorite-btn ${isFav ? 'favorited' : ''}" onclick="toggleFavorite('${escapeJs(f.path)}', event); return false;" title="${isFav ? I18N.t('toast.favorites_removed') : I18N.t('toast.favorites_added')}"><i class="${isFav ? 'fa-solid' : 'fa-regular'} fa-star"></i></button><button type="button" class="file-tag-btn" onclick="event.stopPropagation(); openTagModal('${escapeJs(f.path)}')" title="${I18N.t('modal.manage_tags')}"><i class="fa-solid fa-tag"></i></button></div><div class="file-info"><div class="file-name" title="${escapeHtml(f.name)}">${escapeHtml(f.name)}</div>${f.tags?.length ? `<div class="file-tags">${f.tags.map(t => `<span class="file-tag" style="background:${t.color}20;color:${t.color};border-color:${t.color}">${escapeHtml(t.name)}</span>`).join('')}</div>` : ''}</div></div>`;
}

// ============================================
// ✅ SÉLECTION MULTIPLE
// ============================================
window.toggleSelectionMode = function () {
  isSelectionMode = !isSelectionMode;
  selectedFiles.clear();
  const btn = document.getElementById('select-all-btn');
  if (btn) {
    btn.classList.toggle('active', isSelectionMode);
    btn.innerHTML = isSelectionMode ? `<i class="fa-solid fa-times"></i> ${I18N.t('actions.cancel')}` : `<i class="fa-solid fa-square-check"></i> ${I18N.t('actions.select')}`;
  }
  const actionBar = document.getElementById('selection-action-bar');
  if (actionBar) actionBar.style.display = isSelectionMode ? 'flex' : 'none';
  renderFiles();
  updateSelectionCount();
};

window.toggleFileSelection = function (filePath, event) {
  if (event) {
    event.preventDefault();
    event.stopPropagation();
  }
  if (selectedFiles.has(filePath)) selectedFiles.delete(filePath);
  else selectedFiles.add(filePath);
  renderFiles();
  updateSelectionCount();
};

window.selectAllFiles = function () {
  if (selectedFiles.size === filteredFiles.length) selectedFiles.clear();
  else filteredFiles.forEach(f => selectedFiles.add(f.path));
  renderFiles();
  updateSelectionCount();
};

function updateSelectionCount() {
  const countEl = document.getElementById('selection-count');
  if (countEl) {
    countEl.textContent = `${I18N.tp('common.file_count', selectedFiles.size, { count: selectedFiles.size })} ${I18N.t('actions.select').toLowerCase()}`;
  }
}

window.sendSelectedToSlicer = async function () {
  if (selectedFiles.size === 0) {
    showToast(I18N.t('toast.no_selection'), 'warning');
    return;
  }
  try {
    const res = await fetch(`${API}/api/slicer/send-batch`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ files: [...selectedFiles] })
    });
    const data = await res.json();
    if (res.ok) {
      showToast(data.message || `${selectedFiles.size} ${I18N.t('toast.files_sent')}`, 'success');
      selectedFiles.clear();
      toggleSelectionMode();
    } else {
      showToast(data.error || I18N.t('toast.send_error'), 'error');
    }
  } catch (err) {
    showToast(I18N.t('toast.connection_error'), 'error');
    console.error('[Batch Slicer]', err);
  }
};

// ============================================
// 🎨 RENDU GRILLE FICHIERS (AVEC CHUNKING)
// ============================================
function renderFiles(chunkSize = 50) {
  const grid = document.getElementById('files-grid');
  if (!filteredFiles?.length) {
    grid.innerHTML = `<div class="empty-state"><i class="fa-solid fa-inbox"></i><p>${I18N.t('library.no_files')}</p></div>`;
    I18N.apply();
    return;
  }
  
  const icons = { '.stl': 'fa-cube', '.3mf': 'fa-file-lines', '.obj': 'fa-shapes' };
  const isFolderSort = currentSort.startsWith('folder');
  const isTagSort = currentSort.startsWith('tag');
  let htmlContent = '';
  let lastGroup = '';
  const getFolderName = path => (path.split('/').filter(Boolean).slice(0, -1).join('/') || '/');
  
  // 🚀 Préparation du contenu par chunks
  const filesToRender = [];
  
  if (isFolderSort) {
    const filesByFolder = {};
    filteredFiles.forEach(f => {
      const folder = getFolderName(f.path);
      if (!filesByFolder[folder]) filesByFolder[folder] = [];
      filesByFolder[folder].push(f);
    });
    Object.keys(filesByFolder).sort((a, b) => currentSort === 'folder-asc' ? a.localeCompare(b) : b.localeCompare(a)).forEach(folder => {
      const files = filesByFolder[folder].sort((a, b) => currentSort === 'folder-asc' ? a.name.localeCompare(b.name) : b.name.localeCompare(a.name));
      filesToRender.push({ type: 'folder-header', folder, files });
      files.forEach(f => filesToRender.push({ type: 'file', f }));
    });
  } else if (isTagSort) {
    filteredFiles.forEach(f => {
      const currentTag = f.tags?.length > 0 ? f.tags[0].name : I18N.t('filters.tags');
      if (currentTag !== lastGroup) {
        lastGroup = currentTag;
        const tagFilesCount = filteredFiles.filter(item => (item.tags?.[0]?.name || I18N.t('filters.tags')) === currentTag).length;
        filesToRender.push({ type: 'tag-header', tag: currentTag, count: tagFilesCount });
      }
      filesToRender.push({ type: 'file', f });
    });
  } else {
    filteredFiles.forEach(f => filesToRender.push({ type: 'file', f }));
  }
  
  // 🚀 Rendu chunké avec requestIdleCallback
  let idx = 0;
  grid.innerHTML = '';
  
  function renderChunk() {
    const end = Math.min(idx + chunkSize, filesToRender.length);
    let chunkHtml = '';
    
    for (let i = idx; i < end; i++) {
      const item = filesToRender[i];
      if (item.type === 'folder-header') {
        chunkHtml += `<div class="folder-section"><div class="folder-group-header"><i class="fa-solid fa-folder-open"></i>${escapeHtml(item.folder)}<span class="folder-file-count">${I18N.tp('common.file_count', item.files.length, { count: item.files.length })}</span><button class="btn btn-ghost btn-sm folder-select-btn" onclick="event.stopPropagation(); selectFolderFiles('${escapeJs(item.folder)}', this)" title="${I18N.t('actions.select')}"><i class="fa-regular fa-square"></i> ${I18N.t('actions.select')}</button></div><div class="folder-content">`;
      } else if (item.type === 'folder-close') {
        chunkHtml += `</div></div>`;
      } else if (item.type === 'tag-header') {
        chunkHtml += `<div class="tag-group-header"><i class="fa-solid fa-tag"></i>${escapeHtml(item.tag)}<span class="folder-file-count">${I18N.tp('common.file_count', item.count, { count: item.count })}</span></div>`;
      } else if (item.type === 'file') {
        chunkHtml += renderFileCard(item.f, icons);
      }
    }
    
    grid.insertAdjacentHTML('beforeend', chunkHtml);
    idx = end;
    
    if (idx < filesToRender.length) {
      if ('requestIdleCallback' in window) {
        requestIdleCallback(renderChunk, { timeout: 100 });
      } else {
        setTimeout(renderChunk, 0);
      }
    } else {
      // Rendu terminé
      I18N.apply();
      setTimeout(() => {
        grid.querySelectorAll('.file-thumb img').forEach(img => {
          if (img.complete && img.naturalWidth === 0) window.handleThumbnailError(img);
        });
      }, 100);
    }
  }
  
  renderChunk();
}

// ============================================
// 🔄 GÉNÉRATION MINIATURES EN BACKGROUND (OPTIMISÉ)
// ============================================
function startThumbnailGeneration(limit = 20) {
  const files = filteredFiles;
  if (!files?.length) return;
  
  let idx = 0, processed = 0;
  
  async function processNext() {
    if (idx >= files.length || processed >= limit) return;
    const f = files[idx++];
    if (f.has_thumb) { processed++; requestAnimationFrame(processNext); return; }
    
    try {
      const res = await fetch(`${API}/api/thumb/check`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ path: f.path })
      });
      const data = await res.json();
      if (data.exists && data.type === 'cached') {
        updateFileThumbnail(f.name, `${API}${data.url}&t=${Date.now()}`);
      }
    } catch {}
    processed++;
    requestAnimationFrame(processNext);
  }
  processNext();
}

function updateFileThumbnail(fileName, thumbUrl) {
    const card = document.querySelector(`.file-card[data-name="${CSS.escape(fileName)}"]`);
    if (!card) return;
    const img = card.querySelector('.file-thumb img');
    const loader = card.querySelector('.file-loading');
    
    // ✅ Skip si déjà chargée avec succès
    if (img && img.dataset.loaded === 'true' && img.src && !img.src.includes('data:image')) return;
    
    if (img && img.src !== thumbUrl) {
        const testImg = new Image();
        testImg.onload = () => {
            img.src = thumbUrl;
            img.style.display = 'block';
            img.dataset.loaded = 'true'; // ✅ Marquer comme chargée
            if (loader) loader.style.display = 'none';
        };
        testImg.onerror = () => {
            // Ne pas appeler handleThumbnailError si déjà chargée
            if (img.dataset.loaded !== 'true') {
                window.handleThumbnailError(img);
            }
        };
        testImg.src = thumbUrl;
    }
}

function startThumbAutoRefresh() {
    if (thumbRefreshInterval) clearInterval(thumbRefreshInterval);
    thumbRefreshInterval = setInterval(async () => {
        const cards = document.querySelectorAll('.file-card');
        for (let i = 0; i < Math.min(5, cards.length); i++) {
            const card = cards[i];
            const file = filteredFiles.find(f => f.name === card.dataset.name);
            if (!file) continue;
            
            // ✅ Skip si déjà chargée avec succès
            const img = card.querySelector('.file-thumb img');
            if (img && img.dataset.loaded === 'true') continue;
            
            try {
                const checkRes = await fetch(`${API}/api/thumb/check`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ path: file.path })
                });
                const checkData = await checkRes.json();
                if (checkData.exists && checkData.type === 'cached') {
                    updateFileThumbnail(card.dataset.name, `${API}${checkData.url}`);
                }
            } catch (err) { /* Silent */ }
        }
    }, 30000);
}

// ============================================
// 🏷️ GESTION DES TAGS
// ============================================
async function loadTags() {
  try {
    const res = await fetch(`${API}/api/tags`);
    if (res.ok) {
      allTags = await res.json();
      renderTagFilters();
    }
  } catch (err) {
    console.error('[Tags] Erreur:', err);
  }
}

function renderTagFilters() {
  const container = document.getElementById('filter-tags');
  if (!container) return;
  if (!allTags.length) {
    container.innerHTML = `<p style="color:var(--text-muted);font-size:13px">${I18N.t('toast.tag_empty')}</p>`;
    return;
  }
  container.innerHTML = allTags.map(t => `<label class="checkbox-label"><input type="checkbox" value="${escapeHtml(t.name)}" class="filter-tag" ${activeTagFilters.has(t.name) ? 'checked' : ''}><span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:${t.color};margin-right:6px;"></span>${escapeHtml(t.name)} <span class="tag-count" style="color:var(--text-muted)">(${t.count})</span></label>`).join('');
  updateSidebarCounts(filteredFiles || allFiles);
  I18N.apply();
}

function updateSidebarCounts(currentFiles) {
  const counts = {};
  allTags.forEach(tag => {
    counts[tag.name.toLowerCase()] = currentFiles.filter(f => f.tags?.some(t => t.name.toLowerCase() === tag.name.toLowerCase())).length;
  });
  document.querySelectorAll('.filter-tag').forEach(checkbox => {
    const tagName = checkbox.value.toLowerCase();
    const countSpan = checkbox.closest('.checkbox-label')?.querySelector('.tag-count');
    if (countSpan) {
      countSpan.textContent = `(${counts[tagName] || 0})`;
      checkbox.closest('.checkbox-label').style.opacity = (counts[tagName] === 0 && !checkbox.checked) ? '0.4' : '1';
    }
  });
}

function openTagModal(filePath) {
  openTagManagerModal('file', filePath);
}

function openTagManagerModal(mode = 'global', filePath = null) {
  const filePathEl = document.getElementById('tag-modal-file-path');
  const currentTagsEl = document.getElementById('tag-modal-current-tags');
  const tagsListEl = document.getElementById('tag-modal-list');
  const newTagGroup = document.getElementById('tag-modal-new-tag')?.closest('.input-group');
  const applyBtn = document.getElementById('add-tag-to-file-btn');
  const modalTitle = document.querySelector('#modal-tag-manager .modal-header h3');
  
  if (mode === 'global') {
    currentTagFile = null;
    if (modalTitle) modalTitle.innerHTML = `<i class="fa-solid fa-tags"></i> ${I18N.t('modal.manage_tags')}`;
    if (filePathEl?.closest('.input-group')) filePathEl.closest('.input-group').style.display = 'none';
    if (currentTagsEl?.parentElement) currentTagsEl.parentElement.style.display = 'none';
    if (tagsListEl) {
      if (allTags.length === 0) {
        tagsListEl.innerHTML = `<p style="color:var(--text-muted);font-size:12px;padding:10px">${I18N.t('toast.tag_empty')}</p>`;
      } else {
        tagsListEl.innerHTML = allTags.map(t => `<div style="display:flex;justify-content:space-between;align-items:center;padding:10px;border-bottom:1px solid var(--border);"><div style="display:flex;align-items:center;gap:10px;"><span style="display:inline-block;width:12px;height:12px;border-radius:50%;background:${t.color};"></span><strong>${escapeHtml(t.name)}</strong><span style="color:var(--text-muted);font-size:12px">(${t.count} ${I18N.t('library.no_files').toLowerCase()})</span></div><div style="display:flex;gap:6px;"><button class="btn btn-ghost btn-sm" onclick="editTag(${t.id}, '${escapeJs(t.name)}', '${t.color}')" title="${I18N.t('actions.rename')}" style="color:var(--accent)"><i class="fa-solid fa-pen"></i></button><button class="btn btn-ghost btn-sm" onclick="deleteTag(${t.id}, '${escapeJs(t.name)}')" title="${I18N.t('actions.delete')}" style="color:var(--danger)"><i class="fa-solid fa-trash"></i></button></div></div>`).join('');
      }
    }
    if (newTagGroup) newTagGroup.style.display = 'flex';
    if (applyBtn) {
      applyBtn.style.display = 'inline-flex';
      applyBtn.innerHTML = I18N.t('modal.create_tag');
      applyBtn.onclick = createGlobalTag;
    }
  } else {
    currentTagFile = filePath;
    if (modalTitle) modalTitle.innerHTML = `<i class="fa-solid fa-tag"></i> ${I18N.t('modal.selected_file')}`;
    if (filePathEl && filePath) {
      filePathEl.closest('.input-group').style.display = 'block';
      filePathEl.value = filePath.split('/').pop() || filePath;
    }
    if (currentTagsEl?.parentElement) {
      currentTagsEl.parentElement.style.display = 'block';
      const file = allFiles.find(f => f.path === filePath);
      const currentTags = file?.tags?.map(t => t.name) || [];
      currentTagsEl.innerHTML = currentTags.length ? currentTags.map(t => `<span class="tag-badge">${escapeHtml(t)}</span>`).join('') : `<span style="color:var(--text-muted);font-size:12px">${I18N.t('toast.file_not_selected')}</span>`;
    }
    if (tagsListEl) {
      const file = allFiles.find(f => f.path === filePath);
      const currentTags = file?.tags?.map(t => t.name) || [];
      tagsListEl.innerHTML = allTags.map(t => `<label class="checkbox-label" style="margin:6px 0;"><input type="checkbox" value="${escapeHtml(t.name)}" class="tag-select" ${currentTags.includes(t.name) ? 'checked' : ''}><span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:${t.color};margin-right:8px;"></span>${escapeHtml(t.name)}</label>`).join('');
    }
    if (newTagGroup) newTagGroup.style.display = 'flex';
    if (applyBtn) {
      applyBtn.style.display = 'inline-flex';
      applyBtn.innerHTML = `<i class="fa-solid fa-check"></i> ${I18N.t('filters.apply')}`;
      applyBtn.onclick = applyTagsToFile;
    }
  }
  openModal('modal-tag-manager');
  I18N.apply();
}

async function createGlobalTag() {
  const newTagInput = document.getElementById('tag-modal-new-tag');
  const newTagName = newTagInput?.value.trim();
  if (!newTagName) {
    showToast(I18N.t('toast.tag_empty'), 'warning');
    return;
  }
  if (currentTagFile) {
    await applyTagsToFile();
    return;
  }
  try {
    const res = await fetch(`${API}/api/tags`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: newTagName, color: '#' + Math.floor(Math.random() * 16777215).toString(16).padStart(6, '0') })
    });
    const data = await res.json();
    if (res.ok) {
      showToast(I18N.t('toast.tag_created'), 'success');
      if (newTagInput) newTagInput.value = '';
      await loadTags();
      openTagManagerModal('global');
    } else {
      showToast(data.error || I18N.t('toast.tag_error'), 'error');
    }
  } catch (err) {
    showToast(I18N.t('toast.fetch_error'), 'error');
    console.error('[Tags] Erreur:', err);
  }
}

async function applyTagsToFile() {
  if (!currentTagFile) {
    showToast(I18N.t('toast.file_not_selected'), 'error');
    return;
  }
  const selected = [...document.querySelectorAll('.tag-select:checked')].map(c => c.value);
  const newTagInput = document.getElementById('tag-modal-new-tag');
  const newTag = newTagInput?.value.trim();
  const tagsToSave = [...new Set([...selected, ...(newTag ? [newTag] : [])])];
  try {
    const res = await fetch(`${API}/api/files/tags`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ path: currentTagFile, tags: tagsToSave })
    });
    const data = await res.json();
    if (res.ok) {
      showToast(I18N.t('toast.tags_updated'), 'success');
      closeModal('modal-tag-manager');
      await Promise.all([loadFiles(), loadTags()]);
    } else {
      showToast(data.error || I18N.t('toast.tag_assign_error'), 'error');
    }
  } catch (err) {
    showToast(I18N.t('toast.fetch_error'), 'error');
    console.error('[Tags] Erreur:', err);
  }
}

window.deleteTag = (tagId, tagName) => {
  closeModal('modal-tag-manager');
  showConfirmModal(`${I18N.t('toast.delete_tag')} "${tagName}" ?`, async () => {
    try {
      const res = await fetch(`${API}/api/tags/${tagId}`, { method: 'DELETE' });
      if (res.ok) {
        showToast(I18N.t('toast.tags_deleted'), 'success');
        await loadTags();
        await loadFiles();
        setTimeout(() => openTagManagerModal('global'), 200);
      } else {
        const data = await res.json();
        showToast(data.error || I18N.t('toast.error'), 'error');
      }
    } catch (err) {
      showToast(I18N.t('toast.fetch_error'), 'error');
      console.error('[Tags] Erreur:', err);
    }
  });
};

window.editTag = async (tagId, currentName, currentColor) => {
  const newName = prompt(`${I18N.t('modal.rename_source')} :`, currentName);
  if (!newName || newName.trim() === currentName) return;
  const newColor = prompt(`${I18N.t('settings.brand_color')} (hex, ex: #ff6b6b) :`, currentColor);
  try {
    const res = await fetch(`${API}/api/tags/${tagId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: newName.trim(), color: newColor || currentColor })
    });
    const data = await res.json();
    if (res.ok) {
      showToast(I18N.t('toast.tags_updated_global'), 'success');
      await loadTags();
      openTagManagerModal('global');
    } else {
      showToast(data.error, 'error');
    }
  } catch (err) {
    showToast(I18N.t('toast.fetch_error'), 'error');
    console.error(err);
  }
};

// ============================================
//  COMPTES EXTERNES
// ============================================
async function loadAccounts() {
    try {
        const res = await fetch(`${API}/api/accounts`);
        if (res.status === 401) return;
        const accounts = await res.json();
        renderAccounts(accounts);
        
        // ✅ AJOUTER CETTE LIGNE
        loadMakerWorldCookie();
        
    } catch (err) {
        console.error('Erreur chargement comptes:', err);
    }
}

function renderAccounts(accounts) {
  const container = document.getElementById('accounts-list');
  if (!accounts?.length) {
    container.innerHTML = `<div class="empty-state small"><p>${I18N.t('settings.no_accounts')}</p></div>`;
    return;
  }
  const icons = { 'cults': 'fa-c', 'thingiverse': 'fa-cube', 'telegram': 'fa-telegram', 'makerworld': 'fa-globe' };
  container.innerHTML = accounts.map(a => `<div class="source-item" data-platform="${a.platform}"><div class="source-info"><div class="source-icon"><i class="fa-brands ${icons[a.platform] || 'fa-key'}"></i></div><div class="source-details"><h4> ${a.platform.charAt(0).toUpperCase() + a.platform.slice(1)}</h4></div></div><div style="display: flex; gap: 4px;"><button class="btn btn-ghost btn-sm" onclick="editAccount('${a.platform}')" title="${I18N.t('actions.rename')}"><i class="fa-solid fa-pen"></i></button><button class="btn btn-ghost btn-sm" onclick="deleteAccount('${a.platform}')" title="${I18N.t('actions.delete')}" style="color: var(--danger)"><i class="fa-solid fa-trash"></i></button></div></div>`).join('');
  I18N.apply();
}

async function editAccount(platform) {
  console.log(`[DEBUG] Édition: ${platform}`);
  openAccountModal(platform, true);
}

async function saveAccount(e) {
  e.preventDefault();
  const platform = document.getElementById('account-platform').value;
  const email = document.getElementById('account-email')?.value.trim() || '';
  const password = document.getElementById('account-password')?.value || '';
  const apiKey = document.getElementById('account-api-key')?.value.trim() || '';
  const phone = document.getElementById('account-phone')?.value.trim() || '';
  const telegramApiId = document.getElementById('account-telegram-api-id')?.value.trim() || '';
  const telegramApiHash = document.getElementById('account-telegram-api-hash')?.value.trim() || '';
  
  if (platform === 'cults' && !apiKey) { showToast(I18N.t('toast.api_required') + ' Cults3D', 'warning'); return; }
  if (platform === 'thingiverse' && !apiKey) { showToast(I18N.t('toast.api_required') + ' Thingiverse', 'warning'); return; }
  if (platform === 'telegram') {
    if (!telegramApiId || !telegramApiHash) { showToast(I18N.t('toast.tg_api_required'), 'warning'); return; }
  } else if (platform && !['telegram', 'cults', 'thingiverse'].includes(platform)) {
    if (!email || !password) { showToast(I18N.t('toast.email_pass_required'), 'warning'); return; }
  }
  
  try {
    if (platform === 'thingiverse' && apiKey) {
      const res = await fetch(`${API}/api/accounts`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ platform: 'thingiverse', api_key: apiKey, is_edit: isEditingAccount })
      });
      const data = await res.json();
      if (res.ok) {
        showToast(isEditingAccount ? I18N.t('toast.account_updated') : I18N.t('toast.account_saved'), 'success');
        closeModal('modal-account');
        loadAccounts();
        setTimeout(async () => {
          try {
            const validateRes = await fetch(`${API}/api/accounts/thingiverse/validate`, { method: 'POST' });
            const validateData = await validateRes.json();
            updateThingiverseFooterStatus(validateRes.ok && validateData.connected, validateData.error || I18N.t('toast.api_invalid'));
            showToast(validateRes.ok && validateData.connected ? I18N.t('toast.thingiverse_connected') : `${I18N.t('toast.account_saved')} mais: ${validateData.error}`, validateRes.ok ? 'success' : 'warning');
          } catch (err) {
            console.error('[Validate Thingiverse]', err);
            updateThingiverseFooterStatus(false, I18N.t('toast.validation_error'));
          }
        }, 1000);
        isEditingAccount = false;
        editingAccountPlatform = null;
      } else {
        showToast(data.error || I18N.t('toast.error'), 'error');
      }
      return;
    }
    if (platform === 'cults' && apiKey) {
      const res = await fetch(`${API}/api/accounts`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ platform: 'cults', api_key: apiKey, is_edit: isEditingAccount })
      });
      const data = await res.json();
      if (res.ok) {
        showToast(isEditingAccount ? I18N.t('toast.account_updated') : I18N.t('toast.account_saved'), 'success');
        closeModal('modal-account');
        loadAccounts();
        setTimeout(async () => {
          try {
            const validateRes = await fetch(`${API}/api/accounts/cults/validate`, { method: 'POST' });
            const validateData = await validateRes.json();
            updateCultsFooterStatus(validateRes.ok && validateData.connected, validateData.error || I18N.t('toast.api_invalid'));
            showToast(validateRes.ok && validateData.connected ? I18N.t('toast.cults_connected') : `️ ${I18N.t('toast.account_saved')} mais: ${validateData.error}`, validateRes.ok ? 'success' : 'warning');
          } catch (err) {
            console.error('[Validate Cults]', err);
            updateCultsFooterStatus(false, I18N.t('toast.validation_error'));
          }
        }, 1000);
        isEditingAccount = false;
        editingAccountPlatform = null;
      } else {
        showToast(data.error || I18N.t('toast.error'), 'error');
      }
      return;
    }
    if (platform === 'telegram' && telegramApiId && telegramApiHash && phone) {
      const saveRes = await fetch(`${API}/api/accounts`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ platform, telegram_api_id: telegramApiId, telegram_api_hash: telegramApiHash })
      });
      if (!saveRes.ok) {
        const err = await saveRes.json();
        showToast(err.error, 'error');
        return;
      }
      showToast('📱 ' + I18N.t('toast.telegram_code_sent'), 'info');
      const authRes = await fetch(`${API}/api/telegram/send_code`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ phone, api_id: telegramApiId, api_hash: telegramApiHash })
      });
      if (!authRes.ok) {
        const err = await authRes.json();
        showToast(`${I18N.t('toast.error')}: ${err.error}`, 'error');
        return;
      }
      showToast(I18N.t('toast.telegram_code_sent'), 'success');
      const code = await showTelegramCodeModal();
      if (!code) {
        showToast(I18N.t('toast.telegram_cancelled'), 'info');
        return;
      }
      const verifyRes = await fetch(`${API}/api/telegram/verify_code`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code, password_2fa: '' })
      });
      if (verifyRes.ok) {
        showToast(I18N.t('toast.telegram_connected'), 'success');
        closeModal('modal-account');
        loadAccounts();
        return;
      } else {
        const err = await verifyRes.json();
        showToast(`${I18N.t('toast.error')}: ${err.error}`, 'error');
        return;
      }
    }
    const res = await fetch(`${API}/api/accounts`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ platform, email: email || null, password: password || null, api_key: apiKey || null, phone: phone || null, telegram_api_id: telegramApiId || null, telegram_api_hash: telegramApiHash || null, is_edit: isEditingAccount })
    });
    const data = await res.json();
    if (res.ok) {
      showToast(isEditingAccount ? I18N.t('toast.account_updated') : I18N.t('toast.account_saved'), 'success');
      closeModal('modal-account');
      loadAccounts();
      isEditingAccount = false;
      editingAccountPlatform = null;
    } else {
      showToast(data.error, 'error');
    }
  } catch (err) {
    showToast(I18N.t('toast.fetch_error'), 'error');
    console.error('[Save Account]', err);
  }
}

async function deleteAccount(platform) {
  showConfirmModal(`${I18N.t('toast.delete_account')} ${platform} ?`, async () => {
    try {
      const res = await fetch(`${API}/api/accounts/${platform}`, { method: 'DELETE' });
      if (res.ok) {
        showToast(I18N.t('toast.account_deleted'), 'success');
        loadAccounts();
        if (platform === 'cults') updateCultsFooterStatus(false, I18N.t('settings.no_accounts'));
        else if (platform === 'thingiverse') updateThingiverseFooterStatus(false, I18N.t('settings.no_accounts'));
      } else {
        const data = await res.json();
        showToast(data.error, 'error');
      }
    } catch (err) {
      showToast(I18N.t('toast.fetch_error'), 'error');
    }
  });
}

function updateCultsFooterStatus(connected, error = null) { /* Implement */ }
function updateThingiverseFooterStatus(connected, error = null) { /* Implement */ }
function updateTelegramFooterStatus(connected, error = null) { /* Implement */ }

// ============================================
// ⬇️ TÉLÉCHARGEMENTS
// ============================================
async function loadDownloadSources() {
  const select = document.getElementById('download-source');
  if (!select) return;
  
  select.innerHTML = `<option value="">📁 ${I18N.t('download.select_folder')}</option>`;
  
  try {
    const res = await fetch(`${API}/api/sources`);
    if (!res.ok) throw new Error(I18N.t('toast.load_source_error'));
    const sources = await res.json();
    
    // ✅ Inclure folder ET smb (et nfs si nécessaire)
    const folderSources = sources.filter(s => 
      s.type === 'folder' || s.type === 'smb' || s.type === 'nfs'
    );
    
    if (folderSources.length === 0) { 
      select.innerHTML += `<option value="" disabled>${I18N.t('download.no_local_folders')}</option>`; 
      return; 
    }
    
    folderSources.forEach(source => {
      const option = document.createElement('option');
      option.value = source.id;
      // ✅ Icône différente selon le type de source
      const icon = source.type === 'smb' ? '🌐' : (source.type === 'nfs' ? '🗄️' : '📁');
      option.textContent = `${icon} ${source.name} (${source.path})`;
      option.dataset.sourceType = source.type;
      select.appendChild(option);
    });
    
  } catch (err) { 
    console.error('[Download Sources]', err); 
    select.innerHTML += `<option value="" disabled>${I18N.t('download.load_error')}</option>`; 
  }
}

function openDownloadModal() {
  loadDownloadSources(); // ✅ Doit être appelé en premier
  document.getElementById('download-form').reset();
  document.getElementById('download-progress').classList.add('hidden');
  document.getElementById('download-result').style.display = 'none';
  document.getElementById('download-btn').disabled = false;
  openModal('modal-download');
  setTimeout(() => { document.getElementById('download-url')?.focus(); }, 100);
}

let activeDownloads = [];
let downloadToastElements = {};
let downloadIdCounter = 0;
let isFormLocked = false;

async function handleDownload(e) {
  e.preventDefault();
  if (isFormLocked) { showToast(I18N.t('toast.please_wait'), 'warning'); return; }
  const url = document.getElementById('download-url').value.trim();
  const sourceId = document.getElementById('download-source').value;
  if (!url) { showToast(I18N.t('toast.url_required'), 'warning'); return; }
  isFormLocked = true;
  try {
    const downloadId = ++downloadIdCounter;
    const downloadInfo = { id: downloadId, url, sourceId, status: 'starting', filename: '', progress: 0, current: 0, total: 0, toastElement: null };
    activeDownloads.push(downloadInfo);
    createDownloadToast(downloadInfo);
    startDownload(downloadInfo);
    document.getElementById('download-form').reset();
    setTimeout(() => { isFormLocked = false; }, 500);
  } catch (err) { console.error('[handleDownload] Erreur:', err); isFormLocked = false; showToast(I18N.t('toast.start_error'), 'error'); }
}

async function startDownload(downloadInfo) {
  try {
    const progressPollingInterval = setInterval(async () => {
      try {
        const res = await fetch(`${API}/api/download/progress/${downloadInfo.id}`);
        const data = await res.json();
        if (data.active && data.download_id === downloadInfo.id) {
          downloadInfo.status = 'downloading';
          downloadInfo.filename = data.filename || I18N.t('download.file_placeholder');
          downloadInfo.progress = data.percentage || 0;
          downloadInfo.current = data.current || 0;
          downloadInfo.total = data.total || 0;
          const currentMB = (downloadInfo.current / 1024 / 1024).toFixed(1);
          const totalMB = (downloadInfo.total / 1024 / 1024).toFixed(1);
          updateDownloadToast(downloadInfo, currentMB, totalMB);
        }
      } catch (err) { console.error('[Progress polling error]', err); }
    }, 500);
    const res = await fetch(`${API}/api/download`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ url: downloadInfo.url, target_source_id: downloadInfo.sourceId || null, download_id: downloadInfo.id }) });
    clearInterval(progressPollingInterval);
    const data = await res.json();
    if (res.ok) {
      downloadInfo.status = 'completed'; downloadInfo.progress = 100; downloadInfo.filename = data.filename || I18N.t('download.file_placeholder');
      updateDownloadToast(downloadInfo, (data.size / 1024 / 1024).toFixed(1), (data.size / 1024 / 1024).toFixed(1), true);
      showToast(`✓ ${downloadInfo.filename} ${I18N.t('toast.download_success')}`, 'success');
      setTimeout(() => { removeDownloadToast(downloadInfo.id); }, 3000);
      loadFiles();
    } else {
      downloadInfo.status = 'error';
      updateDownloadToast(downloadInfo, 0, 0, false, data.error || I18N.t('app.error'));
      setTimeout(() => { removeDownloadToast(downloadInfo.id); }, 5000);
    }
  } catch (err) {
    downloadInfo.status = 'error';
    updateDownloadToast(downloadInfo, 0, 0, false, I18N.t('toast.connection_error'));
    console.error('[Download]', err);
    setTimeout(() => { removeDownloadToast(downloadInfo.id); }, 5000);
  } finally {
    const index = activeDownloads.findIndex(d => d.id === downloadInfo.id);
    if (index > -1) activeDownloads.splice(index, 1);
    reorganizeDownloadToasts();
  }
}

function createDownloadToast(downloadInfo) {
  const container = document.getElementById('toast-container');
  if (!container) return;
  const toast = document.createElement('div');
  toast.id = `download-toast-${downloadInfo.id}`;
  toast.className = 'toast info';
  toast.style.cssText = `min-width: 350px; pointer-events: auto; margin-bottom: 8px; transition: all 0.3s ease;`;
  toast.innerHTML = `<i class="fa-solid fa-spinner fa-spin" style="color: var(--accent)"></i><div style="flex: 1; min-width: 0;"><div style="font-weight: 600; margin-bottom: 4px; display: flex; justify-content: space-between; align-items: center;"><span><i class="fa-solid fa-download"></i> ${I18N.t('download.title')} #${downloadInfo.id}</span><button onclick="cancelDownload(${downloadInfo.id})" class="btn btn-ghost btn-sm" style="padding: 2px 6px; font-size: 11px;"><i class="fa-solid fa-times"></i></button></div><div style="font-size: 12px; color: var(--text-muted); margin-bottom: 6px;" id="toast-filename-${downloadInfo.id}">${I18N.t('download.connecting')}</div><div class="progress-track" style="height: 4px; margin-top: 4px;"><div id="toast-bar-${downloadInfo.id}" class="progress-bar" style="width: 0%"></div></div><div style="font-size: 11px; color: var(--text-muted); margin-top: 4px; text-align: right;" id="toast-progress-${downloadInfo.id}">0%</div></div>`;
  container.appendChild(toast);
  downloadInfo.toastElement = toast;
  downloadToastElements[downloadInfo.id] = toast;
  reorganizeDownloadToasts();
}

function updateDownloadToast(downloadInfo, currentMB, totalMB, isComplete = false, error = null) {
  const toast = downloadInfo.toastElement;
  if (!toast) return;
  const bar = document.getElementById(`toast-bar-${downloadInfo.id}`);
  const filenameEl = document.getElementById(`toast-filename-${downloadInfo.id}`);
  const progressEl = document.getElementById(`toast-progress-${downloadInfo.id}`);
  if (bar) bar.style.width = `${downloadInfo.progress}%`;
  if (filenameEl) filenameEl.textContent = downloadInfo.filename || I18N.t('download.file_placeholder');
  if (progressEl) {
    if (error) { progressEl.textContent = `❌ ${error}`; progressEl.style.color = 'var(--danger)'; }
    else if (isComplete) { progressEl.textContent = `✅ ${I18N.t('download.completed')} - ${currentMB} ${I18N.t('units.MB')}`; progressEl.style.color = 'var(--success)'; }
    else { progressEl.textContent = `${Math.round(downloadInfo.progress)}% (${currentMB}/${totalMB} ${I18N.t('units.MB')})`; }
  }
  if (error) toast.className = 'toast error';
  else if (isComplete) toast.className = 'toast success';
  else toast.className = 'toast info';
}

function removeDownloadToast(downloadId) {
  const toast = downloadToastElements[downloadId];
  if (toast) {
    toast.style.opacity = '0'; toast.style.transform = 'translateX(100%)';
    setTimeout(() => { toast.remove(); delete downloadToastElements[downloadId]; }, 300);
  }
  const index = activeDownloads.findIndex(d => d.id === downloadId);
  if (index > -1) activeDownloads.splice(index, 1);
  reorganizeDownloadToasts();
}

function reorganizeDownloadToasts() {
  const container = document.getElementById('toast-container');
  if (!container) return;
  const sortedDownloads = [...activeDownloads].sort((a, b) => b.id - a.id);
  sortedDownloads.forEach((download, index) => {
    if (download.toastElement) {
      if (index === 0) container.insertBefore(download.toastElement, container.firstChild);
      else { const nextToast = sortedDownloads[index - 1]?.toastElement; if (nextToast && nextToast.nextSibling) container.insertBefore(download.toastElement, nextToast.nextSibling); }
    }
  });
}

async function cancelDownload(downloadId) {
  const download = activeDownloads.find(d => d.id === downloadId);
  if (download) {
    try {
      const res = await fetch(`${API}/api/download/cancel/${downloadId}`, { method: 'POST', headers: { 'Content-Type': 'application/json' } });
      download.status = 'cancelled';
      updateDownloadToast(download, 0, 0, false, I18N.t('download.cancelled'));
      setTimeout(() => { removeDownloadToast(downloadId); }, 2000);
      showToast(I18N.t('download.cancelled_toast'), 'info');
    } catch (err) { console.error('[cancelDownload] Erreur:', err); removeDownloadToast(downloadId); showToast(I18N.t('toast.cancel_error'), 'error'); }
  }
}

window.openCreateFolderModal = async function() {
    const sourceSelect = document.getElementById('download-source');
    const selectedSourceId = sourceSelect ? sourceSelect.value : null;
    
    let parentPath = null;
    
    // 1️ Déterminer le dossier parent selon la sélection
    if (selectedSourceId && selectedSourceId !== "") {
        // Une source est sélectionnée → utiliser son chemin (extrait entre parenthèses)
        const selectedOption = sourceSelect.options[sourceSelect.selectedIndex];
        const match = selectedOption.text.match(/\((.*?)\)$/);
        if (match) {
            parentPath = match[1];
        } else {
            showToast(I18N.t('toast.source_path_missing') || 'Impossible de trouver le chemin', 'warning');
            return;
        }
    } else {
        // ❌ Aucune source sélectionnée → ouvrir l'explorateur Windows
        showToast(I18N.t('toast.select_parent_folder') || 'Sélectionnez un dossier parent', 'info');
        try {
            const res = await fetch(`${API}/api/picker/folder`, { method: 'POST' });
            const data = await res.json();
            if (!res.ok || !data.path) {
                showToast(I18N.t('toast.selection_cancelled'), 'info');
                return;
            }
            parentPath = data.path;
        } catch (err) {
            showToast(I18N.t('toast.connection_error'), 'error');
            return;
        }
    }
    
    // 2️Modal custom pour saisir le nom (style Stellio)
    const overlay = document.createElement('div');
    overlay.style.cssText = `position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0, 0, 0, 0.75); display: flex; align-items: center; justify-content: center; z-index: 100000; backdrop-filter: blur(5px); animation: fadeIn 0.2s ease;`;
    
    const modal = document.createElement('div');
    modal.style.cssText = `background: var(--bg-secondary, #1e2129); border-radius: 16px; padding: 28px; max-width: 450px; width: 90%; box-shadow: 0 12px 40px rgba(0, 0, 0, 0.6); border: 1px solid var(--border, #2a2f3a); animation: slideIn 0.3s ease;`;
    
    modal.innerHTML = `
        <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 20px;">
            <i class="fa-solid fa-folder-plus" style="font-size: 24px; color: var(--accent, #4ea1d3);"></i>
            <h3 style="margin: 0; color: var(--text-primary, #e6e6e6); font-size: 18px; font-weight: 600;">${I18N.t('download.create_folder') || 'Créer un dossier'}</h3>
        </div>
        <p style="color: var(--text-muted, #9ca3af); margin-bottom: 20px; line-height: 1.5; font-size: 14px;">
            ${I18N.t('download.enter_folder_name') || 'Entrez le nom du nouveau dossier'}
        </p>
        <input type="text" id="folder-name-input" placeholder="${I18N.t('download.folder_name_placeholder') || 'Nom du dossier'}" maxlength="50" style="width: 100%; padding: 12px 16px; border: 2px solid var(--border, #2a2f3a); border-radius: 10px; background: var(--bg-primary, #15181e); color: var(--text-primary, #e6e6e6); font-size: 15px; margin-bottom: 24px; box-sizing: border-box; transition: border-color 0.2s;" onfocus="this.style.borderColor='var(--accent, #4ea1d3)'" onblur="this.style.borderColor='var(--border, #2a2f3a)'">
        <div style="display: flex; gap: 12px; justify-content: flex-end;">
            <button id="folder-cancel-btn" style="padding: 11px 24px; border: none; border-radius: 10px; background: var(--bg-tertiary, #2a2f3a); color: var(--text-primary, #e6e6e6); cursor: pointer; font-weight: 500; transition: all 0.2s; font-size: 14px;" onmouseover="this.style.background='#3a3f4a'" onmouseout="this.style.background='var(--bg-tertiary, #2a2f3a)'">${I18N.t('actions.cancel') || 'Annuler'}</button>
            <button id="folder-ok-btn" style="padding: 11px 24px; border: none; border-radius: 10px; background: var(--accent, #4ea1d3); color: white; cursor: pointer; font-weight: 600; transition: all 0.2s; font-size: 14px;" onmouseover="this.style.background='#3d8fb8'" onmouseout="this.style.background='var(--accent, #4ea1d3)'">${I18N.t('actions.create') || 'Créer'}</button>
        </div>
    `;
    
    overlay.appendChild(modal);
    document.body.appendChild(overlay);
    
    if (!document.getElementById('folder-modal-styles')) {
        const style = document.createElement('style');
        style.id = 'folder-modal-styles';
        style.textContent = `@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } } @keyframes slideIn { from { transform: translateY(-20px); opacity: 0; } to { transform: translateY(0); opacity: 1; } }`;
        document.head.appendChild(style);
    }
    
    const input = modal.querySelector('#folder-name-input');
    const okBtn = modal.querySelector('#folder-ok-btn');
    const cancelBtn = modal.querySelector('#folder-cancel-btn');
    
    setTimeout(() => input.focus(), 100);
    
    const createFolder = async () => {
        const folderName = input.value.trim();
        if (!folderName) {
            input.style.borderColor = 'var(--danger, #ef4444)';
            return;
        }
        
        const cleanFolderName = folderName.replace(/[<>:"/\\|?*]/g, '_');
        const newFolderPath = `${parentPath}/${cleanFolderName}`;
        
        try {
            // ✅ add_as_source: true → ajoute automatiquement aux sources
            const createRes = await fetch(`${API}/api/download/create-folder`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    folder_path: newFolderPath,
                    folder_name: cleanFolderName,
                    add_as_source: true
                })
            });
            
            const result = await createRes.json();
            
            if (createRes.ok) {
                showToast(I18N.t('toast.folder_created') || 'Dossier créé avec succès', 'success');
                
                // ✅ Recharger les sources (panneau gauche) et le dropdown téléchargement
                await loadSources();
                await loadDownloadSources();
                
                // ✅ Pré-sélectionner le nouveau dossier dans le dropdown
                setTimeout(() => {
                    const opts = sourceSelect.options;
                    for (let i = 0; i < opts.length; i++) {
                        if (opts[i].text.includes(cleanFolderName)) {
                            sourceSelect.selectedIndex = i;
                            break;
                        }
                    }
                }, 500);
            } else {
                showToast(result.error || I18N.t('toast.folder_create_error') || 'Erreur de création', 'error');
            }
        } catch (err) {
            console.error('[Create Folder]', err);
            showToast(I18N.t('toast.connection_error') || 'Erreur de connexion', 'error');
        }
        
        overlay.remove();
    };
    
    okBtn.addEventListener('click', createFolder);
    cancelBtn.addEventListener('click', () => overlay.remove());
    input.addEventListener('keypress', (e) => { if (e.key === 'Enter') createFolder(); });
    input.addEventListener('input', () => { input.style.borderColor = 'var(--border, #2a2f3a)'; });
    overlay.addEventListener('click', (e) => { if (e.target === overlay) overlay.remove(); });
};

// Fonction auxiliaire pour le CAS B (ouvrir explorateur si pas de source sélectionnée)
async function selectParentFolderManually(folderName) {
    try {
        const res = await fetch(`${API}/api/picker/folder`, { method: 'POST' });
        const data = await res.json();
        
        if (!res.ok || !data.path) {
            showToast(I18N.t('toast.selection_cancelled'), 'info');
            return;
        }

        const parentPath = data.path;
        const newFolderPath = `${parentPath}/${folderName}`;

        const createRes = await fetch(`${API}/api/download/create-folder`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                folder_path: newFolderPath,
                folder_name: folderName,
                add_as_source: true
            })
        });

        const result = await createRes.json();

        if (createRes.ok) {
            showToast(I18N.t('toast.folder_created'), 'success');
            await loadDownloadSources();
        } else {
            showToast(result.error || I18N.t('toast.folder_create_error'), 'error');
        }
    } catch (err) {
        showToast(I18N.t('toast.connection_error'), 'error');
    }
}

// ✅ Fonction pour parcourir les dossiers
window.browseDownloadLocation = async function() {
  try {
    const res = await fetch(`${API}/api/picker/folder`, { method: 'POST' });
    const data = await res.json();
    if (res.ok && data.path) {
      showToast(`📍 ${I18N.t('toast.folder_selected')}: ${data.path}`, 'info');
      // Recharger les sources pour inclure le nouveau dossier
      await loadDownloadSources();
    }
  } catch (err) {
    showToast(I18N.t('toast.picker_unavailable'), 'warning');
  }
};

// ============================================
// 🔍 FILTRES
// ============================================
function applyFilters() {
  let files = [...allFiles];
  if (activeTypeFilters?.length > 0 && activeTypeFilters.length < 3) files = files.filter(f => activeTypeFilters.includes(f.extension));
  if (currentSizeFilter) files = files.filter(f => { const mb = (f.size || 0) / (1024 * 1024); return mb >= (currentSizeFilter.min || 0) && mb <= (currentSizeFilter.max !== undefined ? currentSizeFilter.max : Infinity); });
  if (activeTagFilters.size > 0) files = files.filter(f => { const fileTags = new Set((f.tags || []).map(t => t.name.toLowerCase())); for (const tag of activeTagFilters) { if (!fileTags.has(tag.toLowerCase())) return false; } return true; });
  filteredFiles = files;
  applySorting();
  renderFiles();
  updateSidebarCounts(filteredFiles);
  startThumbnailGeneration();
}

document.getElementById('toggle-astuces')?.addEventListener('click', function () {
  const menu = document.getElementById('astuces-menu');
  const icon = document.getElementById('astuces-icon');
  if (menu.style.display === 'none') {
    menu.style.display = 'block';
    icon.classList.remove('fa-chevron-down');
    icon.classList.add('fa-chevron-up');
  } else {
    menu.style.display = 'none';
    icon.classList.remove('fa-chevron-up');
    icon.classList.add('fa-chevron-down');
  }
});

function toggleAstuceSubmenu(submenuId) {
  const submenu = document.getElementById(submenuId);
  const icon = document.getElementById(submenuId.replace('astuces', 'astuces-icon'));
  if (submenu.style.display === 'none') {
    submenu.style.display = 'block';
    icon.classList.remove('fa-chevron-right');
    icon.classList.add('fa-chevron-down');
  } else {
    submenu.style.display = 'none';
    icon.classList.remove('fa-chevron-down');
    icon.classList.add('fa-chevron-right');
  }
}

function openFiltersModal() {
  document.querySelectorAll('.filter-type').forEach(cb => { cb.checked = !activeTypeFilters || activeTypeFilters.length === 0 || activeTypeFilters.includes(cb.value); });
  document.getElementById('size-min').value = currentSizeFilter?.min || '';
  document.getElementById('size-max').value = currentSizeFilter?.max || '';
  renderFilterTagsModal();
  openModal('modal-filters');
}

function applyFiltersFromModal() {
  const selectedTypes = [...document.querySelectorAll('.filter-type:checked')].map(cb => cb.value);
  activeTypeFilters = selectedTypes.length === 3 ? [] : selectedTypes;
  const minVal = parseFloat(document.getElementById('size-min').value);
  const maxVal = parseFloat(document.getElementById('size-max').value);
  currentSizeFilter = { min: isNaN(minVal) ? 0 : minVal, max: isNaN(maxVal) ? Infinity : maxVal };
  closeModal('modal-filters');
  applyFilters();
  showToast(I18N.t('toast.filters_applied'), 'success');
}

function resetFilters() {
  document.querySelectorAll('.filter-type').forEach(cb => cb.checked = true);
  document.getElementById('size-min').value = '';
  document.getElementById('size-max').value = '';
  activeTypeFilters = [];
  currentSizeFilter = null;
  activeTagFilters.clear();
  closeModal('modal-filters');
  applyFilters();
  showToast(I18N.t('toast.filters_reset'), 'info');
}

function renderFilterTagsModal() {
  const container = document.getElementById('filter-tags-modal');
  if (!container) return;
  if (!allTags.length) {
    container.innerHTML = `<p style="color:var(--text-muted);font-size:13px">${I18N.t('toast.tag_empty')}</p>`;
    return;
  }
  container.innerHTML = allTags.map(t => `<label class="checkbox-label" style="margin-bottom: 8px;"><input type="checkbox" value="${escapeHtml(t.name)}" class="filter-tag-modal" ${activeTagFilters.has(t.name) ? 'checked' : ''}><span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:${t.color};margin-right:6px;"></span>${escapeHtml(t.name)} <span style="color:var(--text-muted)">(${t.count})</span></label>`).join('');
  container.querySelectorAll('.filter-tag-modal').forEach(checkbox => {
    checkbox.addEventListener('change', (e) => {
      if (e.target.checked) activeTagFilters.add(e.target.value);
      else activeTagFilters.delete(e.target.value);
    });
  });
  I18N.apply();
}

// ============================================
// ✂️ ENVOI AU SLICER
// ============================================
function sendToSlicer(path, name) {
  currentSlicerFile = path;
  document.getElementById('slicer-file-name').textContent = `${I18N.t('modal.selected_file')}: ${name}`;
  openModal('modal-slicer');
}

// ============================================
// 🎮 VISUALISEUR 3D (AVEC NETTOYAGE MÉMOIRE)
// ============================================
let viewer3D = null, viewerControls = null, viewerScene = null, viewerCamera = null, viewerMesh = null, viewerRenderer = null;

function open3DViewer(fileName, filePath) {
  document.getElementById('viewer-title').innerHTML = `<i class="fa-solid fa-cube"></i> ${fileName}`;
  openModal('modal-3d-viewer');
  load3DModel(filePath);
}

function load3DModel(filePath) {
  const container = document.getElementById('viewer-canvas-container');
  container.innerHTML = `<div style="display:flex;align-items:center;justify-content:center;height:100%;color:var(--text-muted);"><i class="fa-solid fa-spinner fa-spin fa-2x"></i></div>`;
  
  fetch(`${API}/api/file/data?path=${encodeURIComponent(filePath)}`)
    .then(res => {
      if (!res.ok) throw new Error(I18N.t('toast.file_not_found'));
      return res.blob();
    })
    .then(blob => {
      const url = URL.createObjectURL(blob);
      const ext = filePath.split('.').pop().toLowerCase();
      
      viewerScene = new THREE.Scene();
      viewerScene.background = new THREE.Color('#1a1d23');
      viewerCamera = new THREE.PerspectiveCamera(45, container.clientWidth / container.clientHeight, 0.1, 10000);
      viewerCamera.position.set(50, 50, 50);
      viewerRenderer = new THREE.WebGLRenderer({ antialias: true });
      viewerRenderer.setSize(container.clientWidth, container.clientHeight);
      viewerRenderer.setPixelRatio(window.devicePixelRatio);
      container.innerHTML = '';
      container.appendChild(viewerRenderer.domElement);
      
      viewerControls = new THREE.OrbitControls(viewerCamera, viewerRenderer.domElement);
      viewerControls.enableDamping = true;
      viewerControls.dampingFactor = 0.05;
      
      const ambientLight = new THREE.AmbientLight(0x404040, 2);
      viewerScene.add(ambientLight);
      const directionalLight = new THREE.DirectionalLight(0xffffff, 1);
      directionalLight.position.set(50, 50, 50);
      viewerScene.add(directionalLight);
      
      let loader, geometry = null, material = null;
      if (ext === 'stl') loader = new THREE.STLLoader();
      else if (ext === 'obj') loader = new THREE.OBJLoader();
      else throw new Error(I18N.t('toast.invalid_format'));
      
      loader.load(url, function (object) {
        if (object.isGroup || object.isObject3D) {
          viewerMesh = object;
          viewerScene.add(object);
        } else {
          material = new THREE.MeshPhongMaterial({ color: 0x4ea1d3, specular: 0x111111, shininess: 200, flatShading: false });
          viewerMesh = new THREE.Mesh(object, material);
          object.computeBoundingBox();
          const center = new THREE.Vector3();
          object.boundingBox.getCenter(center);
          object.translate(-center.x, -center.y, -center.z);
          viewerScene.add(viewerMesh);
          const size = new THREE.Vector3();
          object.boundingBox.getSize(size);
          const maxDim = Math.max(size.x, size.y, size.z);
          const fov = viewerCamera.fov * (Math.PI / 180);
          const cameraZ = Math.abs(maxDim / 2 / Math.tan(fov / 2)) * 1.5;
          viewerCamera.position.set(cameraZ, cameraZ, cameraZ);
          viewerCamera.lookAt(0, 0, 0);
        }
        
        function animate() {
          if (!container.contains(viewerRenderer.domElement)) return;
          requestAnimationFrame(animate);
          viewerControls.update();
          viewerRenderer.render(viewerScene, viewerCamera);
        }
        animate();
        
        // 🚀 Nettoyage mémoire THREE.js
        URL.revokeObjectURL(url);
        if (geometry) geometry.dispose();
        if (material) material.dispose();
        
      }, undefined, function (error) {
        console.error('[3D Viewer]', error);
        container.innerHTML = `<div style="display:flex;align-items:center;justify-content:center;height:100%;color:var(--danger);">${I18N.t('toast.connection_error')}</div>`;
      });
    })
    .catch(err => {
      console.error('[3D Viewer]', err);
      container.innerHTML = `<div style="display:flex;align-items:center;justify-content:center;height:100%;color:var(--danger);">${I18N.t('toast.connection_error')}</div>`;
    });
}

function onViewerResize() {
  if (!viewerRenderer || !viewerCamera) return;
  const container = document.getElementById('viewer-canvas-container');
  viewerCamera.aspect = container.clientWidth / container.clientHeight;
  viewerCamera.updateProjectionMatrix();
  viewerRenderer.setSize(container.clientWidth, container.clientHeight);
}

// ============================================
// ⚙️ PARAMÈTRES & THÈMES
// ============================================
async function loadSlicerSettings() {
  const select = document.getElementById('default-slicer-select');
  if (!select) return;
  try {
    const res = await fetch(`${API}/api/settings`);
    if (res.ok) {
      const data = await res.json();
      if (data.default_slicer) select.value = data.default_slicer;
    }
  } catch (err) { console.warn('[Slicer Settings] Échec'); }
}

function applyTheme(mode) {
  if (mode === 'auto') {
    const isLight = window.matchMedia && window.matchMedia('(prefers-color-scheme: light)').matches;
    document.documentElement.setAttribute('data-theme', isLight ? 'light' : 'dark');
  } else {
    document.documentElement.setAttribute('data-theme', mode);
  }
}

function applyFabricant(fabricant) {
  document.documentElement.setAttribute('data-fabricant', fabricant);
}

async function initSettings() {
  const themeSelector = document.getElementById('theme-selector');
  const fabricantSelector = document.getElementById('fabricant-selector');
  if (!themeSelector || !fabricantSelector) {
    console.warn('[Theme] ⚠️ Sélecteurs introuvables');
    return;
  }
  let savedTheme = 'dark', savedFabricant = 'stellio';
  try {
    const res = await fetch(`${API}/api/settings`);
    if (res.ok) {
      const data = await res.json();
      savedTheme = data.theme || savedTheme;
      savedFabricant = data.fabricant || savedFabricant;
    }
  } catch (e) { console.warn('[Theme] Backend indisponible'); }
  if (!savedTheme || savedTheme === 'undefined') savedTheme = localStorage.getItem('stellio-theme') || 'dark';
  if (!savedFabricant || savedFabricant === 'undefined') savedFabricant = localStorage.getItem('stellio-fabricant') || 'stellio';
  themeSelector.value = savedTheme;
  fabricantSelector.value = savedFabricant;
  applyTheme(savedTheme);
  applyFabricant(savedFabricant);
  
  themeSelector.addEventListener('change', async (e) => {
    const mode = e.target.value;
    localStorage.setItem('stellio-theme', mode);
    try {
      await fetch(`${API}/api/settings`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ theme: mode }) });
    } catch (err) { console.warn('[Theme] Échec sauvegarde:', err); }
    applyTheme(mode);
  });
  
  fabricantSelector.addEventListener('change', async (e) => {
    const fabricant = e.target.value;
    localStorage.setItem('stellio-fabricant', fabricant);
    try {
      await fetch(`${API}/api/settings`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ fabricant }) });
    } catch (err) { console.warn('[Theme] Échec sauvegarde:', err); }
    applyFabricant(fabricant);
  });
  
  if (window.matchMedia) {
    window.matchMedia('(prefers-color-scheme: light)').addEventListener('change', e => {
      if (localStorage.getItem('stellio-theme') === 'auto') {
        applyTheme('auto');
        console.log('[Theme] 🔄 Système:', e.matches ? I18N.t('settings.theme_light') : I18N.t('settings.theme_dark'));
      }
    });
  }
  loadSlicerSettings();
}

// ============================================
//  ÉCOUTEURS D'ÉVÉNEMENTS
// ============================================
function setupEventListeners() {
  // === AUTHENTIFICATION ===
  document.getElementById('register-form')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const username = document.getElementById('reg-username').value.trim();
    const email = document.getElementById('reg-email')?.value.trim() || '';
    const password = document.getElementById('reg-password').value;
    const confirm = document.getElementById('reg-password-confirm').value;
    if (password !== confirm) { showToast(I18N.t('toast.password_mismatch'), 'error'); return; }
    if (password.length < 3) { showToast(I18N.t('toast.password_short'), 'error'); return; }
    try {
      const res = await fetch(`${API}/api/auth/register`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ username, password, email }) });
      const data = await res.json();
      if (res.ok) { showToast(I18N.t('toast.account_created'), 'success'); showApp(data.user); }
      else showToast(data.error, 'error');
    } catch (err) { showToast(I18N.t('toast.server_error'), 'error'); }
  });
  
  document.getElementById('login-form')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const username = document.getElementById('login-username').value.trim();
    const password = document.getElementById('login-password').value;
    try {
      const res = await fetch(`${API}/api/auth/login`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ username, password }) });
      const data = await res.json();
      if (res.ok) { showToast(I18N.t('toast.logged_in'), 'success'); showApp(data.user); }
      else showToast(data.error, 'error');
    } catch (err) { showToast(I18N.t('toast.connection_error'), 'error'); }
  });
  
  document.getElementById('show-register')?.addEventListener('click', (e) => { e.preventDefault(); showPanel('register-panel'); });
  document.getElementById('show-forgot')?.addEventListener('click', (e) => { e.preventDefault(); showPanel('forgot-panel'); });
  
  document.getElementById('forgot-form')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const email = document.getElementById('forgot-email').value.trim();
    const btn = e.target.querySelector('button');
    const originalText = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> ${I18N.t('auth.send_code')}`;
    try {
      const res = await fetch(`${API}/api/auth/forgot`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ email }) });
      const data = await res.json();
      if (res.ok) {
        showToast(I18N.t('toast.code_sent'), 'success');
        document.getElementById('reset-email-display').textContent = email;
        document.getElementById('forgot-email').value = email;
        showPanel('reset-panel');
      } else showToast(data.error, 'error');
    } catch (err) { showToast(I18N.t('toast.connection_error'), 'error'); }
    finally { btn.disabled = false; btn.innerHTML = originalText; }
  });
  
  document.getElementById('reset-form')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const email = document.getElementById('reset-email-display').textContent;
    const code = document.getElementById('reset-code').value.trim();
    const password = document.getElementById('reset-password').value;
    const confirm = document.getElementById('reset-password-confirm').value;
    if (password !== confirm) { showToast(I18N.t('toast.password_mismatch'), 'error'); return; }
    try {
      const res = await fetch(`${API}/api/auth/reset`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ email, code, password }) });
      const data = await res.json();
      if (res.ok) { showToast(I18N.t('toast.password_reset'), 'success'); showPanel('login-panel'); }
      else showToast(data.error, 'error');
    } catch (err) { showToast(I18N.t('toast.network_error'), 'error'); }
  });
  
  document.getElementById('global-logout-btn')?.addEventListener('click', async () => {
    await fetch(`${API}/api/auth/logout`, { method: 'POST' });
    location.reload();
  });
  
  // === SLICER ===
  document.getElementById('default-slicer-select')?.addEventListener('change', async (e) => {
    try {
      await fetch(`${API}/api/settings`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ default_slicer: e.target.value }) });
      showToast(I18N.t('toast.slicer_updated'), 'success');
    } catch (err) { showToast(I18N.t('toast.error'), 'error'); }
  });
  
  // === NAVIGATION ===
  document.querySelectorAll('.nav-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const page = btn.dataset.page;
      if (btn.id === 'nav-favorites-btn') { toggleFavoritesFilterFromNav(); return; }
      if (page === 'library') {
        if (showFavoritesOnly) {
          showFavoritesOnly = false;
          document.getElementById('nav-favorites-btn')?.classList.remove('active');
          document.getElementById('favorites-filter-btn')?.classList.remove('active');
          const headerTitle = document.getElementById('header-page-title');
          if (headerTitle) headerTitle.innerHTML = `<i class="fa-solid fa-layer-group"></i> ${I18N.t('nav.library')}`;
        }
        document.querySelector('.nav-btn[data-page="library"]')?.classList.add('active');
      }
      if (btn.innerHTML.includes('fa-filter')) { openFiltersModal(); return; }
      if (!page) return;
      document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
      document.getElementById(`page-${page}`)?.classList.add('active');
      const titleKey = btn.dataset.titleKey || 'app.title';
      document.getElementById('header-page-title').innerHTML = `<i class="fa-solid ${btn.dataset.icon || 'fa-layer-group'}"></i> ${I18N.t(titleKey)}`;
      if (page === 'library') loadFiles();
	  if (page === 'printers') loadPrinters();
      if (page === 'settings') loadSources();
    });
  });
  
  // === VUES ===
  document.querySelectorAll('.view-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.view-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      currentView = btn.dataset.view;
      document.getElementById('files-grid').className = `files-grid ${currentView}`;
      renderFiles();
    });
  });
  
  // === SÉLECTION ===
  document.getElementById('select-all-btn')?.addEventListener('click', () => toggleSelectionMode());
  document.getElementById('select-toggle-all')?.addEventListener('click', () => selectAllFiles());
  document.getElementById('send-selected-to-slicer-btn')?.addEventListener('click', () => sendSelectedToSlicer());
  document.getElementById('cancel-selection-btn')?.addEventListener('click', () => toggleSelectionMode());
  
  // === SOURCES ===
  document.getElementById('add-source-btn')?.addEventListener('click', () => openModal('modal-select-type'));
  document.querySelectorAll('.type-card').forEach(card => {
    card.addEventListener('click', async () => {
      const type = card.dataset.type;
      closeModal('modal-select-type');
      if (type === 'folder' || type === 'file') await handleFilePicker(type);
      else if (type === 'smb') {
        document.getElementById('smb-form')?.reset();
        document.getElementById('smb-name').value = '';
        if (document.getElementById('add-smb-btn')) document.getElementById('add-smb-btn').disabled = true;
        openModal('modal-smb');
      } else if (type === 'nfs') {
        document.getElementById('nfs-form')?.reset();
        document.getElementById('nfs-name').value = '';
        if (document.getElementById('add-nfs-btn')) document.getElementById('add-nfs-btn').disabled = true;
        openModal('modal-nfs');
      }
    });
  });
  
  document.getElementById('rename-source-form')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const id = document.getElementById('rename-source-id').value;
    const newName = document.getElementById('rename-source-name').value.trim();
    if (!newName) { showToast(I18N.t('toast.rename_empty'), 'error'); return; }
    try {
      const res = await fetch(`${API}/api/sources/${id}`, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ name: newName }) });
      const data = await res.json();
      if (res.ok) { showToast(I18N.t('toast.source_renamed'), 'success'); closeModal('modal-rename-source'); loadSources(); }
      else showToast(data.error || I18N.t('toast.error'), 'error');
    } catch (err) { showToast(I18N.t('toast.fetch_error'), 'error'); }
  });
  
  const addSmbBtn = document.getElementById('add-smb-btn');
  const addNfsBtn = document.getElementById('add-nfs-btn');
  ['smb-host', 'smb-share', 'smb-user', 'smb-pass'].forEach(id => {
    document.getElementById(id)?.addEventListener('input', () => { if (addSmbBtn) addSmbBtn.disabled = true; });
  });
  ['nfs-host', 'nfs-path'].forEach(id => {
    document.getElementById(id)?.addEventListener('input', () => { if (addNfsBtn) addNfsBtn.disabled = true; });
  });
  
  document.getElementById('smb-form')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    if (addSmbBtn?.disabled) { showToast(I18N.t('toast.test_required'), 'warning'); return; }
    const name = document.getElementById('smb-name').value.trim();
    const host = document.getElementById('smb-host').value.trim();
    const share = document.getElementById('smb-share').value.trim();
    const username = document.getElementById('smb-user').value.trim();
    const password = document.getElementById('smb-pass').value;
    if (await addSource('smb', name, `\\\\${host}\\${share}`, { username, password, type: 'smb' })) {
      showToast(I18N.t('toast.source_added'), 'success');
      closeModal('modal-smb');
      loadSources();
      loadFiles();
    }
  });
  
  document.getElementById('nfs-form')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    if (addNfsBtn?.disabled) { showToast(I18N.t('toast.test_required'), 'warning'); return; }
    const data = { name: document.getElementById('nfs-name').value.trim(), host: document.getElementById('nfs-host').value.trim(), path: document.getElementById('nfs-path').value.trim() };
    if (await addSource('nfs', data.name, `${data.host}:${data.path}`, data)) {
      showToast(I18N.t('toast.source_added'), 'success');
      closeModal('modal-nfs');
      loadSources();
    }
  });
  
  document.getElementById('test-smb-btn')?.addEventListener('click', async () => {
    const host = document.getElementById('smb-host').value.trim();
    const share = document.getElementById('smb-share').value.trim();
    const username = document.getElementById('smb-user').value.trim();
    const password = document.getElementById('smb-pass').value;
    const resultDiv = document.getElementById('smb-test-result');
    const btn = document.getElementById('test-smb-btn');
    if (!host || !share) { resultDiv.innerHTML = `<span style="color: var(--warning)"><i class="fa-solid fa-exclamation-triangle"></i> ${I18N.t('toast.fill_required')}</span>`; return; }
    btn.disabled = true;
    btn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> ${I18N.t('toast.refreshing')}`;
    resultDiv.innerHTML = '';
    try {
      const res = await fetch(`${API}/api/test-connection`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ type: 'smb', host, share, username, password }) });
      const data = await res.json();
      if (res.ok) { resultDiv.innerHTML = `<span style="color: var(--success)"><i class="fa-solid fa-check-circle"></i> ${data.message}</span>`; if (addSmbBtn) addSmbBtn.disabled = false; }
      else { resultDiv.innerHTML = `<span style="color: var(--danger)"><i class="fa-solid fa-times-circle"></i> ${data.error}</span>`; if (addSmbBtn) addSmbBtn.disabled = true; }
    } catch (err) { resultDiv.innerHTML = `<span style="color: var(--danger)"><i class="fa-solid fa-times-circle"></i> ${I18N.t('toast.connection_error')}</span>`; if (addSmbBtn) addSmbBtn.disabled = true; }
    finally { btn.disabled = false; btn.innerHTML = `<i class="fa-solid fa-plug"></i> ${I18N.t('actions.test_connection')}`; }
  });
  
  document.getElementById('test-nfs-btn')?.addEventListener('click', async () => {
    const host = document.getElementById('nfs-host').value.trim();
    const path = document.getElementById('nfs-path').value.trim();
    const resultDiv = document.getElementById('nfs-test-result');
    const btn = document.getElementById('test-nfs-btn');
    if (!host || !path) { resultDiv.innerHTML = `<span style="color: var(--warning)"><i class="fa-solid fa-exclamation-triangle"></i> ${I18N.t('toast.fill_nfs')}</span>`; return; }
    btn.disabled = true;
    btn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> ${I18N.t('toast.refreshing')}`;
    resultDiv.innerHTML = '';
    try {
      const res = await fetch(`${API}/api/test-connection`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ type: 'nfs', host, path }) });
      const data = await res.json();
      if (res.ok) { resultDiv.innerHTML = `<span style="color: var(--success)"><i class="fa-solid fa-check-circle"></i> ${data.message}</span>`; if (addNfsBtn) addNfsBtn.disabled = false; }
      else { resultDiv.innerHTML = `<span style="color: var(--danger)"><i class="fa-solid fa-times-circle"></i> ${data.error}</span>`; if (addNfsBtn) addNfsBtn.disabled = true; }
    } catch (err) { resultDiv.innerHTML = `<span style="color: var(--danger)"><i class="fa-solid fa-times-circle"></i> ${I18N.t('toast.connection_error')}</span>`; if (addNfsBtn) addNfsBtn.disabled = true; }
    finally { btn.disabled = false; btn.innerHTML = `<i class="fa-solid fa-plug"></i> ${I18N.t('actions.test_connection')}`; }
  });
  
  async function handleFilePicker(type) {
    const url = type === 'folder' ? `${API}/api/picker/folder` : `${API}/api/picker/file`;
    try {
      showToast(I18N.t('toast.refreshing'), 'info');
      const res = await fetch(url, { method: 'POST' });
      const data = await res.json();
      if (!res.ok) {
        const errorMsg = data.error || I18N.t('actions.cancel');
        if (errorMsg.includes('tkinter')) showToast(I18N.t('toast.explorer_unavailable'), 'warning');
        else if (errorMsg === I18N.t('actions.cancel')) showToast(I18N.t('toast.selection_cancelled_user'), 'info');
        else showToast(`❌ ${errorMsg}`, 'error');
        return;
      }
      let success = false;
      if (type === 'folder' && data.path) {
        const folderName = data.path.split('/').pop() || I18N.t('source.local_folder');
        success = await addSource('folder', folderName, data.path, {});
        if (success) showToast(`📁 ${I18N.t('source.local_folder')} "${folderName}" ${I18N.t('toast.source_added').toLowerCase()}`, 'success');
      } else if (type === 'file' && data.paths?.length) {
        if (data.paths.length === 1) {
          success = await addSource('file', data.paths[0].split('/').pop(), data.paths[0], {});
          if (success) showToast(I18N.t('toast.source_added'), 'success');
        } else {
          for (const p of data.paths) await addSource('file', p.split('/').pop(), p, {});
          showToast(`✅ ${data.paths.length} ${I18N.t('toast.source_added')}`, 'success');
          success = true;
        }
      }
      if (success) { loadSources(); loadFiles(); }
    } catch (err) { showToast(I18N.t('toast.picker_error'), 'error'); console.error('[handleFilePicker]', err); }
  }
  
  document.getElementById('refresh-files')?.addEventListener('click', () => { loadFiles(); showToast(I18N.t('toast.refreshing'), 'info'); });
  
  document.getElementById('global-search')?.addEventListener('input', (e) => {
    const query = e.target.value.toLowerCase();
    filteredFiles = allFiles.filter(f => f.name.toLowerCase().includes(query) || f.path.toLowerCase().includes(query));
    applySorting();
    renderFiles();
    updateSidebarCounts(filteredFiles);
  });
  
  document.getElementById('sort-select')?.addEventListener('change', (e) => { currentSort = e.target.value; applySorting(); renderFiles(); });
  document.getElementById('apply-filters')?.addEventListener('click', applyFilters);
  
  document.getElementById('confirm-slicer')?.addEventListener('click', async () => {
    if (!currentSlicerFile) return;
    try {
      const res = await fetch(`${API}/api/slicer/send`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ file_path: currentSlicerFile }) });
      const data = await res.json();
      showToast(res.ok ? I18N.t('toast.files_sent') : data.error, res.ok ? 'success' : 'error');
    } catch (err) { showToast(I18N.t('toast.send_error'), 'error'); }
    closeModal('modal-slicer');
  });
  
document.getElementById('contact-form')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const btn = e.target.querySelector('button[type="submit"]');
    const originalBtn = btn.innerHTML;
    btn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> ${I18N.t('contact.send')}`;
    btn.disabled = true;
    
    const data = {
        name: document.getElementById('contact-name').value,
        email: document.getElementById('contact-email').value,
        subject: document.getElementById('contact-subject').value,
        message: document.getElementById('contact-message').value
    };
    
    try {
        const res = await fetch(`${API}/api/contact/send`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        
        const result = await res.json();
        if (res.ok) {
            showToast(I18N.t('toast.message_sent') || 'Message envoyé !', 'success');
            document.getElementById('contact-form').reset();
        } else {
            showToast(result.error || I18N.t('toast.send_fail'), 'error');
        }
    } catch (err) {
        showToast(I18N.t('toast.fetch_error'), 'error');
    } finally {
        btn.innerHTML = originalBtn;
        btn.disabled = false;
    }
});
  
  document.querySelectorAll('.modal').forEach(modal => {
    modal.addEventListener('click', (e) => { if (e.target === modal) modal.classList.add('hidden'); });
  });
  document.getElementById('modal-about')?.addEventListener('click', (e) => { if (e.target.id === 'modal-about') closeModal('modal-about'); });
  
  const mainContent = document.querySelector('.main-content');
  const scrollToTopBtn = document.getElementById('scroll-to-top');
  if (mainContent && scrollToTopBtn) {
    mainContent.addEventListener('scroll', () => {
      if (mainContent.scrollTop > 300) scrollToTopBtn.classList.add('visible');
      else scrollToTopBtn.classList.remove('visible');
    });
    scrollToTopBtn.addEventListener('click', () => { mainContent.scrollTo({ top: 0, behavior: 'smooth' }); });
  }
  
  document.getElementById('force-refresh-btn')?.addEventListener('click', async () => {
    showToast(I18N.t('toast.refreshing'), 'info');
    try { await fetch(`${API}/api/files/invalidate-cache`, { method: 'POST' }); } catch (e) { /* Ignore */ }
    await loadFiles();
    showToast(I18N.t('toast.refreshed'), 'success');
  });
  
  document.getElementById('manage-tags-btn')?.addEventListener('click', () => openTagManagerModal('global'));
  document.getElementById('manage-tags-modal-btn')?.addEventListener('click', () => { closeModal('modal-filters'); setTimeout(() => openTagManagerModal('global'), 100); });
  
  document.getElementById('filter-tags')?.addEventListener('change', (e) => {
    if (e.target.classList.contains('filter-tag')) {
      if (e.target.checked) activeTagFilters.add(e.target.value);
      else activeTagFilters.delete(e.target.value);
      applyFilters();
    }
  });
  document.getElementById('favorites-filter-btn')?.addEventListener('click', () => toggleFavoritesFilter(null));
  document.getElementById('add-account-btn')?.addEventListener('click', () => openAccountModal());
  document.getElementById('account-form')?.addEventListener('submit', saveAccount);
  document.getElementById('telegram-send-code')?.addEventListener('click', sendTelegramCode);
  document.getElementById('telegram-verify')?.addEventListener('click', verifyTelegramCode);
  document.getElementById('download-form')?.addEventListener('submit', handleDownload);
  
  // === 🌍 SÉLECTEUR DE LANGUE ===
  document.getElementById('language-selector')?.addEventListener('change', (e) => { I18N.setLanguage(e.target.value); translateSortOptions(); });
  // === 🌍 SÉLECTEUR DE LANGUE (PAGE AUTHENTIFICATION) ===
  document.getElementById('language-selector-auth')?.addEventListener('change', (e) => { 
  	   I18N.setLanguage(e.target.value); 
	  setTimeout(() => {
	 	  translateAuthFields();
		  I18N.apply(document.querySelector('.auth-panel:not(.hidden)') || document);
	  }, 100);
  });
  // === Synchronisation auth selector ===
  document.addEventListener('i18n:changed', (e) => {
    const authSelector = document.getElementById('language-selector-auth');
    if (authSelector && authSelector.value !== e.detail.lang) authSelector.value = e.detail.lang;
    translateSortOptions();
    translateAuthFields();
    const activeBtn = document.querySelector('.nav-btn.active');
    if (activeBtn) {
      const titleKey = activeBtn.dataset.titleKey || 'app.title';
      const iconClass = activeBtn.dataset.icon || 'fa-layer-group';
      const headerTitle = document.getElementById('header-page-title');
      if (headerTitle) headerTitle.innerHTML = `<i class="fa-solid ${iconClass}"></i> ${I18N.t(titleKey)}`;
    }
    const searchInput = document.getElementById('global-search');
    if (searchInput) searchInput.placeholder = I18N.t('search.placeholder');
    I18N.apply();
  });
}

// ============================================
//  SÉLECTION PAR DOSSIER
// ============================================
let selectedFolderFiles = new Set();

window.selectFolderFiles = function (folderPath, btnElement) {
  const icon = btnElement.querySelector('i');
  const folderCards = document.querySelectorAll(`.file-card[data-path^="${folderPath}/"], .file-card[data-path="${folderPath}"]`);
  const allSelected = Array.from(folderCards).every(card => selectedFolderFiles.has(card.dataset.path));
  if (allSelected) {
    folderCards.forEach(card => { selectedFolderFiles.delete(card.dataset.path); card.classList.remove('selected'); });
    icon.classList.remove('fa-check-square');
    icon.classList.add('fa-square');
    btnElement.innerHTML = `<i class="fa-regular fa-square"></i> ${I18N.t('actions.select')}`;
  } else {
    folderCards.forEach(card => { selectedFolderFiles.add(card.dataset.path); card.classList.add('selected'); });
    icon.classList.remove('fa-square');
    icon.classList.add('fa-check-square');
    btnElement.innerHTML = `<i class="fa-solid fa-check-square"></i> ${I18N.t('actions.cancel')}`;
  }
  updateFolderSelectionBar();
};

function updateFolderSelectionBar() {
  const count = selectedFolderFiles.size;
  let bar = document.getElementById('folder-selection-bar');
  const countEl = document.getElementById('folder-selection-count');
  if (count > 0) {
    if (!bar) {
      bar = document.createElement('div');
      bar.id = 'folder-selection-bar';
      bar.className = 'folder-selection-bar';
      bar.style.display = 'flex';
      bar.innerHTML = `<span id="folder-selection-count">${I18N.tp('common.file_count', count, { count })} ${I18N.t('actions.select').toLowerCase()}</span><button onclick="sendFolderSelectionToSlicer()" class="btn btn-primary btn-sm"><i class="fa-solid fa-scissors"></i> ${I18N.t('actions.send_to_slicer')}</button><button onclick="clearFolderSelection()" class="btn btn-ghost btn-sm"><i class="fa-solid fa-times"></i> ${I18N.t('actions.cancel')}</button>`;
      document.querySelector('.main-content').appendChild(bar);
    } else {
      bar.style.display = 'flex';
      if (countEl) countEl.textContent = `${I18N.tp('common.file_count', count, { count })} ${I18N.t('actions.select').toLowerCase()}`;
    }
  } else {
    if (bar) bar.style.display = 'none';
  }
}

window.sendFolderSelectionToSlicer = async function () {
  if (selectedFolderFiles.size === 0) { showToast(I18N.t('toast.no_selection'), 'warning'); return; }
  try {
    const res = await fetch(`${API}/api/slicer/send-batch`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ files: [...selectedFolderFiles] }) });
    const data = await res.json();
    if (res.ok) { showToast(`✅ ${data.message}`, 'success'); clearFolderSelection(); }
    else { showToast(data.error || I18N.t('toast.send_error'), 'error'); }
  } catch (err) { showToast(I18N.t('toast.connection_error'), 'error'); }
};

window.clearFolderSelection = function () {
  selectedFolderFiles.clear();
  document.querySelectorAll('.file-card.selected').forEach(card => card.classList.remove('selected'));
  document.querySelectorAll('.folder-select-btn').forEach(btn => {
    const icon = btn.querySelector('i');
    if (icon) { icon.classList.remove('fa-check-square'); icon.classList.add('fa-square'); }
    btn.innerHTML = `<i class="fa-regular fa-square"></i> ${I18N.t('actions.select')}`;
  });
  const bar = document.getElementById('folder-selection-bar');
  if (bar) bar.style.display = 'none';
};

window.testFolderFiles = async function (sourceId) { /* Implement */ };
window.testBatchSend = async function (filePaths, slicerPath = null) { /* Implement */ };
window.testBatchPreview = async function (filePaths) { /* Implement */ };

// ============================================
// 🔧 GESTION PAGE RÉPARATION (CORRIGÉ - STABLE)
// ============================================
let repairFilesList = [];
let isRepairScanning = false;
const MAX_FILES_TO_SCAN = 30; // ✅ Limite pour éviter le freeze

document.querySelector('.nav-btn[data-page="repair"]')?.addEventListener('click', () => {
    document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
    document.querySelector('.nav-btn[data-page="repair"]')?.classList.add('active');
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    document.getElementById('page-repair')?.classList.add('active');
    const titleEl = document.getElementById('header-page-title');
    if (titleEl) {
        titleEl.innerHTML = `<i class="fa-solid fa-screwdriver-wrench"></i> ${I18N.t('nav.repair') || 'Réparation'}`;
    }
    loadRepairFiles();
});

async function loadRepairFiles() {
    const grid = document.getElementById('repair-grid');
    const empty = document.getElementById('repair-empty');
    
    // ✅ Affiche le spinner sans bloquer
    grid.innerHTML = `
        <div style="grid-column:1/-1;text-align:center;padding:40px;">
            <i class="fa-solid fa-spinner fa-spin fa-2x"></i>
            <p style="margin-top:12px;color:var(--text-muted);">Chargement des fichiers...</p>
        </div>`;
    empty.classList.add('hidden');
    
    repairFilesList = [];
    isRepairScanning = false;
    
    try {
        const res = await fetch(`${API}/api/files`);
        if (!res.ok) throw new Error(I18N.t('toast.connection_error'));
        const files = await res.json();
        
        // ✅ 1. Récupère uniquement les fichiers DÉJÀ analysés comme non-manifold
        repairFilesList = files.filter(f => 
            f.metadata?.needs_repair === true || 
            f.metadata?.is_manifold === false
        );
        
        // ✅ 2. Stocke les fichiers NON analysés (sans lancer l'analyse auto)
        const unanalyzedFiles = files.filter(f => !f.metadata).slice(0, MAX_FILES_TO_SCAN);
        
        renderRepairFiles(unanalyzedFiles);
        updateRepairBadge();
        
    } catch (err) {
        grid.innerHTML = `<div class="empty-state"><i class="fa-solid fa-triangle-exclamation"></i><p>${err.message}</p></div>`;
    }
}

function renderRepairFiles(unanalyzedFiles = []) {
    const grid = document.getElementById('repair-grid');
    const empty = document.getElementById('repair-empty');
    
    if (repairFilesList.length === 0 && unanalyzedFiles.length === 0) {
        grid.innerHTML = '';
        empty.classList.remove('hidden');
        updateRepairBadge();
        return;
    }
    
    empty.classList.add('hidden');
    
    let html = '';
    
    // ✅ Fichiers déjà détectés comme non-manifold
    repairFilesList.forEach(f => {
        html += `
            <div class="repair-card" data-path="${escapeJs(f.path)}">
                <div class="repair-thumb">
                    ${f.has_thumb ? `<img src="${API}/api/thumb?path=${encodeURIComponent(f.path)}" alt="${escapeHtml(f.name)}">` : `<i class="fa-solid fa-cube"></i>`}
                    <span class="repair-badge-warn">
                        <i class="fa-solid fa-triangle-exclamation"></i> Non-manifold
                    </span>
                </div>
                <div class="repair-info">
                    <div class="repair-name" title="${escapeHtml(f.name)}">${escapeHtml(f.name)}</div>
                    <div class="repair-meta">${formatSize(f.size)} • ${(f.extension || '.stl').toUpperCase()}</div>
                    <button class="btn btn-primary btn-sm repair-btn" onclick="repairFile('${escapeJs(f.path)}', this)">
                        <i class="fa-solid fa-wrench"></i> ${I18N.t('actions.repair') || 'Réparer'}
                    </button>
                </div>
            </div>`;
    });
    
    // ✅ Fichiers non analysés (proposition d'analyse manuelle)
    if (unanalyzedFiles.length > 0 && !isRepairScanning) {
        html += `
            <div class="repair-card" style="grid-column:1/-1;display:flex;flex-direction:column;align-items:center;justify-content:center;padding:30px;border:2px dashed var(--border);background:transparent;">
                <i class="fa-solid fa-magnifying-glass" style="font-size:32px;color:var(--text-muted);margin-bottom:12px;"></i>
                <p style="color:var(--text-secondary);margin-bottom:16px;font-size:14px;">
                    ${unanalyzedFiles.length} fichier(s) non analysé(s)
                </p>
                <button class="btn btn-primary" onclick="scanUnanalyzedFiles()" style="gap:8px;">
                    <i class="fa-solid fa-play"></i> Analyser ces fichiers
                </button>
                <p style="color:var(--text-muted);font-size:12px;margin-top:10px;">
                    Limite à ${MAX_FILES_TO_SCAN} fichiers par session
                </p>
            </div>`;
    }
    
    grid.innerHTML = html;
    updateRepairBadge();
}

async function scanUnanalyzedFiles() {
    if (isRepairScanning) return;
    isRepairScanning = true;
    
    const grid = document.getElementById('repair-grid');
    grid.innerHTML = `
        <div style="grid-column:1/-1;text-align:center;padding:40px;">
            <i class="fa-solid fa-spinner fa-spin fa-2x" style="color:var(--accent);"></i>
            <p style="margin-top:12px;color:var(--text-muted);">Analyse en cours... (peut prendre quelques secondes)</p>
            <p id="repair-progress-text" style="margin-top:8px;color:var(--text-secondary);font-size:12px;">0 fichier(s) analysé(s)</p>
        </div>`;
    
    const res = await fetch(`${API}/api/files`);
    const files = await res.json();
    const unanalyzed = files.filter(f => !f.metadata).slice(0, MAX_FILES_TO_SCAN);
    let analyzed = 0;
    let found = 0;
    
    // ✅ Analyse SÉQUENTIELLE (1 par 1) pour éviter le freeze
    for (const f of unanalyzed) {
        try {
            const analyzeRes = await fetch(`${API}/api/files/analyze`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ path: f.path })
            });
            const data = await analyzeRes.json();
            analyzed++;
            
            // Mise à jour UI toutes les 5 analyses
            if (analyzed % 5 === 0) {
                const progressEl = document.getElementById('repair-progress-text');
                if (progressEl) progressEl.textContent = `${analyzed}/${unanalyzed.length} - ${found} problème(s) détecté(s)`;
            }
            
            if (data.success && data.metadata?.needs_repair) {
                found++;
                repairFilesList.push({ ...f, metadata: data.metadata });
            }
            
            // ✅ Pause entre chaque analyse pour laisser respirer l'UI
            await new Promise(r => setTimeout(r, 100));
            
        } catch (err) {
            console.debug(`[Repair] Erreur analyse ${f.name}:`, err);
        }
    }
    
    isRepairScanning = false;
    renderRepairFiles();
    showToast(`✅ Analyse terminée : ${found} problème(s) détecté(s) sur ${analyzed} fichiers`, 'success');
}

function updateRepairBadge() {
    const badge = document.getElementById('repair-count');
    if (badge) {
        const count = repairFilesList.length;
        badge.textContent = count > 0 ? count : '';
        badge.style.display = count > 0 ? 'inline-block' : 'none';
    }
}

window.repairFile = async function(filePath, btn) {
    const originalHtml = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> ${I18N.t('actions.repairing') || 'Réparation'}...`;
    
    try {
        const res = await fetch(`${API}/api/files/repair`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ path: filePath })
        });
        const data = await res.json();
        
        if (res.ok && data.success) {
            btn.innerHTML = `<i class="fa-solid fa-check"></i> ${I18N.t('actions.repaired') || 'Réparé'}`;
            btn.classList.replace('btn-primary', 'btn-success');
            showToast(data.message || I18N.t('toast.repair_success') || 'Réparé avec succès', 'success');
            
            setTimeout(() => {
                repairFilesList = repairFilesList.filter(f => f.path !== filePath);
                renderRepairFiles();
                loadFiles();
            }, 1200);
        } else {
            btn.innerHTML = originalHtml;
            btn.disabled = false;
            showToast(data.error || I18N.t('toast.repair_failed') || 'Échec', 'error');
        }
    } catch (err) {
        btn.innerHTML = originalHtml;
        btn.disabled = false;
        showToast(I18N.t('toast.connection_error'), 'error');
    }
};

// ============================================
// 🖨️ GESTION & MONITORING DES IMPRIMANTES
// ============================================
window.addPrinter = async function() {
    const name = document.getElementById('printer-name').value.trim();
    const type = document.getElementById('printer-type').value;
    const ip = document.getElementById('printer-ip').value.trim();
    const apiKey = document.getElementById('printer-api-key').value.trim();
    const port = document.getElementById('printer-port').value.trim();
    const bambuCode = document.getElementById('printer-bambu-code').value.trim();
    
    if (!name || !ip || !type) {
        showToast(I18N.t('toast.fill_required') || 'Champs requis manquants', 'warning');
        return;
    }
    
    // Construire la config selon le type
    const config = {};
    if (type === 'klipper' && port) config.port = port;
    if (type === 'bambu') {
        config.code = bambuCode;
        config.user = 'bblp';
    }
    
    const btn = document.querySelector('#modal-add-printer .btn-primary');
    if (btn) {
        btn.disabled = true;
        btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Ajout...';
    }
    
    try {
        const res = await fetch(`${API}/api/printers`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                name,
                type,
                ip,
                api_key: apiKey || null,
                config
            })
        });
        
        const data = await res.json();
        
        if (res.ok) {
            showToast(`✅ ${data.message}`, 'success');
            closeModal('modal-add-printer');
            document.getElementById('add-printer-form').reset();
            loadPrinters(); // Recharge la liste
        } else {
            showToast(`❌ ${data.error || 'Erreur lors de l\'ajout'}`, 'error');
        }
    } catch (err) {
        console.error('[Add Printer]', err);
        showToast(I18N.t('toast.connection_error') || 'Erreur de connexion', 'error');
    } finally {
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = '<i class="fa-solid fa-plus"></i> Ajouter';
        }
    }
};

let printersList = [];
let printerPollingInterval = null;
let printerMonitorInterval = null;
let currentMonitorPid = null;

function loadPrinters() {
    fetch(`${API}/api/printers`)
        .then(res => res.json())
        .then(data => {
            printersList = data;
            renderPrinters();
            if (printerPollingInterval) clearInterval(printerPollingInterval);
            printerPollingInterval = setInterval(refreshAllPrinters, 5000);
        });
}

function formatDuration(seconds) {
    if (!seconds || seconds <= 0) return '—';
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = Math.floor(seconds % 60);
    if (h > 0) return `${h}h ${m.toString().padStart(2,'0')}m ${s.toString().padStart(2,'0')}s`;
    if (m > 0) return `${m}m ${s.toString().padStart(2,'0')}s`;
    return `${s}s`;
}

function renderPrinters() {
    const grid = document.getElementById('printers-grid');
    if (!grid) return;
    if (printersList.length === 0) {
        grid.innerHTML = `<div class="empty-state"><i class="fa-solid fa-print"></i><p>Aucune imprimante connectée</p></div>`;
        return;
    }
    grid.innerHTML = printersList.map(p => `
        <div class="printer-card" data-id="${p.id}" style="cursor:pointer" onclick="openPrinterMonitor(${p.id})">
            <div class="printer-header">
                <i class="mdi ${getPrinterIcon(p.type)}" style="font-size:22px;"></i>
                <span class="printer-name">${escapeHtml(p.name)}</span>
                <span class="printer-status ${p.is_connected ? 'connected' : 'disconnected'}">
                    ${p.is_connected ? 'En ligne' : 'Hors ligne'}
                </span>
            </div>
            <div class="printer-body">
                <p style="font-size: 12px; color: var(--text-muted); margin-bottom:6px;">${p.ip}</p>
                <div style="display:flex; justify-content:space-between; font-size:11px; color:var(--text-muted);">
                    <span id="card-status-${p.id}">—</span>
                    <span id="card-progress-${p.id}">0%</span>
                </div>
                <div class="progress-track" style="margin-top:6px">
                    <div class="progress-bar" id="progress-${p.id}" style="width: 0%;"></div>
                </div>
                <div style="display:flex; gap:10px; margin-top:8px; font-size:11px; color:var(--text-secondary);">
                    <span title="Extrudeur">🔥 <span id="card-ext-${p.id}">--°C</span></span>
                    <span title="Plateau">🛏️ <span id="card-bed-${p.id}">--°C</span></span>
                </div>
            </div>
            <div class="printer-actions" onclick="event.stopPropagation()">
                <button class="btn btn-ghost btn-sm" onclick="openPrinterMonitor(${p.id})" title="Monitoring">
                    <i class="fa-solid fa-chart-line"></i>
                </button>
                <button class="btn btn-ghost btn-sm" onclick="refreshPrinterStatus(${p.id})" title="Rafraîchir">
                    <i class="fa-solid fa-rotate"></i>
                </button>
                <button class="btn btn-ghost btn-sm" style="color:var(--danger)" onclick="deletePrinter(${p.id})" title="Supprimer">
                    <i class="fa-solid fa-trash"></i>
                </button>
            </div>
        </div>
    `).join('');
    refreshAllPrinters();
}

function getPrinterIcon(type) {
    if (type === 'klipper') return 'mdi-printer-3d-nozzle';
    if (type === 'octoprint') return 'mdi-printer-3d-nozzle';
    if (type === 'bambu') return 'mdi-printer-3d-nozzle';
    return 'mdi-printer';
}

function refreshAllPrinters() {
    printersList.forEach(p => {
        fetch(`${API}/api/printers/${p.id}/status`)
            .then(res => res.json())
            .then(data => {
                // Carte simplifiée
                const progressBar = document.getElementById(`progress-${p.id}`);
                const cardStatus = document.getElementById(`card-status-${p.id}`);
                const cardProg = document.getElementById(`card-progress-${p.id}`);
                const cardExt = document.getElementById(`card-ext-${p.id}`);
                const cardBed = document.getElementById(`card-bed-${p.id}`);
                
                if (progressBar) progressBar.style.width = `${data.progress || 0}%`;
                if (cardProg) cardProg.textContent = `${Math.round(data.progress || 0)}%`;
                if (cardStatus) {
                    const statusMap = {
                        printing: '🖨️ Impression', idle: '✅ Prête',
                        paused: '⏸️ Pause', error: '❌ Erreur',
                        offline: '🔌 Hors ligne', timeout: '⏳ Timeout'
                    };
                    cardStatus.textContent = statusMap[data.status] || data.status;
                }
                if (cardExt) cardExt.textContent = `${data.temps?.extruder?.current || 0}°C`;
                if (cardBed) cardBed.textContent = `${data.temps?.bed?.current || 0}°C`;
                
                // Mise à jour du modal si ouvert
                if (currentMonitorPid === p.id) updateMonitorUI(data);
            })
            .catch(() => {});
    });
}

function openPrinterMonitor(pid) {
    const printer = printersList.find(p => p.id === pid);
    if (!printer) return;
    currentMonitorPid = pid;
    
    // Créer le modal s'il n'existe pas
    let modal = document.getElementById('modal-printer-monitor');
    if (!modal) {
        modal = document.createElement('div');
        modal.id = 'modal-printer-monitor';
        modal.className = 'modal hidden';
        modal.innerHTML = `
            <div class="modal-content monitor-modal-content">
                <div class="modal-header">
                    <h3><i class="fa-solid fa-gauge-high"></i> <span id="monitor-title">Monitoring</span></h3>
                    <button class="modal-close" onclick="closePrinterMonitor()">×</button>
                </div>
                <div class="modal-body" id="monitor-body">
                    <div style="text-align:center; padding:40px; color:var(--text-muted)">
                        <i class="fa-solid fa-spinner fa-spin fa-2x"></i>
                        <p style="margin-top:10px">Connexion...</p>
                    </div>
                </div>
            </div>`;
        document.body.appendChild(modal);
        modal.addEventListener('click', (e) => { if (e.target === modal) closePrinterMonitor(); });
    }

    document.getElementById('monitor-title').textContent = `🖨️ ${printer.name}`;
    
    // ✅ CRÉER LA STRUCTURE HTML UNE SEULE FOIS
    initMonitorUI(printer);
    
    openModal('modal-printer-monitor');

    // Rafraîchissement toutes les 2s
    if (printerMonitorInterval) clearInterval(printerMonitorInterval);
    fetchAndUpdateMonitor(pid);
    printerMonitorInterval = setInterval(() => fetchAndUpdateMonitor(pid), 2000);
}

// ✅ Crée la structure HTML du monitoring UNE SEULE FOIS
function initMonitorUI(printer) {
    const body = document.getElementById('monitor-body');
    if (!body) return;
    
    // 🔵 Bouton Klipper (lien vers Fluidd/Mainsail)
    const klipperUrl = printer ? `http://${printer.ip}` : '#';
    const klipperBtn = printer && printer.type === 'klipper' ? `
        <a href="${klipperUrl}" target="_blank" class="btn btn-sm" 
           style="background:var(--accent); color:white; text-decoration:none; display:inline-flex; align-items:center; gap:6px;">
            <i class="fa-solid fa-external-link-alt"></i> Klipper
        </a>
    ` : '';
    
    // 🟠 Bouton OctoPrint (lien vers l'interface OctoPrint)
    const octoprintUrl = printer ? `http://${printer.ip}` : '#';
    const octoprintBtn = printer && printer.type === 'octoprint' ? `
        <a href="${octoprintUrl}" target="_blank" class="btn btn-sm" 
           style="background:var(--accent); color:white; text-decoration:none; display:inline-flex; align-items:center; gap:6px;">
            <i class="fa-solid fa-external-link-alt"></i> OctoPrint
        </a>
    ` : '';
    
    body.innerHTML = `
        <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:16px;">
            <span id="monitor-status-badge" class="monitor-status-badge idle">
                <span id="monitor-live-dot" class="live-dot" style="display:none;"></span>
                <span id="monitor-status-label">Connexion...</span>
            </span>
            <div style="display:flex; gap:8px; align-items:center;">
                ${klipperBtn}
                ${octoprintBtn}
            </div>
        </div>
        
        <!-- Caméra (structure fixe, le contenu sera injecté dynamiquement) -->
        <div id="printer-camera-container" class="monitor-card full" style="display:none;">
            <h4><i class="fa-solid fa-camera"></i> Caméra</h4>
            <div id="camera-content" style="position:relative; width:100%; min-height:200px; background:#000; border-radius:8px; overflow:hidden; display:flex; align-items:center; justify-content:center;">
                <div style="color:var(--text-muted);"><i class="fa-solid fa-spinner fa-spin"></i> Chargement...</div>
            </div>
        </div>
        
        <div class="monitor-grid">
            <!-- Températures -->
            <div class="monitor-card">
                <h4><i class="fa-solid fa-temperature-half"></i> Températures</h4>
                <div id="monitor-temps-container"></div>
            </div>
            
            <!-- Temps -->
            <div class="monitor-card">
                <h4><i class="fa-solid fa-clock"></i> Progression</h4>
                <div class="monitor-progress-bar">
                    <div id="monitor-progress-fill" class="monitor-progress-fill" style="width: 0%"></div>
                </div>
                <div id="monitor-progress-pct" class="time-big">0%</div>
                <div class="stat-row">
                    <span class="stat-label">⏱️ Écoulé</span>
                    <span id="monitor-time-elapsed" class="stat-value">—</span>
                </div>
                <div class="stat-row">
                    <span class="stat-label">⏳ Restant</span>
                    <span id="monitor-time-remaining" class="stat-value">—</span>
                </div>
                <div class="stat-row">
                    <span class="stat-label">📊 Total estimé</span>
                    <span id="monitor-time-total" class="stat-value">—</span>
                </div>
            </div>
            
            <!-- Dernière impression -->
            <div class="monitor-card full">
                <h4><i class="fa-solid fa-history"></i> Dernière impression</h4>
                <div id="monitor-last-print-container">
                    <p style="color:var(--text-muted); font-size:13px">Chargement...</p>
                </div>
            </div>
        </div>
    `;
    
    // ✅ Charger la caméra UNE SEULE FOIS
    loadPrinterCamera(currentMonitorPid);
}

function fetchAndUpdateMonitor(pid) {
    fetch(`${API}/api/printers/${pid}/status`)
        .then(res => res.json())
        .then(data => updateMonitorUI(data))
        .catch(() => {});
}

// ✅ Met à jour UNIQUEMENT les données dynamiques (sans recréer le HTML)
function updateMonitorUI(data) {
    const body = document.getElementById('monitor-body');
    if (!body) return;
    
    // Statut
    const statusClass = ['printing','idle','paused','error','offline','timeout'].includes(data.status) ? data.status : 'idle';
    const statusLabel = {
        printing: 'En cours d\'impression', idle: 'Prête',
        paused: 'En pause', complete: 'Terminée',
        error: 'Erreur', offline: 'Hors ligne', timeout: 'Délai dépassé',
        unknown: 'Inconnu'
    }[data.status] || data.status;

    const isPrinting = data.status === 'printing' || data.status === 'paused';
    
    // Badge statut
    const badge = document.getElementById('monitor-status-badge');
    if (badge) {
        badge.className = `monitor-status-badge ${statusClass}`;
    }
    
    const liveDot = document.getElementById('monitor-live-dot');
    if (liveDot) {
        liveDot.style.display = isPrinting ? 'inline-block' : 'none';
    }
    
    const statusLbl = document.getElementById('monitor-status-label');
    if (statusLbl) statusLbl.textContent = statusLabel;
    
    
    // Températures
    const tempsContainer = document.getElementById('monitor-temps-container');
    if (tempsContainer) {
        let tempsHtml = renderTempRow('Extrudeur', data.temps?.extruder);
        tempsHtml += renderTempRow('Plateau', data.temps?.bed);
        if (data.temps?.chamber?.current > 0) {
            tempsHtml += renderTempRow('Chambre', data.temps?.chamber);
        }
        tempsContainer.innerHTML = tempsHtml;
    }
    
    // Progression
    const progressFill = document.getElementById('monitor-progress-fill');
    if (progressFill) progressFill.style.width = `${data.progress || 0}%`;
    
    const progressPct = document.getElementById('monitor-progress-pct');
    if (progressPct) progressPct.textContent = `${Math.round(data.progress || 0)}%`;
    
    // Temps
    const elapsedEl = document.getElementById('monitor-time-elapsed');
    if (elapsedEl) elapsedEl.textContent = formatDuration(data.time?.elapsed);
    
    const remainingEl = document.getElementById('monitor-time-remaining');
    if (remainingEl) remainingEl.textContent = formatDuration(data.time?.remaining);
    
    const totalEl = document.getElementById('monitor-time-total');
    if (totalEl) totalEl.textContent = formatDuration(data.time?.total);
    
    // Dernière impression
    const lastPrintContainer = document.getElementById('monitor-last-print-container');
    if (lastPrintContainer && data.last_print) {
        if (data.last_print.filename) {
            let lpHtml = `
                <div class="stat-row">
                    <span class="stat-label">Fichier</span>
                    <span class="stat-value" style="font-size:12px">${escapeHtml(data.last_print.filename)}</span>
                </div>
                <div class="stat-row">
                    <span class="stat-label">Durée</span>
                    <span class="stat-value">${formatDuration(data.last_print.duration)}</span>
                </div>
            `;
            if (data.last_print.finished_at) {
                lpHtml += `
                    <div class="stat-row">
                        <span class="stat-label">Terminée le</span>
                        <span class="stat-value" style="font-size:12px">${new Date(data.last_print.finished_at * 1000).toLocaleString('fr-FR')}</span>
                    </div>
                `;
            }
            lastPrintContainer.innerHTML = lpHtml;
        } else {
            lastPrintContainer.innerHTML = '<p style="color:var(--text-muted); font-size:13px">Aucune impression récente</p>';
        }
    }
    
    // ✅ NE PAS recharger la caméra ici ! Elle est déjà chargée par initMonitorUI()
}

// 🎥 Fonction pour charger et afficher la caméra
// 🎥 Fonction pour charger et afficher la caméra (UNE SEULE FOIS)
let cameraLoadedForPid = null; // Mémorise l'ID de l'imprimante dont la caméra est chargée

async function loadPrinterCamera(pid) {
    // ✅ Si la caméra est déjà chargée pour cette imprimante, on ne fait rien
    if (cameraLoadedForPid === pid) return;
    
    const container = document.getElementById('printer-camera-container');
    const content = document.getElementById('camera-content');
    if (!container || !content) return;
    
    try {
        const res = await fetch(`${API}/api/printers/${pid}/camera`);
        if (!res.ok) {
            container.style.display = 'none';
            return;
        }
        
        const camData = await res.json();
        
        if (!camData.available) {
            container.style.display = 'none';
            cameraLoadedForPid = null;
            return;
        }
        
        // ✅ Marquer comme chargée
        cameraLoadedForPid = pid;
        
        // Afficher le conteneur
        container.style.display = 'block';
        
        const streamUrl = camData.stream_url || '';
        const snapshotUrl = camData.snapshot_url || '';
        
        // Si on a un stream MJPEG, l'utiliser directement
        if (streamUrl && streamUrl.includes('action=stream')) {
            content.innerHTML = `
                <img src="${streamUrl}" 
                    alt="${camData.name || 'Camera'}" 
                    style="width:100%; height:auto; max-height:400px; object-fit:contain; display:block;"
                    onerror="this.parentElement.innerHTML='<div style=\\'color:var(--danger);padding:20px;text-align:center;\\'>❌ Flux caméra indisponible</div>'">
            `;
        } 
        // Sinon, utiliser des snapshots rafraîchis
        else if (snapshotUrl) {
            const refreshSnapshot = () => {
                const img = content.querySelector('#camera-snapshot');
                if (img) {
                    img.src = snapshotUrl + (snapshotUrl.includes('?') ? '&' : '?') + '_t=' + Date.now();
                }
            };
            
            content.innerHTML = `
                <img id="camera-snapshot" 
                    src="${snapshotUrl}?_t=${Date.now()}" 
                    alt="${camData.name || 'Camera'}" 
                    style="width:100%; height:auto; max-height:400px; object-fit:contain; display:block;"
                    onerror="this.parentElement.innerHTML='<div style=\\'color:var(--danger);padding:20px;text-align:center;\\'>❌ Snapshot caméra indisponible</div>'">
            `;
            
            // Rafraîchir le snapshot toutes les 2 secondes
            if (window.cameraRefreshInterval) clearInterval(window.cameraRefreshInterval);
            window.cameraRefreshInterval = setInterval(refreshSnapshot, 2000);
        } 
        else {
            content.innerHTML = `
                <div style="color:var(--text-muted); padding:20px; text-align:center;">
                    <i class="fa-solid fa-video-slash" style="font-size:32px; margin-bottom:10px;"></i>
                    <p>Aucun flux vidéo configuré</p>
                </div>
            `;
        }
        
    } catch (err) {
        console.error('[Camera] Erreur:', err);
        container.style.display = 'none';
        cameraLoadedForPid = null;
    }
}

function closePrinterMonitor() {
    closeModal('modal-printer-monitor');
    if (printerMonitorInterval) {
        clearInterval(printerMonitorInterval);
        printerMonitorInterval = null;
    }
    if (window.cameraRefreshInterval) {
        clearInterval(window.cameraRefreshInterval);
        window.cameraRefreshInterval = null;
    }
    // ✅ Réinitialiser pour que la caméra se recharge la prochaine fois
    cameraLoadedForPid = null;
    currentMonitorPid = null;
}

function renderTempRow(label, data) {
    if (!data) return '';
    const current = data.current || 0;
    const target = data.target || 0;
    const isHeating = target > 0 && current < target - 2;
    const color = isHeating ? 'var(--warning)' : (current > 0 ? 'var(--accent)' : 'var(--text-muted)');
    
    return `
        <div class="temp-row">
            <span class="temp-label">${label}</span>
            <span class="temp-values">
                <span class="temp-current" style="color:${color}">${current}°C</span>
                <span class="temp-target">/ ${target}°C</span>
            </span>
        </div>
    `;
}

function refreshPrinterStatus(pid) {
    fetchAndUpdateMonitor(pid);
    showToast("Statut mis à jour", "info");
}

function deletePrinter(pid) {
    showConfirmModal(I18N.t('toast.delete_printer') || 'Supprimer cette imprimante ?', async () => {
        try {
            const res = await fetch(`${API}/api/printers/${pid}`, { method: 'DELETE' });
            if (res.ok) {
                showToast(I18N.t('toast.printer_deleted') || 'Imprimante supprimée', 'success');
                loadPrinters();
            } else {
                const data = await res.json();
                showToast(data.error || I18N.t('toast.error'), 'error');
            }
        } catch (err) {
            showToast(I18N.t('toast.connection_error'), 'error');
            console.error('[Delete Printer]', err);
        }
    });
}

window.openAddPrinterModal = function() {
    document.getElementById('add-printer-form').reset();
    togglePrinterFields();
    openModal('modal-add-printer');
}

window.togglePrinterFields = function() {
    const type = document.getElementById('printer-type').value;
    document.getElementById('group-api-key').style.display = type === 'octoprint' ? 'block' : 'none';
    document.getElementById('group-port').style.display = type === 'klipper' ? 'block' : 'none';
    document.getElementById('group-bambu').style.display = type === 'bambu' ? 'block' : 'none';
}
// ============================================
// 🔄 GESTION DES MISES À JOUR AUTOMATIQUES
// ============================================

const UpdateManager = {
    lastCheck: 0,
    checkInterval: 6 * 60 * 60 * 1000, // 6 heures
    currentVersion: '1.0.0',
    
    async init() {
        console.log('[UpdateManager] 🔄 Initialisation...');
        
        // Récupérer la version actuelle depuis le backend
        try {
            const res = await fetch(`${API}/api/update/version`);
            if (res.ok) {
                const data = await res.json();
                this.currentVersion = data.version;
                console.log(`[UpdateManager] Version actuelle: ${this.currentVersion}`);
            }
        } catch (e) {
            console.warn('[UpdateManager] Impossible de récupérer la version');
        }
        
        // Vérifier si on doit afficher le changelog (après une MAJ)
        await this.checkAndShowChangelog();
        
        // Vérifier les mises à jour après 5 secondes
        setTimeout(() => this.checkForUpdates(true), 5000);
        
        // Vérification périodique toutes les 6 heures
        setInterval(() => this.checkForUpdates(false), this.checkInterval);
    },
    
    async checkAndShowChangelog() {
        try {
            // Récupérer la dernière version vue
            const lastSeenVersion = localStorage.getItem('stellio-last-seen-version');
            
            // Récupérer la version actuelle depuis GitHub
            const response = await fetch('https://api.github.com/repos/stellio-app/stellio-app/releases/latest');
            if (!response.ok) return;
            
            const release = await response.json();
            const latestVersion = release.tag_name.replace('v', '');
            
            // Si c'est une nouvelle version (mise à jour effectuée)
            if (lastSeenVersion && lastSeenVersion !== latestVersion && latestVersion === this.currentVersion) {
                console.log(`[UpdateManager] 🎉 Mise à jour détectée: ${lastSeenVersion} → ${latestVersion}`);
                this.showChangelogModal(release);
            }
            
            // Mettre à jour la dernière version vue
            localStorage.setItem('stellio-last-seen-version', latestVersion);
            
        } catch (e) {
            console.warn('[UpdateManager] Erreur check changelog:', e);
        }
    },
    
	async checkForUpdates(showModal = true) {
		try {
			console.log('[UpdateManager] 🔍 Vérification des mises à jour...');
			
			const res = await fetch(`${API}/api/update/check`);
			if (!res.ok) {
				console.warn('[UpdateManager] Impossible de vérifier');
				return;
			}
			
			const data = await res.json();
			console.log('[UpdateManager] Réponse:', data);
			
			if (data.update_available) {
				console.log(`[UpdateManager] ✅ Nouvelle version: ${data.version}`);
				
				if (showModal) {
					this.showUpdateModal(data);
				} else {
					this.showUpdateToast(data);
				}
			} else {
				console.log('[UpdateManager] ✅ Application à jour');
			}
			
		} catch (err) {
			console.error('[UpdateManager] Erreur:', err);
		}
	},
    
	showUpdateModal(updateInfo) {
		const overlay = document.createElement('div');
		overlay.className = 'modal-overlay update-modal-overlay';
		overlay.style.cssText = `
			position: fixed; top: 0; left: 0; right: 0; bottom: 0;
			background: rgba(0, 0, 0, 0.75); display: flex;
			align-items: center; justify-content: center; z-index: 100000;
			backdrop-filter: blur(5px); animation: fadeIn 0.3s ease;
		`;
		
		const modal = document.createElement('div');
		modal.style.cssText = `
			background: var(--bg-secondary, #1e2129); border-radius: 16px;
			padding: 32px; max-width: 600px; width: 90%; max-height: 85vh;
			overflow-y: auto; box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
			border: 1px solid var(--border, #2a2f3a); animation: slideIn 0.3s ease;
		`;
		
		const releaseNotes = this.parseMarkdown(updateInfo.release_notes || 'Corrections de bugs et améliorations.');
		
		// ✅ Boutons différents selon si un installateur est disponible
		const hasInstaller = !!updateInfo.download_url;
		const releaseUrl = updateInfo.release_url || `https://github.com/stellio-app/stellio-app/releases/latest`;
		
		modal.innerHTML = `
			<div style="display: flex; align-items: center; gap: 16px; margin-bottom: 24px;">
				<div style="width: 56px; height: 56px; background: linear-gradient(135deg, var(--accent, #4ea1d3), #00d9ff); border-radius: 12px; display: flex; align-items: center; justify-content: center;">
					<i class="fa-solid fa-download" style="font-size: 28px; color: white;"></i>
				</div>
				<div style="flex: 1;">
					<h3 style="margin: 0; color: var(--text-primary, #e6e6e6); font-size: 22px; font-weight: 700;">
						Mise à jour disponible
					</h3>
					<p style="margin: 4px 0 0 0; color: var(--text-muted, #9ca3af); font-size: 14px;">
						Version ${updateInfo.current_version} → <strong style="color: var(--accent, #4ea1d3);">${updateInfo.version}</strong>
					</p>
				</div>
			</div>
			
			<div style="background: var(--bg-primary, #15181e); padding: 20px; border-radius: 12px; margin-bottom: 24px; max-height: 300px; overflow-y: auto; border: 1px solid var(--border, #2a2f3a);">
				<h4 style="margin: 0 0 12px 0; color: var(--accent, #4ea1d3); font-size: 14px; text-transform: uppercase; letter-spacing: 1px;">
					<i class="fa-solid fa-list-check"></i> Notes de version
				</h4>
				<div style="color: var(--text-secondary, #b0b3b8); font-size: 14px; line-height: 1.7;" class="release-notes-content">
					${releaseNotes}
				</div>
			</div>
			
			<div id="update-progress-container" style="display: none; margin-bottom: 24px; padding: 16px; background: var(--bg-primary, #15181e); border-radius: 12px; border: 1px solid var(--border, #2a2f3a);">
				<div style="display: flex; justify-content: space-between; margin-bottom: 10px; align-items: center;">
					<span style="color: var(--text-secondary, #b0b3b8); font-size: 13px; font-weight: 500;">
						<i class="fa-solid fa-download"></i> Téléchargement...
					</span>
					<span id="update-percent" style="color: var(--accent, #4ea1d3); font-size: 14px; font-weight: 700;">0%</span>
				</div>
				<div style="height: 8px; background: var(--bg-tertiary, #2a2f3a); border-radius: 4px; overflow: hidden;">
					<div id="update-bar" style="height: 100%; background: linear-gradient(90deg, var(--accent, #4ea1d3), #00d9ff); width: 0%; transition: width 0.3s ease; border-radius: 4px;"></div>
				</div>
			</div>
			
			<div style="display: flex; gap: 12px; justify-content: flex-end; flex-wrap: wrap;">
				${!hasInstaller ? `
					<a href="${releaseUrl}" target="_blank" style="
						padding: 12px 24px; border: none; border-radius: 10px;
						background: linear-gradient(135deg, var(--accent, #4ea1d3), #3d8fb8);
						color: white; cursor: pointer; font-weight: 600; font-size: 14px;
						box-shadow: 0 4px 12px rgba(78, 161, 211, 0.3);
						text-decoration: none; display: inline-flex; align-items: center; gap: 8px;
					">
						<i class="fa-solid fa-external-link-alt"></i> Télécharger sur GitHub
					</a>
				` : ''}
				<button id="update-later-btn" style="
					padding: 12px 24px; border: 1px solid var(--border, #363c4a); border-radius: 10px;
					background: var(--bg-tertiary, #2a2f3a); color: var(--text-primary, #e6e6e6);
					cursor: pointer; font-weight: 500; font-size: 14px;
				">
					Plus tard
				</button>
				${hasInstaller ? `
					<button id="update-now-btn" style="
						padding: 12px 28px; border: none; border-radius: 10px;
						background: linear-gradient(135deg, var(--accent, #4ea1d3), #3d8fb8);
						color: white; cursor: pointer; font-weight: 600; font-size: 14px;
						box-shadow: 0 4px 12px rgba(78, 161, 211, 0.3);
					">
						<i class="fa-solid fa-download"></i> Mettre à jour
					</button>
				` : ''}
			</div>
		`;
		
		overlay.appendChild(modal);
		document.body.appendChild(overlay);
		
		document.getElementById('update-later-btn').addEventListener('click', () => {
			overlay.style.animation = 'fadeOut 0.3s ease';
			setTimeout(() => overlay.remove(), 300);
		});
		
		if (hasInstaller) {
			document.getElementById('update-now-btn').addEventListener('click', async () => {
				const btn = document.getElementById('update-now-btn');
				btn.disabled = true;
				btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Préparation...';
				
				document.getElementById('update-progress-container').style.display = 'block';
				
				try {
					const downloadRes = await fetch(`${API}/api/update/download`, {
						method: 'POST',
						headers: { 'Content-Type': 'application/json' },
						body: JSON.stringify({ download_url: updateInfo.download_url })
					});
					
					const downloadData = await downloadRes.json();
					
					if (downloadData.success) {
						btn.innerHTML = '<i class="fa-solid fa-check"></i> Installation...';
						document.getElementById('update-percent').textContent = '100%';
						document.getElementById('update-bar').style.width = '100%';
						
						setTimeout(async () => {
							const installRes = await fetch(`${API}/api/update/install`, {
								method: 'POST',
								headers: { 'Content-Type': 'application/json' },
								body: JSON.stringify({ installer_path: downloadData.installer_path })
							});
							
							if (installRes.ok) {
								btn.innerHTML = '<i class="fa-solid fa-rotate"></i> Redémarrage...';
								showToast('Mise à jour en cours... L\'application va redémarrer', 'success');
							}
						}, 1000);
					} else {
						showToast('Erreur lors du téléchargement', 'error');
						btn.disabled = false;
						btn.innerHTML = '<i class="fa-solid fa-download"></i> Réessayer';
						document.getElementById('update-progress-container').style.display = 'none';
					}
				} catch (err) {
					showToast('Erreur de connexion', 'error');
					btn.disabled = false;
					btn.innerHTML = '<i class="fa-solid fa-download"></i> Réessayer';
					document.getElementById('update-progress-container').style.display = 'none';
				}
			});
		}
		
		overlay.addEventListener('click', (e) => {
			if (e.target === overlay) {
				overlay.style.animation = 'fadeOut 0.3s ease';
				setTimeout(() => overlay.remove(), 300);
			}
		});
	},
    
    showUpdateToast(updateInfo) {
        const toast = document.createElement('div');
        toast.className = 'toast info';
        toast.style.cssText = `
            position: fixed; bottom: 24px; right: 24px;
            background: var(--bg-secondary, #1e2129); border: 1px solid var(--accent, #4ea1d3);
            padding: 16px 20px; border-radius: 12px;
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
            cursor: pointer; z-index: 9999;
            animation: slideInRight 0.3s ease;
            max-width: 350px;
        `;
        
        toast.innerHTML = `
            <div style="display: flex; align-items: center; gap: 12px;">
                <div style="width: 40px; height: 40px; background: linear-gradient(135deg, var(--accent, #4ea1d3), #00d9ff); border-radius: 8px; display: flex; align-items: center; justify-content: center; flex-shrink: 0;">
                    <i class="fa-solid fa-download" style="font-size: 18px; color: white;"></i>
                </div>
                <div style="flex: 1; min-width: 0;">
                    <div style="font-weight: 600; color: var(--text-primary, #e6e6e6); font-size: 14px;">
                        Mise à jour disponible
                    </div>
                    <div style="font-size: 12px; color: var(--text-muted, #9ca3af); margin-top: 2px;">
                        Version ${updateInfo.version} • Cliquez pour installer
                    </div>
                </div>
            </div>
        `;
        
        toast.addEventListener('click', () => {
            toast.remove();
            this.showUpdateModal(updateInfo);
        });
        
        document.body.appendChild(toast);
        
        // Auto-hide après 15 secondes
        setTimeout(() => {
            if (toast.parentNode) {
                toast.style.animation = 'slideOutRight 0.3s ease';
                setTimeout(() => toast.remove(), 300);
            }
        }, 15000);
    },
    
    showChangelogModal(release) {
        const overlay = document.createElement('div');
        overlay.className = 'modal-overlay changelog-modal-overlay';
        overlay.style.cssText = `
            position: fixed; top: 0; left: 0; right: 0; bottom: 0;
            background: rgba(0, 0, 0, 0.75); display: flex;
            align-items: center; justify-content: center; z-index: 100000;
            backdrop-filter: blur(5px); animation: fadeIn 0.3s ease;
        `;
        
        const modal = document.createElement('div');
        modal.style.cssText = `
            background: var(--bg-secondary, #1e2129); border-radius: 16px;
            padding: 32px; max-width: 650px; width: 90%; max-height: 85vh;
            overflow-y: auto; box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
            border: 1px solid var(--border, #2a2f3a); animation: slideIn 0.3s ease;
        `;
        
        const version = release.tag_name || this.currentVersion;
        const changelog = this.parseMarkdown(release.body || 'Corrections de bugs et améliorations.');
        const publishedDate = new Date(release.published_at).toLocaleDateString('fr-FR', {
            year: 'numeric', month: 'long', day: 'numeric'
        });
        
        modal.innerHTML = `
            <div style="text-align: center; margin-bottom: 28px;">
                <div style="display: inline-flex; align-items: center; justify-content: center; width: 72px; height: 72px; background: linear-gradient(135deg, #10b981, #059669); border-radius: 50%; margin-bottom: 16px; box-shadow: 0 8px 24px rgba(16, 185, 129, 0.3);">
                    <i class="fa-solid fa-party-horn" style="font-size: 32px; color: white;"></i>
                </div>
                <h2 style="margin: 0 0 8px 0; color: var(--text-primary, #e6e6e6); font-size: 26px; font-weight: 700;">
                    🎉 Stellio a été mis à jour !
                </h2>
                <p style="margin: 0; color: var(--text-muted, #9ca3af); font-size: 15px;">
                    Version <strong style="color: #10b981;">${version}</strong> • ${publishedDate}
                </p>
            </div>
            
            <div style="background: var(--bg-primary, #15181e); padding: 24px; border-radius: 12px; margin-bottom: 24px; border: 1px solid var(--border, #2a2f3a);">
                <h3 style="margin: 0 0 16px 0; color: var(--accent, #4ea1d3); font-size: 16px; text-transform: uppercase; letter-spacing: 1px; display: flex; align-items: center; gap: 8px;">
                    <i class="fa-solid fa-sparkles"></i> Quoi de neuf ?
                </h3>
                <div style="color: var(--text-secondary, #b0b3b8); font-size: 14px; line-height: 1.8;" class="changelog-content">
                    ${changelog}
                </div>
            </div>
            
            <div style="text-align: center;">
                <button id="changelog-close-btn" style="
                    padding: 14px 32px; border: none; border-radius: 10px;
                    background: linear-gradient(135deg, #10b981, #059669);
                    color: white; cursor: pointer; font-weight: 600; font-size: 15px;
                    box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
                ">
                    <i class="fa-solid fa-thumbs-up"></i> C'est parti !
                </button>
            </div>
        `;
        
        overlay.appendChild(modal);
        document.body.appendChild(overlay);
        
        document.getElementById('changelog-close-btn').addEventListener('click', () => {
            overlay.style.animation = 'fadeOut 0.3s ease';
            setTimeout(() => overlay.remove(), 300);
        });
        
        overlay.addEventListener('click', (e) => {
            if (e.target === overlay) {
                overlay.style.animation = 'fadeOut 0.3s ease';
                setTimeout(() => overlay.remove(), 300);
            }
        });
    },
    
    parseMarkdown(text) {
        // Parser markdown basique
        return text
            .replace(/^### (.*$)/gim, '<h4 style="color: var(--accent, #4ea1d3); margin: 16px 0 8px 0; font-size: 15px;">$1</h4>')
            .replace(/^## (.*$)/gim, '<h3 style="color: var(--accent, #4ea1d3); margin: 20px 0 10px 0; font-size: 17px;">$1</h3>')
            .replace(/^# (.*$)/gim, '<h2 style="color: var(--accent, #4ea1d3); margin: 24px 0 12px 0; font-size: 19px;">$1</h2>')
            .replace(/^\- (.*$)/gim, '<div style="display: flex; align-items: flex-start; gap: 8px; margin: 6px 0;"><span style="color: #10b981; flex-shrink: 0;">✓</span><span>$1</span></div>')
            .replace(/^\* (.*$)/gim, '<div style="display: flex; align-items: flex-start; gap: 8px; margin: 6px 0;"><span style="color: #10b981; flex-shrink: 0;">✓</span><span>$1</span></div>')
            .replace(/\*\*(.*?)\*\*/g, '<strong style="color: var(--text-primary, #e6e6e6);">$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/`(.*?)`/g, '<code style="background: var(--bg-tertiary, #2a2f3a); padding: 2px 6px; border-radius: 4px; font-family: monospace; font-size: 13px;">$1</code>')
            .replace(/\n\n/g, '<br><br>')
            .replace(/\n/g, '<br>');
    }
};

// Initialiser le gestionnaire de mises à jour au chargement
document.addEventListener('DOMContentLoaded', () => {
    setTimeout(() => UpdateManager.init(), 2000);
});

// Ajouter les animations CSS
if (!document.getElementById('update-animations')) {
    const style = document.createElement('style');
    style.id = 'update-animations';
    style.textContent = `
        @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
        @keyframes fadeOut { from { opacity: 1; } to { opacity: 0; } }
        @keyframes slideIn { from { transform: translateY(-20px); opacity: 0; } to { transform: translateY(0); opacity: 1; } }
        @keyframes slideInRight { from { transform: translateX(400px); opacity: 0; } to { transform: translateX(0); opacity: 1; } }
        @keyframes slideOutRight { from { transform: translateX(0); opacity: 1; } to { transform: translateX(400px); opacity: 0; } }
    `;
    document.head.appendChild(style);
}

// ============================================
// 🚪 CONFIRMATION DE FERMETURE (STYLE STELLIO)
// ============================================
window.showQuitConfirmation = function() {
    // Sauvegarder le cache immédiatement
    fetch(`${API}/api/app/save-cache`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({}),
        keepalive: true
    }).catch(() => {});
    
    // Créer l'overlay
    const overlay = document.createElement('div');
    overlay.id = 'quit-confirmation-overlay';
    overlay.style.cssText = `
        position: fixed; top: 0; left: 0; right: 0; bottom: 0;
        background: rgba(0, 0, 0, 0.75);
        backdrop-filter: blur(5px);
        display: flex; align-items: center; justify-content: center;
        z-index: 999999;
        animation: fadeIn 0.2s ease;
    `;
    
    // Créer le modal
    const modal = document.createElement('div');
    modal.style.cssText = `
        background: var(--bg-secondary, #22262e);
        border: 1px solid var(--border, #363c4a);
        border-radius: 16px;
        padding: 32px;
        max-width: 420px;
        width: 90%;
        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
        text-align: center;
        animation: slideUp 0.3s ease;
    `;
    
    modal.innerHTML = `
        <div style="margin-bottom: 20px;">
            <div style="width: 64px; height: 64px; background: linear-gradient(135deg, var(--accent, #4ea1d3), #3d8fb8); border-radius: 50%; display: flex; align-items: center; justify-content: center; margin: 0 auto 16px auto; box-shadow: 0 8px 24px rgba(78, 161, 211, 0.3);">
                <i class="fa-solid fa-power-off" style="font-size: 28px; color: white;"></i>
            </div>
            <h3 style="margin: 0 0 8px 0; color: var(--text-primary, #e8e9eb); font-size: 20px; font-weight: 600;">
                ${I18N.t('app.quit_title') || 'Quitter Stellio'}
            </h3>
            <p style="margin: 0 0 24px 0; color: var(--text-secondary, #9ca0ab); font-size: 14px; line-height: 1.5;">
                ${I18N.t('app.quit_message') || 'Voulez-vous vraiment quitter l\'application ?'}
            </p>
        </div>
        
        <div style="display: flex; gap: 12px; justify-content: center;">
            <button id="quit-cancel-btn" style="
                padding: 12px 28px;
                border: 1px solid var(--border, #363c4a);
                border-radius: 8px;
                background: var(--bg-tertiary, #2a2e38);
                color: var(--text-primary, #e8e9eb);
                cursor: pointer;
                font-weight: 500;
                font-size: 14px;
                transition: all 0.2s;
            ">${I18N.t('actions.cancel') || 'Annuler'}</button>
            <button id="quit-confirm-btn" style="
                padding: 12px 28px;
                border: none;
                border-radius: 8px;
                background: linear-gradient(135deg, var(--danger, #f87171), #ef4444);
                color: white;
                cursor: pointer;
                font-weight: 600;
                font-size: 14px;
                box-shadow: 0 4px 12px rgba(248, 113, 113, 0.3);
                transition: all 0.2s;
                display: flex; align-items: center; gap: 6px;
            "><i class="fa-solid fa-power-off"></i>${I18N.t('actions.quit') || 'Quitter'}</button>
        </div>
    `;
    
    overlay.appendChild(modal);
    document.body.appendChild(overlay);
    
    // Gestionnaires d'événements
    document.getElementById('quit-cancel-btn').addEventListener('click', () => {
        overlay.style.animation = 'fadeOut 0.2s ease';
        setTimeout(() => overlay.remove(), 200);
    });
    
    document.getElementById('quit-confirm-btn').addEventListener('click', () => {
        const btn = document.getElementById('quit-confirm-btn');
        btn.disabled = true;
        btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Fermeture...';
        
        // Appeler l'API pour fermer proprement
        fetch(`${API}/api/app/quit`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({}),
            keepalive: true
        }).catch(() => {});
        
        // Fallback : fermer la fenêtre après 2s
        setTimeout(() => {
            window.close();
        }, 2000);
    });
    
    // Fermer en cliquant à l'extérieur = annuler
    overlay.addEventListener('click', (e) => {
        if (e.target === overlay) {
            overlay.style.animation = 'fadeOut 0.2s ease';
            setTimeout(() => overlay.remove(), 200);
        }
    });
    
    // Fermer avec Echap = annuler
    const escHandler = (e) => {
        if (e.key === 'Escape') {
            overlay.style.animation = 'fadeOut 0.2s ease';
            setTimeout(() => overlay.remove(), 200);
            document.removeEventListener('keydown', escHandler);
        }
    };
    document.addEventListener('keydown', escHandler);
};

// ============================================
// 💾 SAUVEGARDE CACHE AVANT FERMETURE NAVIGATEUR
// ============================================
window.addEventListener('beforeunload', () => {
    try {
        navigator.sendBeacon(`${API}/api/app/save-cache`, JSON.stringify({}));
    } catch (err) {}
});

// ============================================
// 🔍 DÉTECTION AUTOMATIQUE D'URL POUR ASTUCES
// ============================================
document.getElementById('download-url')?.addEventListener('input', (e) => {
    const url = e.target.value.trim();
    
    // Masquer toutes les astuces
    ['telegram', 'cults', 'thingiverse', 'printables', 'makerworld'].forEach(p => {
        const el = document.getElementById(`astuces-${p}`);
        if (el) el.style.display = 'none';
        const icon = document.getElementById(`${p}-astuces-icon`);
        if (icon) {
            icon.classList.remove('fa-chevron-down');
            icon.classList.add('fa-chevron-right');
        }
    });
    
    // Afficher l'astuce correspondante automatiquement
    let matchedPlatform = null;
    if (url.includes('t.me/') || url.includes('telegram.me/')) {
        matchedPlatform = 'telegram';
    } else if (url.includes('cults3d.com')) {
        matchedPlatform = 'cults';
    } else if (url.includes('thingiverse.com')) {
        matchedPlatform = 'thingiverse';
    } else if (url.includes('printables.com')) {
        matchedPlatform = 'printables';
    } else if (url.includes('makerworld.com')) {
        matchedPlatform = 'makerworld';
    }
    
    if (matchedPlatform) {
        const submenu = document.getElementById(`astuces-${matchedPlatform}`);
        const icon = document.getElementById(`${matchedPlatform}-astuces-icon`);
        if (submenu) {
            submenu.style.display = 'block';
            if (icon) {
                icon.classList.remove('fa-chevron-right');
                icon.classList.add('fa-chevron-down');
            }
        }
        // Ouvrir aussi le menu principal des astuces
        const menu = document.getElementById('astuces-menu');
        const mainIcon = document.getElementById('astuces-icon');
        if (menu && menu.style.display === 'none') {
            menu.style.display = 'block';
            if (mainIcon) {
                mainIcon.classList.remove('fa-chevron-down');
                mainIcon.classList.add('fa-chevron-up');
            }
        }
    }
});

// ============================================
// 📊 BARRE DE PROGRESSION OPTIMISÉE
// ============================================
let lastProgressUpdate = 0;
const PROGRESS_THROTTLE = 500; // Mettre à jour max toutes les 500ms

function updateProgressBar(current, total) {
    const now = Date.now();
    
    // Throttle les mises à jour
    if (now - lastProgressUpdate < PROGRESS_THROTTLE) {
        return;
    }
    lastProgressUpdate = now;
    
    const progressBar = document.getElementById('scan-progress-bar');
    const progressText = document.getElementById('scan-progress-text');
    
    if (progressBar && progressText) {
        const percentage = total > 0 ? Math.round((current / total) * 100) : 0;
        
        // Utiliser requestAnimationFrame pour éviter le flickering
        requestAnimationFrame(() => {
            progressBar.style.width = `${percentage}%`;
            progressText.textContent = `${current}/${total} (${percentage}%)`;
        });
    }
}

// ============================================
// 🎨 VISIBILITY CHANGE
// ============================================
document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
        if (autoScanInterval) { clearInterval(autoScanInterval); autoScanInterval = null; }
        if (thumbRefreshInterval) { clearInterval(thumbRefreshInterval); thumbRefreshInterval = null; }
        if (scanPollingInterval) { clearInterval(scanPollingInterval); scanPollingInterval = null; }
    } else {
        startAutoFileMonitor();
        startThumbAutoRefresh();
    }
});