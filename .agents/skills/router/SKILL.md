---
name: skills
description: Index of this repo's user-invoked skills — what each does and when to reach for it.
disable-model-invocation: true
---

# Skills

- [paper-wayfinder](../paper-wayfinder/SKILL.md) — plans and charts a paper as its own map of decision/draft tickets, self-contained (not a thin wrapper around generic Wayfinder). Reach for this first when charting a paper or picking up its next ticket. As of 2026-08-11, reconciled from the "v2" fork that had briefly diverged from this canonical version — see its own "gotten wrong before" section.
- [prototyping](../prototyping/SKILL.md) — resolves `work:prototype` tickets, branching on `stage:`: `stage:outline` (cheap, rough, structurally distinct outline/paragraph-breakdown candidates, drilled depth-first through four tiers, run directly by this skill) and `stage:paragraph` (hands the ticket's Brief/Context to `scientific-writer` as intent and returns its converged paragraph). Zero tracker interaction either way — hands its converged result back to `paper-wayfinder` for posting; also invocable directly for ad hoc, untracked prototyping. Merged what used to be two separate skills, `paper-outline-draft` and `scientific-writer`, then split `scientific-writer` back out same-day (2026-08-11) — see its own entry below. Model-invocable (as of 2026-08-11) — unlike most skills in this list, it can fire on its own trigger phrases, not only by name.
- [scientific-writer](../scientific-writer/SKILL.md) — drafts one paragraph's prose as a whole (2-5 paragraph candidates), with house style (`references/house_style.md`) and AI-writing-smell checks (`../reviewer/references/AI_smells.md`) baked silently into candidate generation instead of a separate review round-trip. Pure drafting, no ticket/tracker awareness — reusable standalone for ad hoc prose, and `prototyping`'s `stage:paragraph` resolver hands it every paragraph ticket's intent. Split back out of `prototyping` same-day as the merge that had absorbed it (2026-08-11).
- [reviewer](../reviewer/SKILL.md) — critiques paragraph candidates against `references/AI_smells.md` and the journal writing-guidelines ticket; never rewrites. No longer wired into any active pipeline skill since `paragraph-draft`'s Agent Team (its former caller) was retired (2026-08-11) — reusable standalone.
- [style-review](../style-review/SKILL.md) — checks a drafted paragraph against `writing-style.md` and the journal writing-guidelines ticket, flagging violations without rewriting. Left as-is pending a dedicated cleanup pass; its former sibling in `paragraph-draft`'s team, `paragraph-draft` itself, was retired 2026-08-11.
- [kill-your-darlings](../kill-your-darlings/SKILL.md) — grilling-based cutting pass: prune a wide field of ideas, or choose one complete version among alternatives.
- [caveman](../caveman/SKILL.md) — ultra-compressed, terse communication register (multiple intensity levels), auto-triggering rather than invoked by name. Standalone since `paragraph-draft`'s Agent Team (its former user) was retired (2026-08-11).
- [humanizer](../humanizer/SKILL.md) — rewrites text to remove AI-writing patterns (inflated symbolism, promotional language, em dash overuse, and more), auto-triggering rather than invoked by name. Standalone — was the source content for the `reviewer` skill's `AI_smells.md` (see `wiki/log.md`'s 2026-08-10 entry).

## Generic matt_pocock_skills, installed directly

The following are unmodified copies of skills also captured as reference resources under [`inbox/resources/matt_pockock_skills/`](../../../inbox/resources/matt_pockock_skills/) — placed directly under `.Codex/skills/` (added via upload, bypassing the normal skill-update flow) so they're invocable in this repo without a paper-specific wrapper. Prefer the paper-specific skills above when one exists for the task; reach for these when the task is general-purpose (any grilling session, any handoff) rather than paper-writing-specific.

- [Codex-handoff](../Codex-handoff/SKILL.md) — hands the current conversation off to a fresh background agent that picks up the work immediately.
- [domain-modeling](../domain-modeling/SKILL.md) — builds and sharpens a project's domain model (terminology, glossary, ADRs) as decisions crystallize.
- [grill-me](../grill-me/SKILL.md) — runs a `/grilling` session: a relentless interview to sharpen a plan or design.
- [grill-with-docs](../grill-with-docs/SKILL.md) — runs a `/grilling` session using `/domain-modeling`, so ADRs and a glossary get written as it goes.
- [grilling](../grilling/SKILL.md) — the underlying interview mechanic `grill-me`/`grill-with-docs` invoke: work the frontier of settled-enough questions round by round until reaching shared understanding.
- [handoff](../handoff/SKILL.md) — compacts the current conversation into a handoff document, saved to the OS temp directory, for another agent to pick up.
- [prototype](../prototype/SKILL.md) — builds throwaway code (a logic demo or a UI-variant set) to answer a design question before committing to an approach; `prototyping` above is explicitly self-contained rather than wrapping this generic skill.
- [to-spec](../to-spec/SKILL.md) — turns the current conversation into a spec and publishes it to the project issue tracker; synthesis only, no interview.
- [to-tickets](../to-tickets/SKILL.md) — breaks a plan, spec, or conversation into tracer-bullet tickets with blocking edges, published to the configured tracker.
- [wayfinder](../wayfinder/SKILL.md) — generic version of `paper-wayfinder`: plans work too large for one session as a shared map of decision tickets, worked one at a time.
- [writing-for-agents](../writing-for-agents/SKILL.md) — reference for writing any document an agent consumes (a skill, `AGENTS.md`/`AGENTS.md`). Use when creating or editing skills.

## Adding a skill

New skill → new `.Codex/skills/<name>/SKILL.md`, written per [writing-for-agents](../../../inbox/resources/matt_pockock_skills/writing-for-agents/SKILL.md) (and [SKILL-MECHANICS](../../../inbox/resources/matt_pockock_skills/writing-for-agents/SKILL-MECHANICS.md) for frontmatter and the invocation choice). Default to user-invoked (`disable-model-invocation: true`); switch to model-invoked only when the skill must fire on its own or another skill needs to reach it. Add a line above for it.
