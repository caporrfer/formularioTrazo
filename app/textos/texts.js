const access = document.querySelector('#access');
const editor = document.querySelector('#editor');
const success = document.querySelector('#success');
const accessForm = document.querySelector('#accessForm');
const textsForm = document.querySelector('#textsForm');
const list = document.querySelector('#textList');
const search = document.querySelector('#search');
const accessError = document.querySelector('#accessError');
const submitError = document.querySelector('#submitError');
const additions = document.querySelector('#additionList');
let project = null;
let originals = new Map();

const endpoint = '../api/content-editor';
const escapeHtml = value => String(value).replace(/[&<>'"]/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[char]));

function updateCount() {
  const changed = [...list.querySelectorAll('textarea')].filter(input => input.value.trim() !== originals.get(input.dataset.id)).length;
  const added = [...additions.querySelectorAll('.addition')].filter(row => row.querySelector('[name=title]').value.trim() || row.querySelector('textarea').value.trim()).length;
  const total = changed + added;
  document.querySelector('#changeCount').textContent = `${total} ${total === 1 ? 'cambio' : 'cambios'}`;
  document.querySelector('#bottomCount').textContent = `${total} ${total === 1 ? 'cambio preparado' : 'cambios preparados'}`;
}

function renderTexts(texts) {
  originals = new Map(texts.map(item => [item.id, item.text]));
  const sections = new Map();
  texts.forEach((item, index) => { const numbered = { ...item, number: String(index + 1).padStart(2, '0') }; if (!sections.has(item.section)) sections.set(item.section, []); sections.get(item.section).push(numbered); });
  list.innerHTML = [...sections].map(([section, items]) => `<section class="text-section"><h2 class="section-title">${escapeHtml(section)}</h2>${items.map(item => `<article class="text-card" data-search="${escapeHtml(`${item.number} ${item.label} ${item.text}`.toLowerCase())}"><div class="text-meta"><code>${escapeHtml(item.number)}</code><span>${escapeHtml(item.label)}</span></div><textarea data-id="${escapeHtml(item.id)}" aria-label="${escapeHtml(item.label)}">${escapeHtml(item.text)}</textarea><div class="text-actions"><small>Texto actual de la web</small><button class="reset" type="button">Restaurar</button></div></article>`).join('')}</section>`).join('');
  list.querySelectorAll('textarea').forEach(input => input.addEventListener('input', () => { input.closest('.text-card').classList.toggle('is-changed', input.value.trim() !== originals.get(input.dataset.id)); updateCount(); }));
  list.querySelectorAll('.reset').forEach(button => button.addEventListener('click', () => { const input = button.closest('.text-card').querySelector('textarea'); input.value = originals.get(input.dataset.id); input.dispatchEvent(new Event('input')); }));
  document.querySelector('#resultCount').textContent = `${texts.length} textos disponibles`;
}

accessForm.addEventListener('submit', async event => {
  event.preventDefault(); accessError.textContent = '';
  const identifier = document.querySelector('#identifier').value.trim().toLowerCase();
  const button = accessForm.querySelector('button'); button.disabled = true; button.textContent = 'Comprobando…';
  try {
    const response = await fetch(`${endpoint}?identifier=${encodeURIComponent(identifier)}`, { headers: { Accept: 'application/json' } });
    const data = await response.json(); if (!response.ok) throw new Error(data.error || 'No se ha podido acceder.');
    project = data; renderTexts(data.texts); document.querySelector('#projectId').textContent = data.identifier; document.querySelector('#projectName').textContent = data.project;
    access.hidden = true; editor.hidden = false; window.scrollTo({ top: 0 });
  } catch (error) { accessError.textContent = error.message; }
  finally { button.disabled = false; button.innerHTML = 'Acceder <span>→</span>'; }
});

search.addEventListener('input', () => {
  const term = search.value.trim().toLowerCase(); let visible = 0;
  list.querySelectorAll('.text-card').forEach(card => { card.hidden = !card.dataset.search.includes(term); if (!card.hidden) visible += 1; });
  list.querySelectorAll('.text-section').forEach(section => { section.hidden = !section.querySelector('.text-card:not([hidden])'); });
  document.querySelector('#resultCount').textContent = `${visible} textos visibles`;
});

function addRow() {
  const row = document.createElement('div'); row.className = 'addition';
  row.innerHTML = '<input name="title" placeholder="Título o nombre del texto" aria-label="Título del texto nuevo"><input name="location" placeholder="¿Dónde debería aparecer?" aria-label="Ubicación del texto nuevo"><button class="remove" type="button" aria-label="Eliminar texto nuevo">Eliminar</button><textarea name="text" placeholder="Escribe aquí el texto nuevo" aria-label="Contenido del texto nuevo"></textarea>';
  row.querySelector('.remove').addEventListener('click', () => { row.remove(); updateCount(); }); row.querySelectorAll('input,textarea').forEach(input => input.addEventListener('input', updateCount)); additions.appendChild(row);
}
document.querySelector('#addText').addEventListener('click', addRow); addRow();
document.querySelector('#exit').addEventListener('click', () => location.reload());

textsForm.addEventListener('submit', async event => {
  event.preventDefault(); submitError.textContent = '';
  const changes = [...list.querySelectorAll('textarea')].filter(input => input.value.trim() !== originals.get(input.dataset.id)).map(input => ({ id: input.dataset.id, text: input.value.trim() }));
  const newTexts = [...additions.querySelectorAll('.addition')].map(row => ({ title: row.querySelector('[name=title]').value.trim(), location: row.querySelector('[name=location]').value.trim(), text: row.querySelector('textarea').value.trim() })).filter(item => item.title || item.text || item.location);
  if (newTexts.some(item => !item.title || !item.text)) { submitError.textContent = 'Completa el título y el contenido de cada texto nuevo.'; return; }
  const button = document.querySelector('#submitButton'); button.disabled = true; button.textContent = 'Guardando…';
  try {
    const payload = { identifier: project.identifier, changes, additions: newTexts };
    let data = await window.trazoData?.submitTextRevision(payload);
    if (!data) {
      const response = await fetch(endpoint, { method: 'POST', headers: { 'Content-Type': 'application/json', Accept: 'application/json' }, body: JSON.stringify(payload) });
      data = await response.json(); if (!response.ok) throw new Error(data.error || 'No se han podido guardar los cambios.');
    }
    document.querySelector('#reference').textContent = data.reference; editor.hidden = true; success.hidden = false; window.scrollTo({ top: 0, behavior: 'smooth' });
  } catch (error) { submitError.textContent = error.message; }
  finally { button.disabled = false; button.innerHTML = 'Enviar cambios <span>→</span>'; }
});
document.querySelector('#reviewAgain').addEventListener('click', () => location.reload());
