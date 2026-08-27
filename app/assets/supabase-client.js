(() => {
  const config = window.TRAZO_SUPABASE || {};
  const configured = Boolean(config.url && config.anonKey && window.supabase);
  const client = configured ? window.supabase.createClient(config.url, config.anonKey) : null;
  const state = { configured, client, user: null };
  const emit = () => window.dispatchEvent(new CustomEvent('trazo:auth', { detail: state }));

  async function init() {
    if (!client) { emit(); return state; }
    state.user = (await client.auth.getUser()).data.user;
    client.auth.onAuthStateChange((_event, session) => { state.user = session?.user || null; emit(); });
    emit(); return state;
  }
  async function google() {
    if (!client) throw new Error('Supabase todavía no está configurado. Consulta docs/SUPABASE.md.');
    const result = await client.auth.signInWithOAuth({ provider: 'google', options: { redirectTo: location.href.split('#')[0] } });
    if (result.error) throw result.error;
    return result;
  }
  async function magicLink(email) {
    if (!client) throw new Error('Supabase todavía no está configurado. Consulta docs/SUPABASE.md.');
    const result = await client.auth.signInWithOtp({ email, options: { emailRedirectTo: location.href.split('#')[0] } });
    if (result.error) throw result.error;
    return result;
  }
  async function signOut() { if (client) await client.auth.signOut(); }
  async function uploadFiles(files, briefId) {
    const paths = [];
    for (const file of files) {
      const safe = file.name.replace(/[^a-zA-Z0-9._-]/g, '-');
      const path = `${state.user.id}/${briefId}/${crypto.randomUUID()}-${safe}`;
      const { error } = await client.storage.from('brief-files').upload(path, file);
      if (error) throw error;
      paths.push(path);
    }
    return paths;
  }
  async function submitBrief(payload, files) {
    if (configured && config.requireAuth && !state.user) throw new Error('Accede a tu cuenta para enviar el proyecto.');
    if (!client || !state.user) return null;
    const reference = `WEB-${Date.now().toString(36).toUpperCase()}`;
    const { data, error } = await client.from('briefs').insert({ user_id: state.user.id, reference, payload }).select('id, reference').single();
    if (error) throw error;
    const filePaths = await uploadFiles(files, data.id);
    if (filePaths.length) {
      const { error: updateError } = await client.from('briefs').update({ file_paths: filePaths }).eq('id', data.id);
      if (updateError) throw updateError;
    }
    return { reference: data.reference };
  }
  async function submitTextRevision(payload) {
    if (configured && config.requireAuth && !state.user) throw new Error('Accede a tu cuenta para enviar cambios.');
    if (!client || !state.user) return null;
    const reference = `TXT-${Date.now().toString(36).toUpperCase()}`;
    const { error } = await client.from('text_revisions').insert({ user_id: state.user.id, project_identifier: payload.identifier, reference, payload });
    if (error) throw error;
    return { reference };
  }
  window.trazoData = { state, init, google, magicLink, signOut, submitBrief, submitTextRevision };
  init();
})();
