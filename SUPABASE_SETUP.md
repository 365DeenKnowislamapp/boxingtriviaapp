# Supabase Setup — Baseball Trivia Leaderboard

The app runs fine without Supabase (it falls back to a per-device local leaderboard).
Do this to enable a **global** leaderboard shared by all players.

## 1. Create the project
- New project name: **asf-baseball-trivia**
- Pick a region close to your players and save the database password somewhere safe.

## 2. Create the table + policies
Open **SQL Editor** and run this:

```sql
-- Leaderboard for Baseball Trivia
create table if not exists public.leaderboard (
  id          bigint generated always as identity primary key,
  name        text not null,
  score       integer not null,
  level       text,
  is_daily    boolean default false,
  is_pro      boolean default false,
  created_at  timestamptz default now()
);

-- Turn on Row Level Security
alter table public.leaderboard enable row level security;

-- Anyone may read the leaderboard
create policy "read_leaderboard"
  on public.leaderboard for select
  to anon
  using (true);

-- Anyone may add their own score (insert only)
create policy "insert_leaderboard"
  on public.leaderboard for insert
  to anon
  with check (true);

-- Helpful index for the top-scores query
create index if not exists leaderboard_score_idx
  on public.leaderboard (score desc);
```

> The app reads with `select *` and, when inserting, automatically retries **without**
> `is_pro` if that column doesn't exist — so an older table won't break it. But the
> schema above is the intended one (it powers the Pro 👑 leaderboard tab).

## 3. Get your keys
**Project Settings → API:**
- **Project URL** → use for `VITE_SUPABASE_URL`
- **Project API keys → `anon` `public`** — copy the long **`eyJ...`** JWT → use for `VITE_SUPABASE_ANON_KEY`

⚠️ **Key gotchas (same as the other ASF apps):**
- Use the **legacy `anon` public** key that looks like `eyJhbGci...` (a JWT).
- Do **not** use a `sb_publishable_...` style key.
- **Never** put the **`service_role`** key in the app — it bypasses RLS and is a security risk.

## 4. Put the keys in Vercel
Add `VITE_SUPABASE_URL` and `VITE_SUPABASE_ANON_KEY` in
**Vercel → Settings → Environment Variables (Production)**, then **redeploy**.

## 5. Test
Play a game → **Leaderboard** → submit a name. Open the site in another browser/device —
your score should appear there too. If it only shows locally, re-check the two env vars and
that you **redeployed** after adding them.
