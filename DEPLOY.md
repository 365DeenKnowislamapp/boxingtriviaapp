# Boxing Trivia — Deployment Guide

This is app #3 in the ASF family and deploys exactly like the Basketball and Football apps:
**GitHub → Vercel → GoDaddy DNS → Supabase (leaderboard) → Stripe (Pro).**
Do **not** touch the Basketball or Football projects while doing this.

The app works with zero backend (local leaderboard + Pro preview). The steps below turn on the
**global leaderboard** and **real Pro checkout**.

---

## 0. What's in this folder
```
asf-boxing-trivia/
├── index.html            ← app shell (dark bg, fonts, placeholder styling)
├── package.json          ← Vite + React + Supabase
├── vite.config.js        ← Vite config (base: './')
├── src/
│   ├── main.jsx          ← storage shim (localStorage + Supabase leaderboard)
│   └── App.jsx           ← the whole game + all 750 questions
├── api/
│   └── checkout.js       ← Stripe Checkout serverless function
├── DEPLOY.md             ← this file
└── SUPABASE_SETUP.md     ← leaderboard table SQL + keys
```
> Keep `src/` and `api/` as folders when you upload. Do not flatten them.

---

## 1. GitHub
1. Create a **new private repo**: `asf-boxing-trivia`.
2. Upload the **contents** of this folder (not the folder itself). Keep the `src/` and `api/` folders intact.
3. Commit.

> Editing later: use the GitHub pencil (✏️) to edit `src/App.jsx` in the browser.
> On Safari/iPad, make sure it saves as `App.jsx` and does **not** rename to `App-2.jsx`.

## 2. Vercel
1. **Add New → Project → Import** the `asf-boxing-trivia` repo.
2. Vercel auto-detects **Vite**. Leave build settings as detected
   (Build: `npm run build`, Output: `dist`). Deploy.
3. You'll get a `*.vercel.app` URL. Test it — the game is fully playable already
   (leaderboard will be local-only, Pro will say "not configured" until steps 4–5).

## 3. GoDaddy DNS (custom domain)
Point your domain (e.g. **boxingtriviaapp.com**) at Vercel:
- **A** record: `@` → `76.76.21.21`
- **CNAME** record: `www` → `cname.vercel-dns.com`

Then in **Vercel → Project → Settings → Domains**, add the domain and follow the verification prompt.
DNS can take a little while to propagate.

## 4. Supabase (global leaderboard)
Follow **SUPABASE_SETUP.md**. In short:
1. New project: `asf-boxing-trivia`.
2. Run the SQL in that file to create the `leaderboard` table + policies.
3. Copy the **Project URL** and the **legacy anon public key** (the long `eyJ...` JWT —
   **not** a `sb_publishable_...` key and **never** the `service_role` key).

## 5. Stripe (Pro — $29.99/year)
1. Create a **Product**: "Boxing Trivia Pro", **recurring**, **$29.99 / year**.
2. Copy the **Price ID** (`price_...`).
3. Copy your **Secret key** (`sk_live_...` for real payments, or `sk_test_...` to test).

## 6. Vercel environment variables → then REDEPLOY
In **Vercel → Project → Settings → Environment Variables** (Production), add:

| Name | Value |
|---|---|
| `VITE_SUPABASE_URL` | your Supabase Project URL |
| `VITE_SUPABASE_ANON_KEY` | the legacy `eyJ...` anon key |
| `VITE_STRIPE_CONFIGURED` | `1` |
| `STRIPE_SECRET_KEY` | `sk_live_...` (or `sk_test_...`) |
| `STRIPE_PRICE_ID` | `price_...` |

> ⚠️ After adding/changing env vars you **must redeploy** (Deployments → ⋯ → Redeploy).
> Vite only reads `VITE_*` values at build time.

## 7. Verify
- Hard-refresh the site after each deploy (mobile browsers cache aggressively).
- Play a game → **Leaderboard** → submit a name → it should appear for everyone.
- Tap **Unlock Pro** → it should send you to Stripe Checkout. Completing it returns to
  `/?pro=success` and the device unlocks Pro (👑). (`?pro=cancelled` just returns home.)

---

## How Pro works
Pro is **device-based**: after a successful Stripe checkout, Stripe redirects to `/?pro=success`
and the app stores `boxing_pro="1"` in that browser's local storage. That unlocks the Legends
level, 5 hints, 3 shields, the daily points bonus, and the Pro leaderboard badge on that device.

## Wiring the "Unlock Pro" button to Stripe (optional polish)
With the env vars set (`VITE_STRIPE_CONFIGURED=1`), the Pro modal shows **Continue to Checkout**.
To make that button call Stripe, POST to the serverless function and redirect to the returned URL:

```js
const r = await fetch('/api/checkout', { method: 'POST' })
const { url } = await r.json()
if (url) window.location.href = url
```
(The function is already deployed at `/api/checkout`. If you'd rather keep the current
device-preview behavior for launch, you can leave it as-is.)

## Local test before deploying
```
npm install
npm run build      # standard build → dist/
```
Or just double-click **Boxing-Trivia-PLAYABLE.html** for a fully offline preview.

## Featuring an athlete (built-in, no code archaeology)
Open `src/App.jsx`, find the `ATHLETE` object near the top, set `enabled: true`,
and fill in `name`, `handle`, `blurb`, `emoji`, `ctaLabel`, `ctaUrl`, and `accent`.
A promo card appears on the home screen. Swap the values any time for a new ambassador.
