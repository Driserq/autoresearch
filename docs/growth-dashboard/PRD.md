# PRD — Persona Growth Dashboard (working title)

**A mobile app that turns the content you save into personalized, trackable habits — so the stuff you learn actually changes how you live.**

Version 0.1 (concept spec) · 2026-07-10 · Companion doc: `viability-research.md`

---

## 0. Read this first — the one idea

You already have a growing pile of "watch later" content you never implement. Every self-help video is *someone else's* generic advice. The gap isn't information — it's **translation**: turning "drink more water / do deep work / journal at night" into *a change to your actual day, phrased in your words, tied to something you already do.*

**This app is a translation machine.** It holds a living model of *you* (persona), knows your goals, and when you feed it a piece of content, it converts that content into 1–3 concrete habits **fitted to your persona and stacked onto your existing routine** — then makes sure you actually do them.

Everything else in this document serves that one loop. If a feature doesn't strengthen the loop or fight the D30 churn cliff, it's cut.

> **Design north star:** *Retention is the product.* The research is blunt — this category is a graveyard, AI apps churn ~30% faster, and revenue is ~400× winner-take-most. We do not win on features. We win by being the one app in this space where people still *do the thing* in month three.

---

## 1. Problem

| | |
|---|---|
| **The pain** | Motivated people consume enormous amounts of self-improvement content and implement almost none of it. Saving feels like progress; nothing changes. |
| **Why it persists** | The intention-action gap: strong intentions produce action only ~53% of the time, and motivating harder barely moves behavior (R²≈.03). The leverage is in *structuring follow-through*, which no content tool does and every habit tool makes you do by hand. |
| **Why now** | AI can finally do the translation step — read a transcript, understand a persona, and author a fitted habit — at a quality that wasn't possible two years ago. |
| **The trap to avoid** | Becoming "another AI habit tracker." Those die on retention and economics. |

## 2. Who it's for (ICP)

**Primary user — "the content-overloaded self-improver" (people like you):**
- Motivated, growth-oriented, saves far more than they implement.
- Has a "watch later" / read-later graveyard they feel guilty about.
- Has *tried* habit trackers and abandoned them (blank-checklist fatigue, no connection to what they're learning).
- Willing to pay for something that actually works; skeptical because nothing has.

**Jobs to be done:**
- *"When I find a great video, help me actually turn it into a change in my life — not another saved link."*
- *"Help me see who I'm trying to become and whether I'm getting there."*
- *"Keep me doing the small things long enough that they stick."*

**Explicit non-goals for v1:** not for teams/coaches (that's a later B2B path), not a note-taking/PKM tool, not a social network. Resist all three — they dilute the loop.

## 3. The wedge & why it's defensible

**Wedge:** *Convert user-saved content into personalized implementation intentions anchored to the user's existing routines.*

Defensible because it bridges two camps that today never meet (see research doc):
- **Content tools** (NoteGPT, Readwise, Blinkist) capture knowledge → but never change behavior.
- **Habit trackers** (Habitica, Finch, Streaks) change behavior → but you author every habit by hand.

The bridge — *content in, fitted habit out* — is verified as unoccupied by the two closest AI competitors. The moat isn't the ingestion (that's commodity); it's the **persona-personalization + co-authoring quality** and the **retention system** wrapped around it.

> **Caveat carried from research:** the "wedge is open" finding is verified only against Rocky.ai and NoteGPT. **Action item before build:** hands-on teardown of Readwise Reader, Fabulous, Finch, and coaching bots to confirm none has shipped an "action" layer.

## 4. The core loop

```
   ┌─────────────┐     ┌──────────────┐     ┌───────────────┐     ┌──────────────┐     ┌────────────┐
   │  PERSONA    │ --> │   GOALS +    │ --> │    DIGEST     │ --> │   FITTED     │ --> │   TRACK    │
   │ materialize │     │  CHECKLIST   │     │   content     │     │   HABITS     │     │  & review  │
   │  who you are│     │ from goals   │     │ (link/text)   │     │ (co-authored)│     │ (do it)    │
   └─────────────┘     └──────────────┘     └───────────────┘     └──────────────┘     └─────┬──────┘
          ^                                                                                   │
          └───────────────────────  persona & dashboard update from evidence  ───────────────┘
```

1. **Persona** — the user materializes who they are and who they're becoming (skills, traits, current habits, values). This is the emotional hook *and* the personalization context.
2. **Goals → Checklist** — goals generate a starter set of trackable habits, so the checklist is never blank.
3. **Digest** — user pastes a link/text. The engine analyzes it *against the persona* and proposes 1–3 fitted habits.
4. **Fitted habits** — **user co-authors**: edits wording, picks the anchor routine, confirms. (This is a hard design rule — see §6.)
5. **Track & review** — do the habit; streaks, reminders, weekly review. Completion feeds evidence back into the persona/dashboard, closing the loop so the dashboard visibly *moves* as you change.

## 5. The digestion engine (the heart of the build)

**Input:** YouTube link, article URL, or pasted text.

**Pipeline:**
1. **Ingest** — extract transcript/text. (Commodity; not the differentiator. Resolve YouTube ToS/transcript-reliability first — see research §3.)
2. **Extract claims/advice** — pull the actionable recommendations from the content (distinct from mere summary — this is what separates us from NoteGPT).
3. **Personalize against persona** — for each recommendation, ask: does this fit this user's goals, current habits, and constraints? Discard what doesn't. Adapt what does.
4. **Author as implementation intentions** — convert each surviving recommendation into an *if-then* habit stacked onto an existing routine: *"After I [existing anchor], I will [tiny new behavior]."*
5. **Propose for co-authoring** — present 1–3 candidates. User edits/confirms. **Never auto-commit.**

**Quality bar (what "good" means):**
- Habits are *tiny* (Fogg-style), *specific*, *anchored*, and *phrased in the user's voice*.
- The engine says **"nothing here fits you right now"** when that's true. Restraint is a feature — dumping 10 habits per video recreates the graveyard.
- Cap: **max 1–3 new habits per digest**, and warn/soft-block when the user's active-habit count is already high (overload kills retention).

**Cost control (non-negotiable, from research §4):** cache transcripts; use a cheap model for extraction and a stronger model only for the personalization/authoring step; cap free-tier digests; keep persona context lean (summary + deltas, not full history) so token cost per digest stays far below per-user revenue.

## 6. Behavior-change design principles (the moat, not decoration)

Each principle maps to a verified research finding. This section *is* the retention strategy.

| Principle | What we build | Evidence |
|---|---|---|
| **Co-author, don't auto-generate** | User edits/confirms/rephrases every habit. We never silently commit a machine-written habit. | Self-formed implementation intentions have d=.65; AI-generated efficacy is *unproven*. Co-authoring inherits the effect. |
| **Implementation intentions** | Every habit is an if-then: "After X, I will Y." | d=.65 across 94 studies. |
| **Habit stacking** | Force every new habit to anchor onto an existing routine the user names. | Established Fogg/Clear anchoring pattern. |
| **Reminders** | Context/time-based reminders on every active habit. | Reminders ~3× daily-goal success (55% vs 18%). |
| **Tiny by default** | Habits start absurdly small; grow only after they stick. | Fogg Behavior Model — reduce required motivation. |
| **Restraint / anti-overload** | Cap active habits; the engine can say "not now." | Overload → the exact graveyard we're fighting. |
| **Streak recovery, not streak shame** | Missing a day offers a gentle "get back on" path, never a punishing reset-to-zero. | Loss-of-motivation is the category's churn driver; shame accelerates abandonment. |
| **Weekly review** | A short ritual: what stuck, what didn't, prune dead habits, celebrate persona movement. | Reflection + pruning sustains long-term engagement; keeps the dashboard honest. |
| **Visible identity progress** | Completions visibly move the persona dashboard ("you're becoming…"). | Identity-based motivation; the emotional hook that makes tracking feel meaningful. |

## 7. Feature set (MoSCoW)

**MUST (MVP — the loop, nothing else):**
- Persona setup (lightweight: a few skills/traits/current habits/goals — *not* an hour-long intake).
- Goal → starter checklist generation.
- Digestion engine: link/text → 1–3 co-authored, anchored, if-then habits.
- Habit tracking: daily check-off, streaks (with recovery), reminders.
- Basic persona dashboard that updates from completions.
- Weekly review ritual.

**SHOULD (v1.x):**
- Share-sheet ingestion (send a YouTube/article straight from another app — kills the friction of the graveyard).
- Habit editing/snoozing/retiring; overload warnings.
- Notification tuning; smart reminder timing.
- Digest history ("what I've implemented from what I watched").

**COULD (later):**
- Accountability (a buddy, a check-in, or lightweight social proof) — strong retention lever, but scope-heavy.
- Persona "evolution" timeline / before-after narrative.
- Multiple personas or life-areas.
- Voice-note digestion; podcast ingestion.

**WON'T (v1 — protect the wedge):**
- Team/coach features · full PKM/note-taking · social feed · in-app content library (we digest *their* content, we don't host a library).

## 8. Information architecture / key screens (described)

**Bottom nav — 3 tabs, deliberately minimal:**

1. **Today** *(the default landing — execution first)*
   - Today's habits as check-offs, grouped by anchor ("morning," "after work").
   - Streak state + gentle recovery prompt if a streak lapsed.
   - Prominent **"+ Digest something"** entry point.

2. **Dashboard** *(the persona — the emotional hook)*
   - "Who you're becoming": skills/traits/values as a living, visual map that moves with completions.
   - Goals and their linked habits; progress made visible.
   - Recent persona movement ("3 weeks of evening shutdown → 'Boundaries' trait strengthening").

3. **Digest** *(the wedge — the magic moment)*
   - Paste link / paste text / (v1.x) share-sheet inbox of saved content.
   - **The co-authoring screen:** proposed habits shown as editable if-then cards, each with an anchor picker and a "why this fits you" line referencing the persona. Accept / edit / dismiss per card.
   - Digest history: content → habits it produced → whether they stuck.

**Supporting flows:** onboarding (persona + first goal + *first digest as the aha-moment*), weekly review (a guided card stack), settings/notifications, paywall.

## 9. Onboarding (must deliver the aha in <5 minutes)

The activation moment is **the first digest**, not persona setup. Sequence:
1. **Quick persona** — 4–6 taps: pick a couple of focus areas, name 1–2 current routines (these become anchors), state one goal. Keep it under 90 seconds. (Long intake = drop-off.)
2. **First digest, immediately** — prompt: *"Paste a video or article you've been meaning to implement."* This is the wow. They watch their own saved content become a fitted habit.
3. **Commit one habit** — co-author and accept exactly one. Set its reminder. Done.
4. **Return hook** — reminder fires tomorrow; the loop begins.

> Activation metric: **% of new users who complete their first digest AND check off one habit the next day.** This single funnel predicts retention.

## 10. Data model (sketch)

- **Persona** — { skills[], traits[], values[], current_routines[] (anchors), constraints[] }. Lean summary kept for cheap digest context.
- **Goal** — { title, area, target, linked_habit_ids[] }.
- **Habit** — { if_then_text, anchor_routine, cadence, reminder, source_digest_id, state (proposed/active/retired), streak, history[] }.
- **Digest** — { source_url/text, extracted_recommendations[], proposed_habit_ids[], accepted_habit_ids[], created_at }.
- **Completion event** — { habit_id, timestamp } → feeds persona/dashboard updates.

## 11. Monetization

- **Model:** freemium → **annual-first subscription** (annual LTV ~4× and churn ~half of monthly, per research). Offer monthly but nudge annual.
- **Free tier:** limited digests/month + a capped number of active habits. Enough to feel the magic; not enough to live in it. (Also caps your AI cost exposure on non-payers.)
- **Paid tier:** unlimited/large digest allowance, unlimited habits, advanced reminders, weekly review insights, history.
- **Price anchor (directional):** self-improvement apps cluster ~$7.50–$16.42/mo on annual plans; target the higher end on annual to maximize LTV, and A/B against a weekly plan (broader-category data shows weekly can dominate outside Health & Fitness). *Do not* cite the refuted "$29/mo" or the refuted market-size figures externally.
- **Unit-economics guardrail:** per-digest AI cost must stay far below per-paid-user revenue. Model `(install→paid ~4–6%) × annual price − (per-digest cost × digests) − infra` **before** scaling spend. This spreadsheet is a gate, not a formality.

## 12. Success metrics

- **North-star:** *habits still being completed at D30/D60 per active user* (behavior sustained, not logins).
- **Activation:** % completing first digest + next-day check-off (§9).
- **Loop health:** digests → accepted habits ratio; accepted → completed ratio.
- **Retention:** D1 / D7 / D30 vs the category cliff (beating it is the entire thesis).
- **Economics:** install→paid %, per-digest cost, blended LTV vs CAC.
- **Efficacy signal:** do AI-co-authored habits get completed at a rate comparable to user-authored ones? (Instrument this from day one — it validates or kills the core assumption.)

## 13. Risks & mitigations

| Risk (from research) | Mitigation in this design |
|---|---|
| Category D30 churn / graveyard | Retention-as-product: reminders + stacking + streak recovery + weekly review + visible identity progress (§6). |
| Unit economics in a ~400× winner-take-most market | Annual-first pricing, tiered digest caps, cheap-model extraction / strong-model only for authoring, lean persona context (§5, §11). |
| AI-generated ≠ self-authored efficacy (unproven) | Co-authoring rule (§6); instrument completion-rate comparison (§12); prototype-test before scale. |
| Wedge less open than it looks | Competitive teardown before build (§3). |
| YouTube ToS / transcript reliability | Resolve legal + extraction strategy (official-less API, ASR fallback) before depending on it (research §3). |
| Overload recreating the graveyard | Hard cap on habits/digest and active habits; engine allowed to say "not now" (§5, §6). |

## 14. Open decisions (need your input)

1. **Ingestion legal strategy** — how comfortable are you depending on unofficial YouTube transcript extraction vs building ASR fallback? (affects cost + risk)
2. **Accountability in v1 or later?** — it's one of the strongest retention levers but the heaviest scope. MVP-cut for now; worth revisiting.
3. **Persona depth** — how rich should the initial persona be? (richer = better personalization but higher onboarding drop-off; I've defaulted to *lean*.)
4. **Platform** — native (Swift/Kotlin) vs cross-platform (React Native/Flutter/Expo) for the mobile build? Affects speed-to-first-prototype.
5. **The validation prototype** — before a full build, do you want a stripped test of *just* the core assumption (AI-co-authored habit vs generic habit → completion rate)? The research flags this as the highest-value next step.

## 15. Suggested roadmap

- **Phase 0 — Validate (weeks):** competitive teardown; ingestion legal/tech spike; **prototype the core assumption** (do co-authored habits get done more?); model unit economics.
- **Phase 1 — MVP:** the core loop end-to-end (§7 MUST). Ship to a tiny cohort of people like you. Instrument the north-star and efficacy signal.
- **Phase 2 — Retention hardening:** share-sheet ingestion, reminder tuning, weekly review polish, streak recovery — everything that fights D30.
- **Phase 3 — Monetize & scale:** annual-first paywall, pricing A/Bs, only scale spend once the unit-economics gate is green.
- **Phase 4 — Expand:** accountability, deeper persona evolution, more content types.

---

*This is a concept spec, not a final design. It deliberately trades breadth for a defensible wedge and a retention obsession, because the research says that is the only version of this idea that survives. Companion: `viability-research.md`.*
