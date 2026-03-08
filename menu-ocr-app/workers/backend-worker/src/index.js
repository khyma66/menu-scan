// menu-ocr-backend — Cloudflare Worker
// Replaces the entire FastAPI backend on Cloudflare edge
// Handles OCR (Gemini + Groq), user management, health profiles, etc.

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const path = url.pathname;
    const method = request.method;

    // CORS preflight
    if (method === 'OPTIONS') return corsResponse();

    try {
      const res = await route(path, method, request, url, env);
      return addCors(res);
    } catch (err) {
      console.error('Unhandled error:', err);
      return addCors(json({ error: 'Something went wrong. Please try again.' }, 500));
    }
  }
};

// ─── Router ───────────────────────────────────────────────────
async function route(path, method, req, url, env) {
  // Health / Root
  if (path === '/' && method === 'GET') return json({ message: 'Menu OCR API', version: '2.0.0', docs: '/health' });
  if (path === '/health' && method === 'GET') return json({ status: 'healthy', environment: env.ENVIRONMENT, version: '2.0.0', timestamp: new Date().toISOString() });

  // ─── OCR ──────────────────────────────────
  if (path === '/ocr/process-upload' && method === 'POST') return handleOcrUpload(req, env);
  if (path === '/ocr/process' && method === 'POST') return handleOcrProcess(req, env);
  if (path === '/ocr/translate-menu-items' && method === 'POST') return handleTranslate(req, env);
  if (path === '/ocr/translate' && method === 'POST') return handleTranslateRaw(req, env);

  // ─── Dishes ───────────────────────────────
  if (path === '/dishes/extract' && method === 'POST') return handleDishesExtract(req, env);
  if (path === '/dishes/' && method === 'GET') return handleGetDishes(req, env);

  // ─── Table Extraction ─────────────────────
  if (path === '/table-extraction/extract' && method === 'POST') return handleTableExtract(req, env);
  if (path === '/table-extraction/extract-from-ocr' && method === 'POST') return handleTableExtractOcr(req, env);

  // ─── Auth ─────────────────────────────────
  if (path === '/auth/test' && method === 'GET') return json({ message: 'Auth working', status: 'ok' });
  if (path === '/auth/user' && method === 'GET') return handleAuthUser(req, env);
  if (path === '/auth/profile' && method === 'POST') return handleAuthProfileUpdate(req, env);
  if (path.startsWith('/auth/health-conditions')) return handleAuthHealthConditions(path, method, req, env);
  // Also serve /health-conditions (iOS calls this path)
  if (path.startsWith('/health-conditions')) return handleAuthHealthConditions('/auth' + path, method, req, env);

  // ─── Health Profile ───────────────────────
  if (path === '/health/profile' && (method === 'GET' || method === 'POST')) return handleHealthProfile(method, req, env);
  if (path === '/health/conditions' && method === 'GET') return handleHealthConditionsList(req, env);
  if (path.startsWith('/health/conditions') && method === 'POST') return handleHealthConditionAdd(req, env);
  if (path.startsWith('/health/conditions/') && method === 'DELETE') return handleHealthConditionDelete(path, req, env);
  if (path === '/health/recommendations' && method === 'POST') return handleHealthRecommendations(req, env);
  if (path === '/health/analytics' && method === 'GET') return handleHealthAnalytics(req, env);

  // ─── Health Profile Compat (v1) ───────────
  if (path === '/v1/user/health-profile' && method === 'GET') return handleV1HealthProfileGet(req, env);
  if (path === '/v1/user/health-profile' && method === 'PUT') return handleV1HealthProfilePut(req, env);

  // ─── User Management ──────────────────────
  if (path === '/user/app-profile') return handleAppProfile(method, req, env);
  if (path === '/user/discovery-preferences') return handleDiscoveryPrefs(method, req, env);
  if (path === '/user/profile-preferences') return handleProfilePrefs(method, req, env);
  if (path === '/user/preferences/food-preferences' && method === 'GET') return handleFoodPrefsGet(req, env);
  if (path === '/user/preferences/food-preferences' && method === 'POST') return handleFoodPrefsAdd(req, env);
  if (path.startsWith('/user/preferences/food-preferences/') && method === 'DELETE') return handleFoodPrefsDelete(path, req, env);
  if (path === '/user/preferences/profile') return handleUserPrefsProfile(method, req, env);
  if (path === '/user/saved-cards' && method === 'GET') return handleSavedCardsGet(req, env);
  if (path === '/user/saved-cards' && method === 'POST') return handleSavedCardsAdd(req, env);
  if (path === '/user/payment-history' && method === 'GET') return handlePaymentHistory(req, env);
  if (path === '/user/subscription/plans' && method === 'GET') return handleSubscriptionPlans(req, env);
  if (path === '/user/subscription' && method === 'GET') return handleSubscriptionInfo(req, env);
  if (path === '/user/subscription/select' && method === 'PUT') return handleSubscriptionSelect(req, env);
  if (path === '/user/profile' && method === 'GET') return handleFullProfile(req, env);
  if (path === '/user/profile' && method === 'POST') return handleProfileUpdate(req, env);
  if (path.startsWith('/user/addresses')) return handleAddresses(path, method, req, env);
  if (path === '/user/change-password' && method === 'POST') return handleChangePassword(req, env);
  if (path.startsWith('/user/referral')) return handleReferral(path, method, req, env);

  // ─── Notifications & Recent Scans ──────────
  if (path === '/user/notifications' && method === 'GET') return handleNotificationsGet(req, env);
  if (path === '/user/notifications' && method === 'POST') return handleNotificationsCreate(req, env);
  if (path === '/user/recent-scans' && method === 'GET') return handleRecentScansGet(req, env);
  if (path === '/user/recent-scans' && method === 'POST') return handleRecentScansCreate(req, env);

  // ─── Auth Proxy (replaces direct anon-key calls from clients) ──
  if (path === '/proxy/auth/signup' && method === 'POST') return handleProxyAuthSignup(req, env);
  if (path === '/proxy/auth/signin' && method === 'POST') return handleProxyAuthSignin(req, env);
  if (path === '/proxy/auth/apple' && method === 'POST') return handleProxyAuthApple(req, env);
  if (path === '/proxy/auth/signout' && method === 'POST') return handleProxyAuthSignout(req, env);
  if (path === '/proxy/auth/recover' && method === 'POST') return handleProxyAuthRecover(req, env);

  // ─── Stripe / Checkout ─────────────────────
  if (path === '/stripe/create-checkout-session' && method === 'POST') return handleStripeCheckout(req, env);
  if (path === '/stripe/webhook' && method === 'POST') return handleStripeWebhook(req, env);

  // ─── LLM Status ───────────────────────────
  if (path === '/llm/status' && method === 'GET') return json({ provider: 'gemini', configured: true, model: env.GEMINI_MODEL, api_key_configured: !!env.GEMINI_API_KEY });
  if (path === '/llm/providers' && method === 'GET') return json({ current_provider: 'gemini', providers: ['gemini', 'groq'] });

  return json({ error: 'Not Found', path }, 404);
}


// ─── Helpers ──────────────────────────────────────────────────

function json(data, status = 200) {
  return new Response(JSON.stringify(data), { status, headers: { 'Content-Type': 'application/json' } });
}

function corsResponse() {
  return new Response(null, { status: 204, headers: corsHeaders() });
}

function corsHeaders() {
  return {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type,Authorization',
    'Access-Control-Max-Age': '86400',
  };
}

function addCors(res) {
  const h = corsHeaders();
  for (const [k, v] of Object.entries(h)) res.headers.set(k, v);
  return res;
}

// ─── Fetch with timeout (AbortController) ─────────────────────

async function fetchWithTimeout(url, opts, timeoutMs = 25000) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const res = await fetch(url, { ...opts, signal: controller.signal });
    return res;
  } finally {
    clearTimeout(timer);
  }
}

// ─── Auth Helpers ─────────────────────────────────────────────

async function getUser(req, env) {
  const auth = req.headers.get('Authorization');
  if (!auth) return null;
  const token = auth.replace('Bearer ', '');
  try {
    const r = await fetch(`${env.SUPABASE_URL}/auth/v1/user`, {
      headers: { Authorization: `Bearer ${token}`, apikey: env.SUPABASE_SERVICE_KEY }
    });
    if (!r.ok) return null;
    const u = await r.json();
    return { id: u.id, email: u.email, name: u.user_metadata?.full_name || u.user_metadata?.name, created_at: u.created_at };
  } catch { return null; }
}

async function requireUser(req, env) {
  const u = await getUser(req, env);
  if (!u) throw new Error('Unauthorized');
  return u;
}

// Supabase PostgREST helper
async function sb(env, path, opts = {}) {
  const url = `${env.SUPABASE_URL}/rest/v1${path}`;
  const headers = {
    apikey: env.SUPABASE_SERVICE_KEY,
    Authorization: `Bearer ${env.SUPABASE_SERVICE_KEY}`,
    'Content-Type': 'application/json',
    Prefer: opts.prefer || 'return=representation',
    ...opts.headers,
  };
  const res = await fetch(url, { method: opts.method || 'GET', headers, body: opts.body ? JSON.stringify(opts.body) : undefined });
  if (!res.ok) {
    const t = await res.text();
    console.error('Supabase error:', res.status, t);
    return opts.defaultVal !== undefined ? opts.defaultVal : null;
  }
  const ct = res.headers.get('content-type') || '';
  if (ct.includes('json')) return res.json();
  return null;
}


// ════════════════════════════════════════════════════════════════
// OCR ENDPOINTS
// ════════════════════════════════════════════════════════════════

async function handleOcrUpload(req, env) {
  const start = Date.now();
  let formData;
  try { formData = await req.formData(); } catch (e) { return json({ success: false, error: 'Invalid multipart form data. Send image as multipart/form-data.' }, 400); }
  const imageFile = formData.get('image');
  if (!imageFile) return json({ success: false, error: 'No image provided' }, 400);

  const language = formData.get('language') || 'auto';
  const outputLanguage = formData.get('output_language') || 'en';
  const useLlm = formData.get('use_llm_enhancement') !== 'false';

  const imageBytes = await imageFile.arrayBuffer();
  if (imageBytes.byteLength > 10 * 1024 * 1024) return json({ success: false, error: 'Image too large (max 10MB)' }, 400);

  const base64 = arrayBufferToBase64(imageBytes);
  const user = await getUser(req, env);

  // Get health profile if authenticated
  let healthProfile = null;
  if (user) {
    healthProfile = await sb(env, `/user_health_profiles?user_id=eq.${user.id}&select=*`, { defaultVal: [] });
    if (Array.isArray(healthProfile) && healthProfile.length > 0) healthProfile = healthProfile[0];
    else healthProfile = null;
  }

  // Pass 1: Gemini OCR extraction
  let geminiItems = [];
  try {
    geminiItems = await geminiExtract(base64, language, env);
  } catch (e) {
    console.error('Gemini pass 1 error:', e.message);
  }

  // Pass 2: Gemini completeness audit
  let pass2Items = [];
  try {
    pass2Items = await geminiCompletenessAudit(base64, geminiItems, env);
  } catch (e) {
    console.error('Gemini pass 2 error:', e.message);
  }

  // Merge & deduplicate
  const merged = mergeUniqueRows(geminiItems, pass2Items);

  // Groq enhancement (add ingredients, taste, recommendations, etc.)
  let enhancedItems = merged;
  if (useLlm && merged.length > 0) {
    try {
      enhancedItems = await groqEnhance(merged, healthProfile, env);
    } catch (e) {
      console.error('Groq enhance error:', e.message);
      enhancedItems = merged.map(fillDefaults);
    }
  } else {
    enhancedItems = merged.map(fillDefaults);
  }

  // Optional translation
  let translatedItems = null;
  if (outputLanguage && outputLanguage !== 'en') {
    try {
      translatedItems = await groqTranslate(enhancedItems, outputLanguage, env);
    } catch (e) {
      console.error('Translation error:', e.message);
    }
  }

  // If no items found at all, return a helpful message
  if (merged.length === 0) {
    return json({
      success: true,
      menu_items: [],
      gemini_menu_items: [],
      raw_text: '',
      processing_time_ms: Date.now() - start,
      enhanced: false,
      cached: false,
      metadata: { gemini_count: 0, pass2_count: 0, merged_count: 0, enhanced_count: 0 },
      user_message: 'No menu items found. Please try a clearer photo with good lighting.'
    });
  }

  const elapsed = Date.now() - start;
  return json({
    success: true,
    menu_items: translatedItems || enhancedItems,
    gemini_menu_items: merged.map(fillDefaults),
    raw_text: '',
    processing_time_ms: elapsed,
    enhanced: useLlm,
    cached: false,
    metadata: { gemini_count: geminiItems.length, pass2_count: pass2Items.length, merged_count: merged.length, enhanced_count: enhancedItems.length }
  });
}

async function handleOcrProcess(req, env) {
  const body = await req.json();
  const base64 = body.image_base64 || '';
  if (!base64 && !body.image_url) return json({ success: false, error: 'No image provided' }, 400);

  let imageBase64 = base64;
  if (!imageBase64 && body.image_url) {
    const resp = await fetch(body.image_url);
    const buf = await resp.arrayBuffer();
    imageBase64 = arrayBufferToBase64(buf);
  }

  const start = Date.now();
  let items = [];
  try {
    items = await geminiExtract(imageBase64, body.language || 'auto', env);
    items = items.map(fillDefaults);
  } catch (e) {
    console.error('OCR process error:', e.message);
  }

  return json({ success: true, menu_items: items, raw_text: '', processing_time_ms: Date.now() - start, enhanced: false, cached: false });
}


// ─── Gemini API Calls ─────────────────────────────────────────

const GEMINI_PROMPT = `### ROLE
You are an expert Data Extraction Specialist and OCR Engineer. Your task is to convert this menu image into a perfectly structured digital format.
### PHASE 1: PRE-SCAN (Internal Reasoning)
Before transcribing, mentally map image coordinates, identify headers/subheaders, and understand multi-column text-price relationships.
### PHASE 2: ENGLISH-ONLY EXTRACTION RULES
Translate the menu COMPLETELY into English. Every single dish from the image must be present in the final output.
1) MANDATORY COVERAGE: Do not skip ANY item. If there are N dishes, output N dish rows.
2) ENGLISH-ONLY: Do not include original-language dish text; output high-quality English for dish names, descriptions, and category headers.
3) SYMBOL FIDELITY: Retain currency symbols, allergen numbers, and units exactly where visible.
4) CULINARY ACCURACY: Translate culinary terms accurately in natural English.
5) ACCURACY OVER SPEED: If ambiguous, reason conservatively; use [?] only if truly unreadable.
### PHASE 3: OUTPUT FORMAT
The application requires strict JSON (not markdown). Preserve menu structure using category field.
### PHASE 4: FOOTER EXTRACTION
Capture all fine print (taxes, service charge, bread cover, policy notes) as explicit rows if visible.
### FINAL STEP
Verify output item count matches visible image items before returning.
Output must be strict JSON only. No markdown, no commentary.

Return this exact structure:
{
  "menu_items": [
    {
      "item": "Dish name in English",
      "description_ingredients": "Short description and key ingredients in English",
      "price": "Original menu price string",
      "currency": "ISO code if known else null",
      "category": "section heading or normalized category"
    }
  ]
}`;

async function geminiExtract(base64, languageHint, env) {
  const prompt = GEMINI_PROMPT + (languageHint !== 'auto' ? `\n\nLanguage hint: The menu is likely in ${languageHint}.` : '');
  const payload = {
    contents: [{ role: 'user', parts: [{ text: prompt }, { inline_data: { mime_type: 'image/jpeg', data: base64 } }] }],
    generationConfig: { temperature: 0.0, response_mime_type: 'application/json' },
  };

  const res = await fetchWithTimeout(
    `https://generativelanguage.googleapis.com/v1beta/models/${env.GEMINI_MODEL}:generateContent?key=${env.GEMINI_API_KEY}`,
    { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) },
    25000
  );

  if (!res.ok) { const t = await res.text(); console.error(`Gemini API ${res.status}: ${t}`); throw new Error('Menu extraction service temporarily unavailable'); }

  const data = await res.json();
  const text = data.candidates?.[0]?.content?.parts?.[0]?.text || '';
  return parseMenuItems(text);
}

async function geminiCompletenessAudit(base64, existingItems, env) {
  const names = existingItems.map(i => i.name || i.item || '').join(', ');
  const prompt = `You already extracted these items from the menu image: [${names}]
Re-scan the image carefully for ANY missed items — check side columns, footers, subsections, drinks, desserts, specials.
Return ONLY the missed items (not already listed above) in the same JSON format:
{
  "menu_items": [
    { "item": "...", "description_ingredients": "...", "price": "...", "currency": null, "category": "..." }
  ]
}
If nothing is missed, return {"menu_items": []}`;

  const payload = {
    contents: [{ role: 'user', parts: [{ text: prompt }, { inline_data: { mime_type: 'image/jpeg', data: base64 } }] }],
    generationConfig: { temperature: 0.0, response_mime_type: 'application/json' },
  };

  const res = await fetchWithTimeout(
    `https://generativelanguage.googleapis.com/v1beta/models/${env.GEMINI_MODEL}:generateContent?key=${env.GEMINI_API_KEY}`,
    { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) },
    25000
  );

  if (!res.ok) return [];
  const data = await res.json();
  const text = data.candidates?.[0]?.content?.parts?.[0]?.text || '';
  return parseMenuItems(text);
}

function parseMenuItems(text) {
  try {
    let parsed;
    try { parsed = JSON.parse(text); } catch {
      const m = text.match(/```(?:json)?\s*([\s\S]*?)```/);
      if (m) parsed = JSON.parse(m[1]);
      else {
        const m2 = text.match(/\{[\s\S]*\}/);
        if (m2) parsed = JSON.parse(m2[0]);
        else return [];
      }
    }
    const items = parsed.menu_items || parsed;
    if (!Array.isArray(items)) return [];
    return items.map(i => ({
      name: i.item || i.name || '',
      price: i.price || null,
      description: i.description_ingredients || i.description || null,
      category: i.category || null,
    }));
  } catch { return []; }
}

function mergeUniqueRows(pass1, pass2) {
  const seen = new Set();
  const result = [];
  for (const row of [...pass1, ...pass2]) {
    const key = `${(row.name || '').toLowerCase().trim()}|${(row.price || '').trim()}`;
    if (!seen.has(key)) { seen.add(key); result.push(row); }
  }
  return result;
}


// ─── Groq API Calls ──────────────────────────────────────────

async function groqEnhance(rows, healthProfile, env) {
  const healthInfo = healthProfile
    ? `User health profile: conditions=${JSON.stringify(healthProfile.health_conditions || [])}, allergies=${JSON.stringify(healthProfile.allergies || [])}, dietary=${JSON.stringify(healthProfile.dietary_preferences || [])}`
    : 'No health profile available — give general recommendations.';

  const rowsJson = JSON.stringify(rows.map((r, i) => ({ index: i, name: r.name, price: r.price, description: r.description, category: r.category })));

  const prompt = `You are an expert culinary nutritionist. Given these menu items and user health data, enrich each item.

${healthInfo}

Menu items:
${rowsJson}

For EACH item (maintain exact same count=${rows.length}), return:
{
  "menu_items": [
    {
      "name": "exact same name",
      "price": "exact same price",
      "description": "enhanced description",
      "category": "same category",
      "ingredients": ["ingredient1", "ingredient2"],
      "taste": "flavor profile",
      "similarDish1": "a similar well-known dish",
      "similarDish2": "another similar dish",
      "recommendation": "Most Recommended" or "Recommended" or "Not Recommended",
      "recommendation_reason": "why this recommendation based on health profile",
      "allergens": ["allergen1"],
      "spiciness_level": "Mild" or "Medium" or "Hot" or "Very Hot" or "None",
      "preparation_method": "how it is typically prepared"
    }
  ]
}

RULES:
- Output EXACTLY ${rows.length} items.
- Do NOT merge, drop, or reorder any items.
- Return strict JSON only.`;

  const data = await callGroq(prompt, env);
  const items = data?.menu_items || data;
  if (!Array.isArray(items) || items.length === 0) return rows.map(fillDefaults);

  // Map enhanced data back to original rows
  return rows.map((orig, i) => {
    const enh = items[i] || {};
    return {
      name: orig.name,
      price: orig.price,
      description: enh.description || orig.description || null,
      category: enh.category || orig.category || null,
      ingredients: enh.ingredients || [],
      taste: enh.taste || null,
      similarDish1: enh.similarDish1 || null,
      similarDish2: enh.similarDish2 || null,
      recommendation: enh.recommendation || 'Recommended',
      recommendation_reason: enh.recommendation_reason || null,
      allergens: enh.allergens || [],
      spiciness_level: enh.spiciness_level || 'None',
      preparation_method: enh.preparation_method || null,
    };
  });
}

async function groqTranslate(items, targetLang, env) {
  // Chunk large batches to prevent Groq from dropping items
  const CHUNK = 12;
  if (items.length > CHUNK) {
    const results = [];
    for (let i = 0; i < items.length; i += CHUNK) {
      const chunk = items.slice(i, i + CHUNK);
      const translated = await groqTranslateChunk(chunk, targetLang, env);
      results.push(...translated);
    }
    return results;
  }
  return groqTranslateChunk(items, targetLang, env);
}

async function groqTranslateChunk(items, targetLang, env) {
  const prompt = `Translate ALL ${items.length} menu items below into ${targetLang}.

FIELDS TO TRANSLATE: name, description, category, ingredients (each element), taste, similarDish1, similarDish2, recommendation_reason, allergens (each element), preparation_method.
FIELDS TO KEEP AS-IS (do NOT translate): price, spiciness_level, recommendation.

CRITICAL RULES:
- You MUST return EXACTLY ${items.length} items — no more, no less.
- Preserve every field from each item. Do NOT drop or merge items.
- Keep the same JSON key names. Keep array fields as arrays.
- Return strict JSON only: { "menu_items": [...] }

Input (${items.length} items):
${JSON.stringify(items)}`;

  const data = await callGroq(prompt, env);
  const translated = data?.menu_items || data;
  if (!Array.isArray(translated) || translated.length === 0) return items;

  // Safely merge: use translated fields when available, fall back to originals
  return items.map((orig, i) => {
    const tr = translated[i];
    if (!tr) return orig;
    return {
      name: tr.name || orig.name,
      price: orig.price,                              // never translate price
      description: tr.description || orig.description,
      category: tr.category || orig.category,
      ingredients: Array.isArray(tr.ingredients) && tr.ingredients.length > 0 ? tr.ingredients : orig.ingredients,
      taste: tr.taste || orig.taste,
      similarDish1: tr.similarDish1 || orig.similarDish1,
      similarDish2: tr.similarDish2 || orig.similarDish2,
      recommendation: orig.recommendation,             // never translate
      recommendation_reason: tr.recommendation_reason || orig.recommendation_reason,
      allergens: Array.isArray(tr.allergens) && tr.allergens.length > 0 ? tr.allergens : orig.allergens,
      spiciness_level: orig.spiciness_level,           // never translate
      preparation_method: tr.preparation_method || orig.preparation_method,
    };
  });
}

async function callGroq(prompt, env) {
  const res = await fetchWithTimeout('https://api.groq.com/openai/v1/chat/completions', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${env.GROQ_API_KEY}` },
    body: JSON.stringify({
      model: env.GROQ_MODEL,
      messages: [
        { role: 'system', content: 'You are a strict JSON API. Return valid JSON only. No markdown fences.' },
        { role: 'user', content: prompt },
      ],
      temperature: 0.0,
      response_format: { type: 'json_object' },
    }),
  }, 25000);

  if (!res.ok) { const t = await res.text(); console.error(`Groq API ${res.status}: ${t}`); throw new Error('Enhancement service temporarily unavailable'); }
  const data = await res.json();
  const text = data.choices?.[0]?.message?.content || '';
  try { return JSON.parse(text); } catch {
    const m = text.match(/\{[\s\S]*\}/);
    if (m) return JSON.parse(m[0]);
    return null;
  }
}

function fillDefaults(row) {
  return {
    name: row.name || '',
    price: row.price || null,
    description: row.description || null,
    category: row.category || null,
    ingredients: row.ingredients || [],
    taste: row.taste || null,
    similarDish1: row.similarDish1 || null,
    similarDish2: row.similarDish2 || null,
    recommendation: row.recommendation || 'Recommended',
    recommendation_reason: row.recommendation_reason || null,
    allergens: row.allergens || [],
    spiciness_level: row.spiciness_level || 'None',
    preparation_method: row.preparation_method || null,
  };
}


// ─── Translation Endpoint ─────────────────────────────────────

async function handleTranslate(req, env) {
  const body = await req.json();
  const items = body.menu_items || [];
  const targetLang = body.target_language || 'en';
  if (targetLang === 'en' || items.length === 0) return json({ menu_items: items });
  try {
    const translated = await groqTranslate(items, targetLang, env);
    return json({ menu_items: translated });
  } catch (e) {
    console.error('Translation error:', e.message);
    return json({ menu_items: items, error: 'Translation is temporarily unavailable. Showing original text.' });
  }
}

async function handleTranslateRaw(req, env) {
  const form = await req.formData();
  const rawText = form.get('raw_text') || '';
  const detectedLang = form.get('detected_language') || 'unknown';
  // Use Groq to translate raw text into menu items
  return json({ success: true, menu_items: [], raw_text: rawText, processing_time_ms: 0 });
}


// ═══════════════════════════════════════════════════════════════
// DISHES & TABLE EXTRACTION
// ═══════════════════════════════════════════════════════════════

async function handleDishesExtract(req, env) {
  const body = await req.json();
  const text = body.text || '';
  const prompt = `Extract dish names, prices, and descriptions from this text. Return JSON: { "dishes": [{"name":"...","price":"...","description":"..."}] }\n\nText:\n${text}`;
  try {
    const data = await callGroq(prompt, env);
    return json({ dishes: data?.dishes || [] });
  } catch {
    return json({ dishes: [] });
  }
}

async function handleGetDishes(req, env) {
  const dishes = await sb(env, '/dishes?select=*&limit=100', { defaultVal: [] });
  return json(dishes || []);
}

async function handleTableExtract(req, env) {
  const body = await req.json();
  const prompt = `Extract a structured table from this text. Format as JSON rows with columns.\n\nText:\n${body.text || ''}`;
  try {
    const data = await callGroq(prompt, env);
    return json({ success: true, raw_table: data, format: body.format || 'json', model_used: env.GROQ_MODEL, tokens_used: 0 });
  } catch (e) {
    console.error('Table extraction error:', e.message);
    return json({ success: false, error: 'Table extraction is temporarily unavailable. Please try again.' }, 500);
  }
}

async function handleTableExtractOcr(req, env) {
  const body = await req.json();
  return handleTableExtract({ json: async () => ({ text: body.ocr_text || '', format: body.format || 'json' }) }, env);
}


// ═══════════════════════════════════════════════════════════════
// AUTH ENDPOINTS
// ═══════════════════════════════════════════════════════════════

async function handleAuthUser(req, env) {
  const user = await requireUser(req, env);
  return json(user);
}

async function handleAuthProfileUpdate(req, env) {
  const user = await requireUser(req, env);
  const body = await req.json();
  // Update profile in Supabase Auth metadata
  const token = req.headers.get('Authorization')?.replace('Bearer ', '');
  await fetch(`${env.SUPABASE_URL}/auth/v1/user`, {
    method: 'PUT',
    headers: { Authorization: `Bearer ${token}`, apikey: env.SUPABASE_SERVICE_KEY, 'Content-Type': 'application/json' },
    body: JSON.stringify({ data: { full_name: body.full_name, phone: body.phone } }),
  });
  return json({ message: 'Profile updated' });
}

async function handleAuthHealthConditions(path, method, req, env) {
  const user = await requireUser(req, env);
  if (method === 'GET') {
    const conditions = await sb(env, `/health_conditions?user_id=eq.${user.id}&select=*`, { defaultVal: [] });
    return json(conditions || []);
  }
  if (method === 'POST') {
    const body = await req.json();
    const result = await sb(env, '/health_conditions', {
      method: 'POST', body: { user_id: user.id, ...body }, prefer: 'return=representation',
    });
    return json({ message: 'Condition added', condition: result?.[0] || body });
  }
  if (method === 'DELETE') {
    const id = path.split('/').pop();
    await sb(env, `/health_conditions?id=eq.${id}&user_id=eq.${user.id}`, { method: 'DELETE', prefer: 'return=minimal' });
    return json({ message: 'Condition removed' });
  }
  return json({ error: 'Method not allowed' }, 405);
}


// ═══════════════════════════════════════════════════════════════
// HEALTH PROFILE
// ═══════════════════════════════════════════════════════════════

async function handleHealthProfile(method, req, env) {
  const user = await requireUser(req, env);
  if (method === 'GET') {
    const profiles = await sb(env, `/user_health_profiles?user_id=eq.${user.id}&select=*`, { defaultVal: [] });
    const profile = Array.isArray(profiles) && profiles.length > 0 ? profiles[0] : null;
    return json({ success: true, profile });
  }
  // POST — create
  const body = await req.json();
  const existing = await sb(env, `/user_health_profiles?user_id=eq.${user.id}&select=id`, { defaultVal: [] });
  if (Array.isArray(existing) && existing.length > 0) {
    // Already exists
    return json({ success: true, profile: existing[0] });
  }
  const result = await sb(env, '/user_health_profiles', {
    method: 'POST', body: { user_id: user.id, profile_name: body.profile_name || 'default' },
  });
  return json({ success: true, profile: result?.[0] || null });
}

async function handleHealthConditionsList(req, env) {
  const user = await requireUser(req, env);
  const conditions = await sb(env, `/health_conditions?user_id=eq.${user.id}&select=*`, { defaultVal: [] });
  return json(conditions || []);
}

async function handleHealthConditionAdd(req, env) {
  const user = await requireUser(req, env);
  const body = await req.json();
  const result = await sb(env, '/health_conditions', {
    method: 'POST', body: { user_id: user.id, ...body },
  });
  return json({ success: true, condition_id: result?.[0]?.id, condition: result?.[0] || body });
}

async function handleHealthConditionDelete(path, req, env) {
  const user = await requireUser(req, env);
  const conditionName = decodeURIComponent(path.split('/').pop());
  await sb(env, `/health_conditions?user_id=eq.${user.id}&condition_name=eq.${conditionName}`, { method: 'DELETE', prefer: 'return=minimal' });
  return json({ success: true, message: 'Condition removed' });
}

async function handleHealthRecommendations(req, env) {
  const user = await requireUser(req, env);
  const body = await req.json();
  const items = body.menu_items || [];

  // Get user health conditions
  const conditions = await sb(env, `/health_conditions?user_id=eq.${user.id}&select=*`, { defaultVal: [] });
  if (!conditions || conditions.length === 0) {
    return json({ recommendations: items.map(i => ({ ...i, recommendation: 'Recommended', recommendation_reason: 'No health conditions specified' })), total_items: items.length, analyzed_conditions: 0, generated_at: new Date().toISOString() });
  }

  // Use Groq to generate health-based recommendations
  try {
    const enhanced = await groqEnhance(items, { health_conditions: conditions.map(c => c.condition_name), allergies: [], dietary_preferences: [] }, env);
    return json({ recommendations: enhanced, total_items: enhanced.length, analyzed_conditions: conditions.length, generated_at: new Date().toISOString() });
  } catch {
    return json({ recommendations: items, total_items: items.length, analyzed_conditions: conditions.length, generated_at: new Date().toISOString() });
  }
}

async function handleHealthAnalytics(req, env) {
  const user = await requireUser(req, env);
  const conditions = await sb(env, `/health_conditions?user_id=eq.${user.id}&select=*`, { defaultVal: [] });
  return json({ total_actions: 0, conditions_by_type: {}, recent_activity: [], conditions_count: (conditions || []).length });
}


// ─── V1 Health Profile (Android compat) ──────────────────────

async function handleV1HealthProfileGet(req, env) {
  const user = await requireUser(req, env);
  const profiles = await sb(env, `/user_health_profiles?user_id=eq.${user.id}&select=*`, { defaultVal: [] });
  const p = Array.isArray(profiles) && profiles.length > 0 ? profiles[0] : {};
  return json({
    health_profile: {
      health_conditions: p.health_conditions || [],
      allergies: p.allergies || [],
      dietary_preferences: p.dietary_preferences || [],
      medical_notes: p.medical_notes || null,
    }
  });
}

async function handleV1HealthProfilePut(req, env) {
  const user = await requireUser(req, env);
  const body = await req.json();
  // Upsert
  const existing = await sb(env, `/user_health_profiles?user_id=eq.${user.id}&select=id`, { defaultVal: [] });
  if (Array.isArray(existing) && existing.length > 0) {
    await sb(env, `/user_health_profiles?user_id=eq.${user.id}`, {
      method: 'PATCH', body: { health_conditions: body.health_conditions, allergies: body.allergies, dietary_preferences: body.dietary_preferences, medical_notes: body.medical_notes },
    });
  } else {
    await sb(env, '/user_health_profiles', {
      method: 'POST', body: { user_id: user.id, ...body },
    });
  }
  return handleV1HealthProfileGet(req, env);
}


// ═══════════════════════════════════════════════════════════════
// USER MANAGEMENT
// ═══════════════════════════════════════════════════════════════

async function handleAppProfile(method, req, env) {
  const user = await requireUser(req, env);
  if (method === 'GET') {
    const profiles = await sb(env, `/app_profiles?user_id=eq.${user.id}&select=*`, { defaultVal: [] });
    if (Array.isArray(profiles) && profiles.length > 0) return json(profiles[0]);
    return json({ user_id: user.id, full_name: user.name, email: user.email, contact: null, phone: null, country: null });
  }
  if (method === 'PUT') {
    const body = await req.json();
    const existing = await sb(env, `/app_profiles?user_id=eq.${user.id}&select=id`, { defaultVal: [] });
    if (Array.isArray(existing) && existing.length > 0) {
      const result = await sb(env, `/app_profiles?user_id=eq.${user.id}`, { method: 'PATCH', body });
      return json(result?.[0] || { user_id: user.id, ...body });
    }
    const result = await sb(env, '/app_profiles', { method: 'POST', body: { user_id: user.id, ...body } });
    return json(result?.[0] || { user_id: user.id, ...body });
  }
  return json({ error: 'Method not allowed' }, 405);
}

async function handleDiscoveryPrefs(method, req, env) {
  const user = await requireUser(req, env);
  if (method === 'GET') {
    const prefs = await sb(env, `/discovery_preferences?user_id=eq.${user.id}&select=*`, { defaultVal: [] });
    if (Array.isArray(prefs) && prefs.length > 0) return json(prefs[0]);
    return json({ user_id: user.id, search_radius_miles: 10, selected_cuisines: [] });
  }
  if (method === 'PUT') {
    const body = await req.json();
    const existing = await sb(env, `/discovery_preferences?user_id=eq.${user.id}&select=id`, { defaultVal: [] });
    if (Array.isArray(existing) && existing.length > 0) {
      const result = await sb(env, `/discovery_preferences?user_id=eq.${user.id}`, { method: 'PATCH', body });
      return json(result?.[0] || { user_id: user.id, ...body });
    }
    const result = await sb(env, '/discovery_preferences', { method: 'POST', body: { user_id: user.id, ...body } });
    return json(result?.[0] || { user_id: user.id, ...body });
  }
  return json({ error: 'Method not allowed' }, 405);
}

async function handleProfilePrefs(method, req, env) {
  const user = await requireUser(req, env);
  if (method === 'GET') {
    const prefs = await sb(env, `/profile_preferences?user_id=eq.${user.id}&select=*`, { defaultVal: [] });
    if (Array.isArray(prefs) && prefs.length > 0) return json(prefs[0]);
    return json({ user_id: user.id, push_notifications: true, email_notifications: true, sms_notifications: false, marketing_emails: false, privacy_mode: false });
  }
  if (method === 'PUT') {
    const body = await req.json();
    const existing = await sb(env, `/profile_preferences?user_id=eq.${user.id}&select=id`, { defaultVal: [] });
    if (Array.isArray(existing) && existing.length > 0) {
      const result = await sb(env, `/profile_preferences?user_id=eq.${user.id}`, { method: 'PATCH', body });
      return json(result?.[0] || body);
    }
    const result = await sb(env, '/profile_preferences', { method: 'POST', body: { user_id: user.id, ...body } });
    return json(result?.[0] || body);
  }
  return json({ error: 'Method not allowed' }, 405);
}

async function handleFoodPrefsGet(req, env) {
  const user = await requireUser(req, env);
  const prefs = await sb(env, `/food_preferences?user_id=eq.${user.id}&select=*`, { defaultVal: [] });
  return json(prefs || []);
}

async function handleFoodPrefsAdd(req, env) {
  const user = await requireUser(req, env);
  const body = await req.json();
  const result = await sb(env, '/food_preferences', { method: 'POST', body: { user_id: user.id, ...body } });
  return json({ success: true, preference_id: result?.[0]?.id, message: 'Preference added' });
}

async function handleFoodPrefsDelete(path, req, env) {
  const user = await requireUser(req, env);
  const id = path.split('/').pop();
  await sb(env, `/food_preferences?id=eq.${id}&user_id=eq.${user.id}`, { method: 'DELETE', prefer: 'return=minimal' });
  return json({ success: true, message: 'Preference removed' });
}

async function handleUserPrefsProfile(method, req, env) {
  const user = await requireUser(req, env);
  if (method === 'GET') {
    const prefs = await sb(env, `/user_preferences?user_id=eq.${user.id}&select=*`, { defaultVal: [] });
    if (Array.isArray(prefs) && prefs.length > 0) return json(prefs[0]);
    return json({ user_id: user.id, dietary_restrictions: [], favorite_cuisines: [], spice_tolerance: 'medium', budget_preference: 'moderate' });
  }
  if (method === 'PUT') {
    const body = await req.json();
    const existing = await sb(env, `/user_preferences?user_id=eq.${user.id}&select=id`, { defaultVal: [] });
    if (Array.isArray(existing) && existing.length > 0) {
      const result = await sb(env, `/user_preferences?user_id=eq.${user.id}`, { method: 'PATCH', body });
      return json(result?.[0] || { user_id: user.id, ...body });
    }
    const result = await sb(env, '/user_preferences', { method: 'POST', body: { user_id: user.id, ...body } });
    return json(result?.[0] || { user_id: user.id, ...body });
  }
  return json({ error: 'Method not allowed' }, 405);
}

// ─── Payments / Subscription (stored in Supabase) ────────────

async function handleSavedCardsGet(req, env) {
  const user = await requireUser(req, env);
  const cards = await sb(env, `/saved_cards?user_id=eq.${user.id}&select=*`, { defaultVal: [] });
  return json({ cards: cards || [] });
}

async function handleSavedCardsAdd(req, env) {
  const user = await requireUser(req, env);
  const body = await req.json();
  const result = await sb(env, '/saved_cards', { method: 'POST', body: { user_id: user.id, ...body } });
  return json(result?.[0] || { ...body, user_id: user.id });
}

async function handlePaymentHistory(req, env) {
  const user = await requireUser(req, env);
  const payments = await sb(env, `/payment_history?user_id=eq.${user.id}&select=*&order=created_at.desc`, { defaultVal: [] });
  return json({ payments: payments || [] });
}

async function handleSubscriptionPlans(req, env) {
  return json({
    plans: [
      { name: 'free', display_name: 'Free', price: 0, currency: 'USD', features: ['3 scans per device', 'Basic OCR', 'English only'], limits: { scans_total: 3 } },
      { name: 'pro', display_name: 'Pro', price: 9.99, currency: 'USD', features: ['Unlimited scans', 'AI Enhancement', 'All languages', 'Priority OCR'], limits: { scans_total: -1 } },
      { name: 'max', display_name: 'Max', price: 12.99, currency: 'USD', features: ['Everything in Pro', 'Health recommendations', 'Diet analysis', 'Priority support'], limits: { scans_total: -1 } },
    ]
  });
}

async function handleSubscriptionInfo(req, env) {
  const user = await requireUser(req, env);
  const subs = await sb(env, `/user_subscriptions?user_id=eq.${user.id}&select=*`, { defaultVal: [] });
  if (Array.isArray(subs) && subs.length > 0) return json(subs[0]);
  return json({ user_id: user.id, plan_name: 'free', status: 'active', started_at: new Date().toISOString() });
}

async function handleSubscriptionSelect(req, env) {
  const user = await requireUser(req, env);
  const body = await req.json();
  const existing = await sb(env, `/user_subscriptions?user_id=eq.${user.id}&select=id`, { defaultVal: [] });
  if (Array.isArray(existing) && existing.length > 0) {
    const result = await sb(env, `/user_subscriptions?user_id=eq.${user.id}`, { method: 'PATCH', body: { plan_name: body.plan_name, status: 'active' } });
    return json(result?.[0] || { user_id: user.id, plan_name: body.plan_name, status: 'active' });
  }
  const result = await sb(env, '/user_subscriptions', { method: 'POST', body: { user_id: user.id, plan_name: body.plan_name, status: 'active' } });
  return json(result?.[0] || { user_id: user.id, plan_name: body.plan_name, status: 'active' });
}

// ─── Stripe Integration ──────────────────────────────────────

const STRIPE_PLANS = {
  pro:  { price_cents: 999,  name: 'Fooder Pro' },
  max:  { price_cents: 1299, name: 'Fooder Max' },
};

async function handleStripeCheckout(req, env) {
  const user = await requireUser(req, env);
  const body = await req.json();
  const plan = body.plan || 'pro';
  const planInfo = STRIPE_PLANS[plan];
  if (!planInfo) return json({ error: 'Invalid plan' }, 400);

  // Create Stripe Checkout Session via Stripe API
  const stripeRes = await fetchWithTimeout('https://api.stripe.com/v1/checkout/sessions', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${env.STRIPE_SECRET_KEY}`,
      'Content-Type': 'application/x-www-form-urlencoded',
    },
    body: new URLSearchParams({
      'mode': 'subscription',
      'customer_email': user.email,
      'line_items[0][price_data][currency]': 'usd',
      'line_items[0][price_data][unit_amount]': String(planInfo.price_cents),
      'line_items[0][price_data][recurring][interval]': 'month',
      'line_items[0][price_data][product_data][name]': planInfo.name,
      'line_items[0][quantity]': '1',
      'success_url': 'https://menuocr.app/success?session_id={CHECKOUT_SESSION_ID}',
      'cancel_url': 'https://menuocr.app/cancel',
      'metadata[user_id]': user.id,
      'metadata[plan]': plan,
    }).toString(),
  }, 15000);

  if (!stripeRes.ok) {
    console.error('Stripe error:', await stripeRes.text());
    // Still record the selection even if Stripe fails
    await sb(env, '/user_subscriptions', {
      method: 'POST', body: { user_id: user.id, plan_name: plan, status: 'active' },
    });
    return json({ success: true, plan, fallback: true });
  }

  const session = await stripeRes.json();

  // Record subscription
  const existing = await sb(env, `/user_subscriptions?user_id=eq.${user.id}&select=id`, { defaultVal: [] });
  if (Array.isArray(existing) && existing.length > 0) {
    await sb(env, `/user_subscriptions?user_id=eq.${user.id}`, { method: 'PATCH', body: { plan_name: plan, status: 'active', stripe_session_id: session.id } });
  } else {
    await sb(env, '/user_subscriptions', { method: 'POST', body: { user_id: user.id, plan_name: plan, status: 'active', stripe_session_id: session.id } });
  }

  return json({ success: true, checkout_url: session.url, session_id: session.id, plan });
}

async function handleStripeWebhook(req, env) {
  // In production, verify Stripe signature. For now, just log.
  const body = await req.text();
  console.log('Stripe webhook received:', body.substring(0, 200));
  return json({ received: true });
}

// ─── Full Profile / Addresses ────────────────────────────────

async function handleFullProfile(req, env) {
  const user = await requireUser(req, env);
  const [profile, addresses, subscription] = await Promise.all([
    sb(env, `/app_profiles?user_id=eq.${user.id}&select=*`, { defaultVal: [] }),
    sb(env, `/user_addresses?user_id=eq.${user.id}&select=*`, { defaultVal: [] }),
    sb(env, `/user_subscriptions?user_id=eq.${user.id}&select=*`, { defaultVal: [] }),
  ]);
  return json({
    profile: Array.isArray(profile) && profile.length > 0 ? profile[0] : { user_id: user.id, full_name: user.name, email: user.email },
    addresses: addresses || [],
    subscription: Array.isArray(subscription) && subscription.length > 0 ? subscription[0] : { plan_name: 'free', status: 'active' },
  });
}

async function handleProfileUpdate(req, env) {
  const user = await requireUser(req, env);
  const body = await req.json();
  const existing = await sb(env, `/app_profiles?user_id=eq.${user.id}&select=id`, { defaultVal: [] });
  if (Array.isArray(existing) && existing.length > 0) {
    await sb(env, `/app_profiles?user_id=eq.${user.id}`, { method: 'PATCH', body });
  } else {
    await sb(env, '/app_profiles', { method: 'POST', body: { user_id: user.id, ...body } });
  }
  return json({ message: 'Profile updated' });
}

async function handleAddresses(path, method, req, env) {
  const user = await requireUser(req, env);
  const parts = path.split('/');
  const addressId = parts.length > 3 ? parts[3] : null;

  if (method === 'GET') {
    const addresses = await sb(env, `/user_addresses?user_id=eq.${user.id}&select=*`, { defaultVal: [] });
    return json(addresses || []);
  }
  if (method === 'POST') {
    const body = await req.json();
    const result = await sb(env, '/user_addresses', { method: 'POST', body: { user_id: user.id, ...body } });
    return json(result?.[0] || body);
  }
  if (method === 'PUT' && addressId) {
    const body = await req.json();
    const result = await sb(env, `/user_addresses?id=eq.${addressId}&user_id=eq.${user.id}`, { method: 'PATCH', body });
    return json(result?.[0] || body);
  }
  if (method === 'DELETE' && addressId) {
    await sb(env, `/user_addresses?id=eq.${addressId}&user_id=eq.${user.id}`, { method: 'DELETE', prefer: 'return=minimal' });
    return json({ message: 'Address deleted' });
  }
  return json({ error: 'Method not allowed' }, 405);
}

async function handleChangePassword(req, env) {
  const token = req.headers.get('Authorization')?.replace('Bearer ', '');
  const body = await req.json();
  const res = await fetch(`${env.SUPABASE_URL}/auth/v1/user`, {
    method: 'PUT',
    headers: { Authorization: `Bearer ${token}`, apikey: env.SUPABASE_SERVICE_KEY, 'Content-Type': 'application/json' },
    body: JSON.stringify({ password: body.new_password }),
  });
  if (!res.ok) return json({ error: 'Password change failed' }, 400);
  return json({ message: 'Password changed', password_changed_at: new Date().toISOString() });
}

async function handleReferral(path, method, req, env) {
  const user = await requireUser(req, env);
  if (method === 'GET') {
    return json({ referral_code: user.id.substring(0, 8).toUpperCase(), referral_count: 0, referral_link: `https://menuocr.app/ref/${user.id.substring(0, 8)}`, pending_referrals: 0 });
  }
  if (method === 'POST') {
    const body = await req.json();
    return json({ message: `Referral code ${body.referral_code} applied` });
  }
  return json({ error: 'Not found' }, 404);
}


// ─── Notifications & Recent Scans ────────────────────────────

async function handleNotificationsGet(req, env) {
  const user = await requireUser(req, env);
  const notifications = await sb(env, `/user_notifications?user_id=eq.${user.id}&select=*&order=created_at.desc&limit=50`, { defaultVal: [] });
  return json({ notifications: notifications || [] });
}

async function handleNotificationsCreate(req, env) {
  const user = await requireUser(req, env);
  const body = await req.json();
  const record = {
    user_id: user.id,
    type: body.type || 'info',
    title: body.title || 'Notification',
    message: body.message || '',
    read: false,
  };
  const result = await sb(env, '/user_notifications', { method: 'POST', body: record });
  return json(result?.[0] || record);
}

async function handleRecentScansGet(req, env) {
  const user = await requireUser(req, env);
  const scans = await sb(env, `/scan_history?user_id=eq.${user.id}&select=*&order=created_at.desc&limit=50`, { defaultVal: [] });
  return json({ scans: scans || [] });
}

async function handleRecentScansCreate(req, env) {
  const user = await requireUser(req, env);
  const body = await req.json();
  const record = {
    user_id: user.id,
    image_key: body.image_key || '',
    dish_count: body.dish_count || 0,
    status: body.status || 'completed',
  };
  const result = await sb(env, '/scan_history', { method: 'POST', body: record });

  // Also create a notification for this scan
  await sb(env, '/user_notifications', {
    method: 'POST',
    body: {
      user_id: user.id,
      type: 'scan',
      title: 'Scan Complete',
      message: `Menu scanned with ${record.dish_count} dish${record.dish_count !== 1 ? 'es' : ''} detected.`,
      read: false,
    },
  });

  return json(result?.[0] || record);
}


// ═══════════════════════════════════════════════════════════════
// AUTH PROXY — so clients never need the anon/service key directly
// Uses SUPABASE_SERVICE_KEY server-side for all GoTrue calls
// ═══════════════════════════════════════════════════════════════

async function handleProxyAuthSignup(req, env) {
  const body = await req.json();
  const res = await fetch(`${env.SUPABASE_URL}/auth/v1/signup`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', apikey: env.SUPABASE_SERVICE_KEY },
    body: JSON.stringify({ email: body.email, password: body.password }),
  });
  const data = await res.json();
  return json(data, res.status);
}

async function handleProxyAuthSignin(req, env) {
  const body = await req.json();
  const res = await fetch(`${env.SUPABASE_URL}/auth/v1/token?grant_type=password`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', apikey: env.SUPABASE_SERVICE_KEY },
    body: JSON.stringify({ email: body.email, password: body.password }),
  });
  const data = await res.json();
  return json(data, res.status);
}

async function handleProxyAuthApple(req, env) {
  const body = await req.json();
  const res = await fetch(`${env.SUPABASE_URL}/auth/v1/token?grant_type=apple`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', apikey: env.SUPABASE_SERVICE_KEY },
    body: JSON.stringify(body),
  });
  const data = await res.json();
  return json(data, res.status);
}

async function handleProxyAuthSignout(req, env) {
  const token = req.headers.get('Authorization')?.replace('Bearer ', '');
  if (!token) return json({ error: 'No token' }, 401);
  const res = await fetch(`${env.SUPABASE_URL}/auth/v1/logout`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
      apikey: env.SUPABASE_SERVICE_KEY,
    },
  });
  return json({ message: 'Signed out' }, res.ok ? 200 : res.status);
}

async function handleProxyAuthRecover(req, env) {
  const body = await req.json();
  const res = await fetch(`${env.SUPABASE_URL}/auth/v1/recover`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', apikey: env.SUPABASE_SERVICE_KEY },
    body: JSON.stringify({ email: body.email }),
  });
  const data = await res.text();
  return new Response(data, { status: res.status, headers: { 'Content-Type': 'application/json' } });
}


// ─── Utility ─────────────────────────────────────────────────

function arrayBufferToBase64(buffer) {
  const bytes = new Uint8Array(buffer);
  let binary = '';
  for (let i = 0; i < bytes.byteLength; i++) binary += String.fromCharCode(bytes[i]);
  return btoa(binary);
}
