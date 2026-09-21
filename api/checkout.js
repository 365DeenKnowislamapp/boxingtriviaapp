// Vercel serverless function: create a Stripe Checkout session for Boxing Trivia Pro.
// Env vars (set in Vercel → Project → Settings → Environment Variables, then REDEPLOY):
//   STRIPE_SECRET_KEY  – your Stripe secret key (sk_live_… or sk_test_…)
//   STRIPE_PRICE_ID    – the Price ID for "Boxing Trivia Pro" ($9.99/year, recurring)

export default async function handler(req, res) {
  if (req.method !== 'POST') {
    res.setHeader('Allow', 'POST')
    return res.status(405).json({ error: 'Method not allowed' })
  }

  const secret = process.env.STRIPE_SECRET_KEY
  const price = process.env.STRIPE_PRICE_ID
  if (!secret || !price) {
    return res.status(500).json({ error: 'Stripe is not configured on the server.' })
  }

  try {
    const origin =
      req.headers.origin ||
      (req.headers.host ? `https://${req.headers.host}` : '')

    // Call Stripe's REST API directly (no SDK dependency needed).
    const body = new URLSearchParams()
    body.append('mode', 'subscription')
    body.append('line_items[0][price]', price)
    body.append('line_items[0][quantity]', '1')
    body.append('success_url', `${origin}/?pro=success`)
    body.append('cancel_url', `${origin}/?pro=cancelled`)
    body.append('allow_promotion_codes', 'true')

    const r = await fetch('https://api.stripe.com/v1/checkout/sessions', {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${secret}`,
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body,
    })

    const session = await r.json()
    if (!r.ok) {
      return res.status(400).json({ error: session.error?.message || 'Stripe error' })
    }
    return res.status(200).json({ url: session.url })
  } catch (e) {
    return res.status(500).json({ error: e.message || 'Server error' })
  }
}
