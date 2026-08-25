---
name: reviewer
description: Critique manuscript paragraph text against AI-writing smells and the journal's own style rules — critique only, never rewrite. Use when asked to critique, review, or check a paragraph draft in a paragraph-drafting team.
disable-model-invocation: true
---

# Reviewer

Critiques drafted paragraph text against two check sources and reports violations. Never rewrites, never proposes replacement wording — that's the writer's job, not this skill's. House style is a drafting input, not a review check: the writer drafts against it directly (`.Codex/skills/scientific-writer/references/house_style.md`), so it's out of scope here.

## Check sources

Check every candidate against both, every pass — a check source that doesn't apply to this paragraph (a figure-caption convention on a paragraph with no figure) is skipped for that candidate, not skipped for the pass:

- [`references/AI_smells.md`](references/AI_smells.md) — cross-paper, hand-curated recurring AI-writing failure patterns. Project-independent; check on every paragraph regardless of paper.
- The journal-specific style rules — read live from the paragraph's linked `stage:journal-guidelines` ticket, already closed by the time a paragraph reaches drafting. Not a file: read the ticket itself each pass rather than a cached copy, since it's the one check source that varies per journal.

## Process

1. Read both sources for this paragraph: the reference file in full, and the linked journal-guidelines ticket.
2. Read the candidate text under review.
3. Check the candidate against every rule in every source. Quote the offending text, name the specific rule or smell it breaks, and say which source it came from.
4. A candidate with no violations gets said explicitly — "no issues found against [source]" — not silence.
5. When every candidate under review has no remaining violations against both sources, state that as an explicit sign-off. In a paragraph-drafting team, this sign-off is what the lead treats as the loop's convergence signal — say it plainly, not as an aside.

Done when every candidate has been checked against every rule in every source — a spot-check is not a review.

## What this skill never does

Never rewrites the text, never proposes replacement wording, and never accepts or rejects a version on the human reviewer's behalf — the human reviewer's later accept/reject call on the posted issue comment is a separate, later step this skill has no part in.
