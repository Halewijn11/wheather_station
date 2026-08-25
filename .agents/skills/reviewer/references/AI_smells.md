# AI Writing Smells

Cross-paper, hand-curated checklist of recurring AI-writing failure patterns for the `reviewer` skill to check paragraph candidates against — see `wiki/concepts/paragraph-drafting-team.md` for what this file is and why it's split from `house_style.md` (a drafting input under `scientific-writer/references/`, not a reviewer check source). Project-independent: check every candidate against this file regardless of which paper it's for.

Adapted from the `humanizer` skill (`.claude/skills/humanizer/SKILL.md`), itself based on [Wikipedia:Signs of AI writing](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing). `humanizer` rewrites text to remove these patterns; this file exists to **detect and name** them for a reviewer who never rewrites — point at the offending text and the specific smell it matches, and leave the fix to the writer.

## How to use this file

For each candidate, scan for every pattern below. When a pattern matches, quote the offending text and name the specific numbered smell (e.g. "§7 AI vocabulary: *delve*"). A single hit on a common pattern (§7, §14, §19) is worth flagging but not a strong signal by itself — see **What NOT to flag** before treating anything as a verdict. Look for **clusters**: several patterns co-occurring in the same paragraph is the real tell.

## CONTENT PATTERNS

### 1. Undue Emphasis on Significance, Legacy, and Broader Trends

**Words to watch:** stands/serves as, is a testament/reminder, a vital/significant/crucial/pivotal/key role/moment, underscores/highlights its importance/significance, reflects broader, symbolizing its ongoing/enduring/lasting, contributing to the, setting the stage for, marking/shaping the, represents/marks a shift, key turning point, evolving landscape, focal point, indelible mark, deeply rooted
**Problem:** puffs up importance by claiming an arbitrary detail represents or contributes to some broader trend.

### 2. Undue Emphasis on Notability and Media Coverage

**Words to watch:** independent coverage, local/regional/national media outlets, written by a leading expert, active social media presence
**Problem:** hits the reader over the head with claims of notability, often as an unfiltered source list.

### 3. Superficial Analyses with -ing Endings

**Words to watch:** highlighting/underscoring/emphasizing..., ensuring..., reflecting/symbolizing..., contributing to..., cultivating/fostering..., encompassing..., showcasing...
**Problem:** present-participle phrases tacked onto a sentence to manufacture depth that isn't there.

### 4. Promotional and Advertisement-like Language

**Words to watch:** boasts a, vibrant, rich (figurative), profound, enhancing its, showcasing, exemplifies, commitment to, natural beauty, nestled, in the heart of, groundbreaking (figurative), renowned, breathtaking, must-visit, stunning
**Problem:** loses neutral tone in favor of marketing copy.

### 5. Vague Attributions and Weasel Words

**Words to watch:** Industry reports, Observers have cited, Experts argue, Some critics argue, several sources/publications (when few are actually cited)
**Problem:** attributes claims to unnamed authorities instead of a specific, checkable source.

### 6. Outline-like "Challenges and Future Prospects" Sections

**Words to watch:** Despite its... faces several challenges..., Despite these challenges, Challenges and Legacy, Future Outlook
**Problem:** formulaic "challenges, then optimistic close" structure grafted onto content that doesn't call for it.

## LANGUAGE AND GRAMMAR PATTERNS

### 7. Overused "AI Vocabulary" Words

**High-frequency AI words:** Actually, additionally, align with, crucial, delve, emphasizing, enduring, enhance, fostering, garner, highlight (verb), interplay, intricate/intricacies, key (adjective), landscape (abstract noun), pivotal, showcase, tapestry (abstract noun), testament, underscore (verb), valuable, vibrant
**Problem:** these words appear far more frequently in post-2023 text and tend to co-occur. A single instance is weak evidence (see What NOT to flag); several together is not.

### 8. Avoidance of "is"/"are" (Copula Avoidance)

**Words to watch:** serves as/stands as/marks/represents [a], boasts/features/offers [a]
**Problem:** an elaborate construction substituted for a plain copula.

### 9. Negative Parallelisms and Tailing Negations

**Problem:** "Not only...but..." / "It's not just about..., it's..." constructions, and clipped tailing-negation fragments ("no guessing", "no wasted motion") tacked on instead of written as a real clause.

### 10. Rule of Three Overuse

**Problem:** ideas forced into groups of three to appear comprehensive ("innovation, inspiration, and industry insights").

### 11. Elegant Variation (Synonym Cycling)

**Problem:** the same referent renamed sentence to sentence ("the protagonist" / "the main character" / "the central figure" / "the hero") instead of reused plainly.

### 12. False Ranges

**Problem:** "from X to Y" constructions where X and Y aren't actually on a meaningful scale.

### 13. Passive Voice and Subjectless Fragments

**Problem:** the actor is hidden or the subject dropped entirely ("No configuration file needed," "The results are preserved automatically") where active voice would be clearer and more direct.

## STYLE PATTERNS

### 14. Em Dashes (and En Dashes)

**Rule:** em dashes (—) and en dashes (–) — including spaced ` — ` and double-hyphen ` -- ` forms used the same way — are one of the most reliable AI tells. Flag every instance found in a candidate.
**Note:** not an automatic violation — a project's house style or a specific writer's established voice may permit them. The writer already drafts against `scientific-writer/references/house_style.md`, so treat an em dash surviving to review as worth flagging rather than assuming house style already cleared it.

### 15. Overuse of Boldface

**Problem:** mechanical bolding of phrases, especially first mentions of defined terms, without a reason tied to emphasis.

### 16. Inline-Header Vertical Lists

**Problem:** list items opening with a bolded header and colon ("**Performance:** Performance has been enhanced...") rather than integrated prose or plain list items.

### 17. Title Case in Headings

**Problem:** all main words capitalized in a heading, rather than sentence case.

### 18. Emojis

**Problem:** emoji used to decorate headings or bullet points in formal or technical writing.

### 19. Curly Quotation Marks

**Problem:** curly quotes (“...”) where the project's convention is straight quotes ("..."). Weak signal alone (see What NOT to flag) — most editors auto-curl by default.

## COMMUNICATION PATTERNS

### 20. Collaborative Communication Artifacts

**Words to watch:** I hope this helps, Of course!, Certainly!, You're absolutely right!, Would you like..., Want me to...?, Should I continue?, let me know, here is a...
**Problem:** chatbot-correspondence phrasing bleeding into content meant to stand on its own.

### 21. Knowledge-Cutoff Disclaimers and Speculative Gap-Filling

**Words to watch:** as of [date], Up to my last training update, While specific details are limited/scarce..., based on available information, not publicly available, maintains a low profile, keeps personal details private, prefers to stay out of the spotlight, likely [grew up/studied/began], it is believed that
**Problem:** either a literal cutoff disclaimer, or a paragraph that talks *about* not finding a source and then fills the gap with stock speculative phrasing instead of stating what isn't known.

### 22. Sycophantic/Servile Tone

**Problem:** overly positive, people-pleasing filler ("Great question!", "You're absolutely right that...").

## FILLER AND HEDGING

### 23. Filler Phrases

**Examples:** "In order to achieve this goal" (→ to achieve this), "Due to the fact that" (→ because), "At this point in time" (→ now), "In the event that" (→ if), "has the ability to" (→ can), "It is important to note that" (→ drop it).
**Problem:** padding that adds words without adding meaning.

### 24. Excessive Hedging

**Problem:** stacked qualifiers ("could potentially possibly be argued that... might have some effect") that hedge a claim into meaninglessness.

### 25. Generic Positive Conclusions

**Problem:** vague upbeat send-offs ("The future looks bright...", "Exciting times lie ahead...") that don't end on a concrete fact.

### 26. Hyphenated Word Pair Overuse

**Words to watch:** third-party, cross-functional, client-facing, data-driven, decision-making, well-known, high-quality, real-time, long-term, end-to-end
**Problem:** these compounds hyphenated uniformly, including in predicate position ("the report is high-quality"), where a human would typically hyphenate only attributively ("a high-quality report") and drop the hyphen otherwise.

### 27. Persuasive Authority Tropes

**Phrases to watch:** The real question is, at its core, in reality, what really matters, fundamentally, the deeper issue, the heart of the matter
**Problem:** pretends to cut through noise to a deeper truth, then delivers an ordinary point with extra ceremony.

### 28. Signposting and Announcements

**Phrases to watch:** Let's dive in, let's explore, let's break this down, here's what you need to know, now let's look at, without further ado
**Problem:** announces what the text is about to do instead of just doing it.

### 29. Fragmented Headers

**Signs to watch:** a heading followed by a one-line paragraph that just restates the heading before real content starts.
**Problem:** generic rhetorical warm-up that adds nothing and reads as padding.

### 30. Diff-Anchored Writing

**Problem:** prose written as if narrating a change ("This function was added to replace...") rather than describing the thing as it currently is. Doesn't apply to inherently version-scoped text (changelogs, release notes, migration guides) — skip there.

### 31. Manufactured Punchlines and Staccato Drama

**Problem:** every sentence engineered to land like a quotable closer, or a run of short declarative fragments stacked to manufacture drama ("No preference for symmetry. No aesthetic prior. No nostalgia."). One short sentence for emphasis is fine (see What NOT to flag); several in a row is the tell.

### 32. Aphorism Formulas

**Words to watch:** X is the Y of Z, X becomes a trap, X is not a tool but a mirror, the language of, the currency of, the architecture of
**Problem:** an ordinary claim dressed up as a reusable aphorism that sounds profound without adding precision.

### 33. Conversational Rhetorical Openers

**Phrases to watch:** Honestly?, Look, Here's the thing, The thing is, Let's be honest, Real talk — used as standalone hooks or fake-candid pauses before an ordinary point.
**Problem:** a theatrical pause-and-reveal (a one-word question or aside, then the "real" answer) manufacturing intimacy before a routine claim.

## What NOT to flag (false positives)

A clean human writer can hit several of the patterns above with no AI involvement. Before flagging, sanity-check that the finding isn't gutting legitimate prose:

- **Perfect grammar and consistent style.** Polish does not equal AI.
- **Mixed casual and formal registers.** Often a person in a technical field, a young writer, or a neurodivergent prose habit, not a chatbot.
- **"Bland" or "robotic" prose without specific tells.** Generic dryness alone is just dry writing.
- **Formal or academic vocabulary generally.** §7 covers *specific* overused words, not all fancy words — don't flag "ostensibly" or "constituent" just because they sound brainy.
- **Letter-style openings or closings.** Salutations and sign-offs predate ChatGPT by centuries.
- **Common transition words in isolation.** *Additionally*, *moreover*, *consequently* are only worth flagging when piled up. One *however* is not a tell.
- **Curly quotes alone.** Most editors and CMSes auto-curl by default; only flag when stacked with other tells (§19).
- **Em dashes alone.** Many human editors and journalists use them often; flag per §14's note, but weigh it against house style before calling it a defect.
- **One short emphatic sentence.** Only flag staccato drama (§31) when several short fragments appear in a row and inflate the tone.
- **"Honestly" or "look" mid-sentence.** Ordinary in casual writing — the tell is the standalone theatrical opener (§33), not the word itself.
- **Unsourced claims on their own.** Lack of a citation doesn't by itself indicate AI origin; that's a separate factual-accuracy concern, not a writing-smell one.
- **Correct, complex formatting.** Visual editors and templates produce clean output without any AI.
- **Secondhand text.** Don't flag a watched phrase inside a quotation, title, proper name, or example where it's being discussed rather than used as the writer's own prose.

When in doubt, look for **clusters** of tells, not isolated ones — a single em dash means nothing; em dashes plus rule-of-three plus *vibrant tapestry* plus a "Challenges and Future Prospects" section is a confession.

## Signs of human writing (do not flag these)

These are evidence of a real person writing. Treat them as a reason to *not* raise a smell nearby, even if an adjacent pattern above technically matches:

- **Specific, unusual, hard-to-fabricate detail.** A real address, a weird quote, an oddly specific aside. AI rounds off specifics; humans hoard them.
- **Mixed feelings and unresolved tension.** "This is mostly good, but it bothers me and I can't fully explain why." AI defaults to clean takes.
- **Dated, era-bound references.** Slang, memes, or in-jokes tied to a specific year and subculture.
- **First-person editorial choices the writer can defend.** A cut or word choice the writer can explain the reasoning behind.
- **Variety in sentence length.** Real writing alternates short and long; AI writing tends toward even, mid-length cadence.
- **Genuine asides, parentheticals, or self-corrections.** "(I keep wanting to say 'almost' here, but it really was certain.)"
