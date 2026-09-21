import React from 'react'
import { createRoot } from 'react-dom/client'
import App from './App.jsx'

/* ------------------------------------------------------------------ *
 * Storage shim: window.storage
 *   get/set/delete/list(key, shared=false)
 *   shared:false -> localStorage (per-device)
 *   shared:true  -> Supabase 'leaderboard' table when configured,
 *                   otherwise falls back to localStorage so the app
 *                   still runs offline / before Supabase is set up.
 * ------------------------------------------------------------------ */

const SB_URL = import.meta.env.VITE_SUPABASE_URL
const SB_KEY = import.meta.env.VITE_SUPABASE_ANON_KEY
const HAS_SUPABASE = Boolean(SB_URL && SB_KEY)

let sb = null
let sbInitPromise = null
function getSupabase() {
  if (!HAS_SUPABASE) return Promise.resolve(null)
  if (sb) return Promise.resolve(sb)
  if (!sbInitPromise) {
    sbInitPromise = import('@supabase/supabase-js')
      .then(({ createClient }) => { sb = createClient(SB_URL, SB_KEY); return sb })
      .catch((e) => { console.warn('Supabase init failed, using local fallback:', e); return null })
  }
  return sbInitPromise
}

const LS = {
  get(k) { try { const v = localStorage.getItem(k); return v == null ? null : { key: k, value: v } } catch { return null } },
  set(k, v) { try { localStorage.setItem(k, v); return { key: k, value: v } } catch { return null } },
  del(k) { try { localStorage.removeItem(k); return { key: k, deleted: true } } catch { return null } },
  list(prefix = '') {
    try {
      const keys = []
      for (let i = 0; i < localStorage.length; i++) {
        const k = localStorage.key(i)
        if (k && k.startsWith(prefix)) keys.push(k)
      }
      return { keys, prefix }
    } catch { return { keys: [], prefix } }
  }
}

/* Supabase-backed leaderboard. We treat the shared leaderboard as a table,
 * gracefully handling an older schema that may not have `is_pro`. */
const CONFIG = { supabase: HAS_SUPABASE }

async function sbInsertScore(row) {
  const client = await getSupabase()
  if (!client) throw new Error('no supabase')
  // Try full insert; if is_pro column is missing, retry without it.
  let { error } = await client.from('leaderboard').insert(row)
  if (error && /is_pro/i.test(error.message || '')) {
    const { is_pro, ...rest } = row
    ;({ error } = await client.from('leaderboard').insert(rest))
  }
  if (error) throw error
  return true
}

async function sbFetchScores() {
  const client = await getSupabase()
  if (!client) throw new Error('no supabase')
  // select * so a missing column never breaks the query
  const { data, error } = await client
    .from('leaderboard')
    .select('*')
    .order('score', { ascending: false })
    .limit(100)
  if (error) throw error
  return data || []
}

window.storage = {
  config: CONFIG,
  async get(key, shared = false) {
    if (shared && HAS_SUPABASE) {
      if (key === 'leaderboard') {
        try { return { key, value: JSON.stringify(await sbFetchScores()), shared: true } }
        catch (e) { console.warn('leaderboard fetch failed, local fallback', e); }
      }
    }
    const r = LS.get((shared ? 'shared:' : '') + key)
    return r ? { ...r, shared } : null
  },
  async set(key, value, shared = false) {
    if (shared && HAS_SUPABASE) {
      if (key === 'leaderboard:add') {
        try { await sbInsertScore(JSON.parse(value)); return { key, value, shared: true } }
        catch (e) { console.warn('leaderboard insert failed, local fallback', e); }
      }
    }
    return LS.set((shared ? 'shared:' : '') + key, value)
  },
  async delete(key, shared = false) { return LS.del((shared ? 'shared:' : '') + key) },
  async list(prefix = '', shared = false) { return LS.list((shared ? 'shared:' : '') + prefix) }
}

createRoot(document.getElementById('root')).render(<App />)
