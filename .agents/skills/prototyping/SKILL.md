---
name: prototyping
description: Resolves a paper-wayfinder work:prototype ticket by proposing candidates and converging on them with the scientist in-chat — stage:outline settles the paper's structure, stage:paragraph drafts one paragraph's prose. Use when asked to prototype, sketch, or produce candidates for a paper's outline/section structure, or to draft/workshop a paragraph for the manuscript, or to resolve a stage:outline or stage:paragraph ticket/issue.
---

# Prototyping
Prototyping raises the fidelity of the discussion by making a cheap, rough and concrete artifact to react to - an outline structure, a paragraph. 

Resolves a **`work:prototype`** ticket from [`paper-wayfinder`](../paper-wayfinder/SKILL.md)'s map — both `stage:outline` and `stage:paragraph` share this one resolver, on the claim that judging a finished sketch is far easier than specifying the exact wording up front. 
`stage:outline` runs entirely within this skill (the four-tier drill below). `stage:paragraph` hands the actual drafting off to [`scientific-writer`](../scientific-writer/SKILL.md) — a standalone drafting skill with its own house-style and AI-writing-smell checks, reusable outside a ticket entirely.

Read the ticket's `stage:` label to pick a branch below — `stage:outline` runs [The loop](#the-loop) directly; `stage:paragraph` hands off to `scientific-writer`'s own version of the same shape.

## Hard guardrail: zero tracker interaction

This skill never runs `git commit`, never edits a file under `sections/`, never opens a pull request, and never posts an issue comment or otherwise touches its ticket. Every candidate round is shown directly in the chat turn; the scientist reacts in-session. Posting the converged result and closing the ticket is entirely [`paper-wayfinder`](../paper-wayfinder/SKILL.md)'s job, done once this skill stops — see its "Confirm before committing" step.

## The loop

Propose 2-5 structurally distinct candidates, shown directly in the chat turn (labelled A/B/C…) and specify **how each prototype is different from one another**.  Stop and wait for a reaction:  Fold that reaction into a refined round — narrower and more concrete than the last, not a repeat of the same spread — and show it. Repeat until the scientist converges. Convergence, not a fixed round count, ends the loop — never advance on your own judgment of "good enough," only an explicit pick or approval.

1. **Judged, not authored.** Candidates are cheap and rough by design — the point is giving the scientist something concrete to react to, fast, not a polished output. Spend effort on making each round's candidates *distinct*, not on finishing any one of them.
2. **Genuinely different, not variations.** Every candidate in a round must independently answer the open question via a different structural or angle choice. Two candidates that read as the same idea reworded is one candidate, not two.

## `stage:outline`: the paper's structure

Settles the paper's paragraph breakdown and every paragraph's intent, whole-paper. Read the ticket's `## Question` and the map's Destination/Notes. No outline is ever authored solo into the ticket body; the ticket's body stays the plain `## Question` throughout, and this skill's final converged result is what `paper-wayfinder` posts as the resolution comment when it closes the ticket.

### Four tiers, depth-first

The outline resolves top-down through four tiers, each narrower than the last:

1. **Whole paper** — the section breakdown.
2. **Section** — that section's paragraph breakdown.
3. **Subsection** — a section's subsection breakdown, *only* when the section actually has subsections. Notice this during the section tier's round, from the shape of the candidates themselves — don't ask the scientist whether subsections exist unless a round leaves it genuinely ambiguous. Skip straight to the paragraph tier for sections without subsections.
4. **Paragraph** — the floor tier: what each paragraph contains.

Resolve **depth-first, one branch at a time**: pick a section, drill it all the way to its paragraphs (through its subsections if it has any) before starting the next section. Never breadth-first across sections at the same tier — a paper with three sections isn't three parallel section-breakdown loops, it's one section's whole branch finished, then the next.

Run [The loop](#the-loop) above on whatever tier scope is currently open (the whole paper, one section, one subsection, one paragraph). Once a tier converges, **explicitly ask before zooming in** — "ready to zoom into `<child scope>`?" — and wait for a yes. Never auto-continue to the next tier just because the current one converged; the scientist may want to sit with a decision, revisit a sibling, or stop for the session.

### Floor tier output

At the paragraph tier, a converged candidate is **bullet points describing what's in the paragraph** — the claims it makes, the evidence or examples it cites, the move it makes relative to the paragraph before it — not a single one-line intent and not prose. This is richer than a one-liner on purpose: still upstream of actual sentences, but enough for the `stage:paragraph-context` → `stage:paragraph` handoff to draft from without re-deciding content.

### Rules

3. **Depth-first, gated zoom.** Finish a branch before starting its sibling; never move to a child tier without the scientist's explicit go-ahead on the "ready to zoom into `<child scope>`?" question above.
4. **Domain terms as they crystallize.** Invoke [Domain Modeling](../../../inbox/resources/matt_pockock_skills/domain-modeling/SKILL.md) alongside the drill if a round surfaces a term the paper's vocabulary hasn't pinned down yet.
5. **Stop once converged.** Once the scientist gives final sign-off on the fully converged outline — every section's (and subsection's) paragraph breakdown, and every paragraph's bullet points — stop. Take no tracker action of any kind, direct or indirect; `paper-wayfinder` takes it from here.

## `stage:paragraph`: one paragraph's prose
Use [`scientific-writer`](../scientific-writer/SKILL.md), to draft publishable scientific paragraphs. 
