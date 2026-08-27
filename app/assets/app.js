const form = document.querySelector('#briefForm');
const steps = [...document.querySelectorAll('.step')];
const prevButton = document.querySelector('#prevButton');
const nextButton = document.querySelector('#nextButton');
const submitButton = document.querySelector('#submitButton');
const progressBar = document.querySelector('#progressBar');
const progressLabel = document.querySelector('#progressLabel');
const formError = document.querySelector('#formError');
const preview = document.querySelector('#sitePreview');
const previewName = document.querySelector('#previewName');
const previewTagline = document.querySelector('#previewTagline');
const summary = document.querySelector('#summary');
const primaryColor = form.elements.primaryColor;
const secondaryColor = form.elements.secondaryColor;
const primaryColorValue = document.querySelector('#primaryColorValue');
const secondaryColorValue = document.querySelector('#secondaryColorValue');
const draftKey = 'trazo-brief-draft-v1';
const submissionEndpoint = document.body.dataset.submitEndpoint?.trim() || '';
let currentStep = 0;
let toastTimer;

const showToast = (message) => {
  const toast = document.querySelector('#toast');
  toast.textContent = message;
  toast.classList.add('visible');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toast.classList.remove('visible'), 2600);
};

const value = (name) => form.elements[name]?.value?.trim() || '';
const checkedValues = (name) => [...form.querySelectorAll(`[name="${name}"]:checked`)].map((input) => input.value);
const palettes = {
  Terracota: ['#b6533b', '#25352f'],
  Natural: ['#6f7551', '#3b4432'],
  Atlántica: ['#26465a', '#8bb4bf'],
  Editorial: ['#724137', '#d6b878'],
};

const syncColorControls = () => {
  primaryColorValue.textContent = primaryColor.value.toUpperCase();
  secondaryColorValue.textContent = secondaryColor.value.toUpperCase();
  const matchingPalette = Object.entries(palettes).find(([, colors]) => colors[0] === primaryColor.value && colors[1] === secondaryColor.value)?.[0];
  form.querySelectorAll('[name="colorPalette"]').forEach((input) => { input.checked = input.value === matchingPalette; });
};

form.querySelectorAll('[name="colorPalette"]').forEach((input) => input.addEventListener('change', () => {
  const [primary, secondary] = palettes[input.value];
  primaryColor.value = primary;
  secondaryColor.value = secondary;
  syncColorControls();
  updatePreview();
}));
primaryColor.addEventListener('input', syncColorControls);
secondaryColor.addEventListener('input', syncColorControls);

const showStep = (index) => {
  currentStep = Math.max(0, Math.min(steps.length - 1, index));
  steps.forEach((step, i) => step.classList.toggle('active', i === currentStep));
  progressBar.style.width = `${((currentStep + 1) / steps.length) * 100}%`;
  progressLabel.textContent = `Paso ${currentStep + 1} de ${steps.length} · ${steps[currentStep].dataset.name}`;
  prevButton.style.visibility = currentStep === 0 ? 'hidden' : 'visible';
  nextButton.style.display = currentStep === steps.length - 1 ? 'none' : 'block';
  submitButton.style.display = currentStep === steps.length - 1 ? 'block' : 'none';
  formError.classList.remove('visible');
  if (currentStep === steps.length - 1) renderSummary();
  window.scrollTo({ top: 0, behavior: 'smooth' });
};

const validateStep = () => {
  const required = [...steps[currentStep].querySelectorAll('[required]')];
  const invalid = required.find((field) => field.type === 'checkbox' ? !field.checked : !field.value.trim() || !field.checkValidity());
  if (!invalid) return true;
  invalid.focus();
  formError.textContent = invalid.type === 'checkbox' ? 'Necesitamos tu consentimiento para enviar el formulario.' : 'Completa los campos obligatorios antes de continuar.';
  formError.classList.add('visible');
  return false;
};

nextButton.addEventListener('click', () => {
  if (validateStep()) showStep(currentStep + 1);
});
prevButton.addEventListener('click', () => showStep(currentStep - 1));

document.querySelector('#styleGrid').addEventListener('change', (event) => {
  const selected = checkedValues('styles');
  if (selected.length > 3) {
    event.target.checked = false;
    showToast('Puedes elegir hasta tres estilos');
  }
  updatePreview();
});

const updatePreview = () => {
  previewName.textContent = value('businessName') || 'Tu negocio';
  const story = value('story');
  previewTagline.textContent = story ? `${story.slice(0, 74)}${story.length > 74 ? '…' : ''}` : 'Una historia que merece ser contada.';
  preview.style.setProperty('--preview-primary', value('primaryColor') || '#b6533b');
  preview.style.setProperty('--preview-secondary', value('secondaryColor') || '#25352f');
  [...preview.classList].filter((name) => name.startsWith('style-')).forEach((name) => preview.classList.remove(name));
  const firstStyle = checkedValues('styles')[0];
  if (firstStyle) preview.classList.add(`style-${firstStyle}`);
  const typography = value('typography');
  const typeMap = {
    'Con carácter / serif': 'Georgia, serif',
    'Limpia / sans serif': '"Trebuchet MS", sans-serif',
    'Manuscrita / cercana': 'cursive',
  };
  previewName.style.fontFamily = typeMap[typography] || 'Georgia, serif';
};

form.addEventListener('input', updatePreview);
form.addEventListener('change', updatePreview);

const setupUpload = (inputId, listId) => {
  const input = document.querySelector(`#${inputId}`);
  const list = document.querySelector(`#${listId}`);
  const box = input.closest('.upload-box');
  const render = () => {
    list.innerHTML = [...input.files].map((file) => `<span class="file-pill">${escapeHtml(file.name)} · ${formatBytes(file.size)}</span>`).join('');
  };
  input.addEventListener('change', render);
  ['dragenter', 'dragover'].forEach((name) => box.addEventListener(name, (event) => { event.preventDefault(); box.classList.add('dragging'); }));
  ['dragleave', 'drop'].forEach((name) => box.addEventListener(name, (event) => { event.preventDefault(); box.classList.remove('dragging'); }));
  box.addEventListener('drop', (event) => { input.files = event.dataTransfer.files; render(); });
};
setupUpload('logoFiles', 'logoFileList');
setupUpload('photoFiles', 'photoFileList');

function escapeHtml(text) {
  return String(text).replace(/[&<>'"]/g, (char) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' }[char]));
}
function formatBytes(bytes) {
  return bytes < 1024 * 1024 ? `${Math.ceil(bytes / 1024)} KB` : `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}

const buildPayload = () => ({
  client: {
    businessName: value('businessName'), contactName: value('contactName'), email: value('email'),
    phone: value('phone'), businessType: value('businessType'), story: value('story'),
  },
  identity: {
    logoStatus: value('logoStatus'), paletteMode: value('paletteMode'), primaryColor: value('primaryColor'),
    secondaryColor: value('secondaryColor'), colorPalette: value('colorPalette'), styles: checkedValues('styles'), typography: value('typography'),
    references: value('references'),
  },
  content: { sections: checkedValues('sections'), photosStatus: value('photosStatus') },
  features: checkedValues('features'),
  social: { instagram: value('instagram'), facebook: value('facebook'), tiktok: value('tiktok'), other: value('otherSocial') },
  launch: {
    domain: value('domain'), domainHelp: form.elements.domainHelp.checked, legal: value('legal'),
    maintenance: value('maintenance'), timeline: value('timeline'), notes: value('notes'),
    responsive: true, availability: '24/7',
  },
});

const renderSummary = () => {
  const data = buildPayload();
  const items = [
    ['Negocio', data.client.businessName || 'Sin indicar'],
    ['Estilo', data.identity.styles.join(', ') || 'Por definir juntos'],
    ['Tipografía', data.identity.typography || 'Por definir juntos'],
    ['Secciones', `${data.content.sections.length} seleccionadas`],
    ['Funciones', data.features.join(', ') || 'Ninguna seleccionada'],
    ['Dominio', data.launch.domain ? `www.${data.launch.domain}.es` : 'Por definir'],
    ['Textos legales', data.launch.legal || 'Por definir'],
    ['Mantenimiento', data.launch.maintenance || 'Por definir'],
  ];
  summary.innerHTML = `<div class="summary-title">Resumen de tu selección</div><div class="summary-grid">${items.map(([label, text]) => `<div class="summary-item"><small>${label}</small><strong>${escapeHtml(text)}</strong></div>`).join('')}</div>`;
};

const serializeDraft = () => {
  const draft = {};
  [...form.elements].forEach((field) => {
    if (!field.name || field.type === 'file' || field.name === 'consent') return;
    if (field.type === 'checkbox' || field.type === 'radio') {
      if (!draft[field.name]) draft[field.name] = [];
      if (field.checked) draft[field.name].push(field.value);
    } else draft[field.name] = field.value;
  });
  return draft;
};

document.querySelector('#saveDraft').addEventListener('click', () => {
  localStorage.setItem(draftKey, JSON.stringify(serializeDraft()));
  showToast('Borrador guardado en este dispositivo');
});

const loadDraft = () => {
  const raw = localStorage.getItem(draftKey);
  if (!raw) return;
  try {
    const draft = JSON.parse(raw);
    [...form.elements].forEach((field) => {
      if (!field.name || !(field.name in draft)) return;
      if (field.type === 'checkbox' || field.type === 'radio') field.checked = draft[field.name].includes(field.value);
      else field.value = draft[field.name];
    });
    showToast('Hemos recuperado tu borrador');
    syncColorControls();
    updatePreview();
  } catch { localStorage.removeItem(draftKey); }
};

form.addEventListener('submit', async (event) => {
  event.preventDefault();
  if (!validateStep()) return;
  submitButton.disabled = true;
  submitButton.textContent = 'Enviando…';
  formError.classList.remove('visible');
  const body = new FormData();
  const submission = buildPayload();
  body.append('payload', JSON.stringify(submission));
  [...document.querySelector('#logoFiles').files, ...document.querySelector('#photoFiles').files].forEach((file) => body.append('files', file));
  try {
    if (!submissionEndpoint) throw new Error('El servicio de recepción no está configurado');
    const response = await fetch(submissionEndpoint, {
      method: 'POST',
      body,
      headers: { Accept: 'application/json' },
    });
    const result = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(result.error || result.detail || 'No se ha podido enviar el formulario');
    result.reference ||= `WEB-${Date.now().toString(36).toUpperCase()}`;
    const successMessage = 'Hemos recibido toda la información. La revisaremos con calma y nos pondremos en contacto contigo.';
    localStorage.removeItem(draftKey);
    form.style.display = 'none';
    document.querySelector('.intro-tag').style.display = 'none';
    document.querySelector('#referenceCode').textContent = result.reference;
    document.querySelector('#successMessage').textContent = successMessage;
    document.querySelector('#success').classList.add('visible');
    document.querySelector('.top-progress').style.visibility = 'hidden';
    document.querySelector('#saveDraft').style.visibility = 'hidden';
    window.scrollTo({ top: 0, behavior: 'smooth' });
  } catch (error) {
    formError.textContent = error.message;
    formError.classList.add('visible');
  } finally {
    submitButton.disabled = false;
    submitButton.innerHTML = 'Enviar formulario <span>→</span>';
  }
});

document.querySelector('#newBrief').addEventListener('click', () => window.location.reload());
loadDraft();
showStep(0);
syncColorControls();
updatePreview();
