---
name: style-review
description: Check a drafted paragraph against this project's writing-style.md and journal writing-guidelines research ticket, flagging concrete violations. Use when asked to check, review, or flag style issues in a manuscript draft.
disable-model-invocation: true
---

# Style Review

Checks drafted text against this project's codified style rules — `writing-style.md` and the journal writing-guidelines research ticket — and reports violations. It does not rewrite the text and does not judge the paragraph's content or argument; that's the reviewer's own accept/reject call and [paragraph-draft](../paragraph-draft/SKILL.md)'s own self-critique, both out of scope here. This skill is narrower: is the prose in front of you consistent with the rules the project has already settled on.

## Precondition

If `writing-style.md` doesn't exist yet in the project, stop and say so plainly — this skill checks against it, it doesn't create it. Point at [Editorial Taste and Style](../../../wiki/concepts/editorial-taste-and-style.md) for how to start one, and don't attempt a review from memory or general style sense instead.

## Process

1. Read `writing-style.md` in full, and the journal writing-guidelines research ticket linked from the paragraph's map — both are rule sources, not just one.
2. Read the text under review: a paragraph-draft ticket's posted candidate versions, or pasted/attached text if no ticket is involved.
3. Check each candidate against every rule in both sources. A rule that doesn't apply to this paragraph (a figure-caption convention on a paragraph with no figure) is skipped, not flagged.
4. Report violations one by one: quote the offending text, name the specific rule it breaks, and say which source the rule came from. A candidate with no violations gets said explicitly — "no style issues found" — not silence.

Done when every candidate has been checked against every rule in both sources — a spot-check is not a style review.

## Where this plugs in

If the text under review is a paragraph-draft ticket's candidate versions, post the report as a comment on that ticket rather than only in chat — it becomes part of the reviewer's record the same way [paragraph-draft](../paragraph-draft/SKILL.md)'s own rounds do. Do not post an approval or rejection yourself; a style violation is input to the human reviewer's accept/reject decision, not a decision of its own.
