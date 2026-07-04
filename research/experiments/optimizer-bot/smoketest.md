# Demand smoke test — "Optimal" (optimizer habit tool)

Fake-door landing page to test **demand + habit + soft willingness-to-pay** for the
optimizer-habit positioning (chosen because round 1/2 showed answer quality isn't a moat —
so we test whether people *want it and would use it often*, not whether answers are better).

- Page: `landing/index.html` (self-contained; deploy on Netlify).
- Analytics: PostHog (project "Rouse Alarm"), events namespaced `optbot_*` so they filter
  cleanly. Email capture via Netlify Forms (`data-netlify`), so raw emails stay out of analytics.

## The funnel (PostHog events)
1. `optbot_landing_view` — page load
2. `optbot_plan_click` `{plan: free|pro}` — tapped a plan (WTP proxy)
3. `optbot_cta_click` `{plan}` — clicked the hero "Get early access"
4. `optbot_email_submit` `{plan}` — **primary demand signal**
5. `optbot_frequency` `{freq: daily|weekly|monthly|rarely}` — **the habit signal** (also set as a
   person property `habit_frequency`)

## Success / kill gates (decide BEFORE reading, so we don't rationalize)
| Signal | Metric | Keep | Kill |
|---|---|---|---|
| **Demand** | `landing_view → email_submit` | ≥ 10% | < 5% |
| **Habit (core bet)** | share of `optbot_frequency` = daily **or** weekly | ≥ 40% | < 25% |
| **WTP (soft)** | of plan-clickers, share choosing `pro` | ≥ 25% | < 10% |

The **habit gate is the one that matters most**: a tool people need only monthly can't retain,
no matter how good signup looks. If demand passes but habit fails → it's a novelty, not a habit
(revisit the viral-funnel or high-stakes wedge). If both pass → build a real prototype and test
activation/retention for real.

## Traffic (you drive it — the env can't manufacture it)
Aim for **≥ 250 unique visitors** (usable CI on email conversion) and **≥ 50 survey responses**
(readable habit split). Warm ICP channels:
- Reddit: r/frugal, r/BuyItForLife, r/personalfinance, r/onebag, r/DataHoarder-adjacent optimizer subs
  (respect self-promo rules — post as "I built this, would you use it?", not an ad).
- HN "Show HN", relevant Discords/X niches for optimizers.
- Keep source honest: use one link per channel (`?ref=frugal` etc.) so conversion is attributable.

## Reading it in PostHog
- Funnel: `optbot_landing_view → optbot_cta_click → optbot_email_submit`.
- Habit: bar of `optbot_frequency` broken down by `freq`.
- WTP: `optbot_plan_click` broken down by `plan`.
- (I can pull these numbers directly via the PostHog MCP once traffic has run.)

## Notes
- Events land in the existing "Rouse Alarm" project (namespaced `optbot_`). If you want isolation,
  spin up a fresh PostHog project and swap the token in `index.html`.
- This is a *concept* test — the page says "a concept we're validating." Deliver on the waitlist
  promise (email people) or explicitly sunset it; don't leave a fake door open forever.
