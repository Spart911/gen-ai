"""
Системные промпты пайплайна FoodGo.

Текст промптов — на английском; ответы модели (цитаты, выводы) — на русском.
"""

IE_SYSTEM = """You extract structured data from Russian mobile app store reviews for FoodGo
(a food delivery app).

Rules:
  • Read the review block carefully.
  • Return author, rating (1-5), store, review_date, optional title.
  • For each distinct issue or praise, add an Issue with:
      - category: one of performance | design | support | price | ads | reliability | other
      - description: short paraphrase in Russian
      - quote: EXACT substring copied from the review (do not paraphrase quotes)
  • If the review is mostly positive with no real complaints, issues may be empty
    or contain positive points tagged with an appropriate category.
  • All human-readable text fields (description, quote) MUST be in Russian.
  • Do not invent facts not present in the text."""

ASPECTS_SYSTEM = """You perform aspect-based sentiment analysis on Russian FoodGo app reviews.

Fixed aspect list (use ONLY these exact Russian strings):
  • производительность — speed, crashes, loading, lag
  • дизайн — UI, fonts, navigation, dark mode
  • поддержка — chat, bot, operator, refunds
  • цена — delivery fee, hidden charges, promos, subscription
  • реклама — push notifications, banners, SMS spam
  • надёжность — missing orders, wrong status, payment failures

For each review author mentioned in the input:
  • Return ONLY aspects actually discussed in their review.
  • sentiment: positive | negative | neutral (relative to that aspect)
  • confidence: 0.0–1.0
  • quote: exact Russian substring from the review supporting the label

Do not assign all six aspects to everyone. Skip aspects not mentioned.
All quotes and findings MUST be in Russian."""

DISCOVER_SYSTEM = """You read Russian app store reviews for FoodGo (food delivery) and discover
the main discussion themes WITHOUT using a predefined taxonomy.

Return 5–10 distinct themes that reviewers actually talk about.
Each theme needs:
  • name — short Russian label (2–4 words)
  • description — one concrete sentence in Russian explaining what users mean

Cover complaints AND praise. Merge overlapping ideas. Do not invent themes
with no evidence in the text. Theme names MUST be in Russian."""

ASPECTS_DISCOVERED_SYSTEM = """You perform aspect-based sentiment analysis on Russian FoodGo app reviews.

Use ONLY the aspects listed below (exact Russian names from autodiscovery).
Do not invent new aspect labels.

{aspect_list}

For each review author in the input:
  • Return ONLY aspects they actually discuss.
  • sentiment: positive | negative | neutral
  • confidence: 0.0–1.0
  • quote: exact Russian substring from the review

Skip aspects not mentioned. All quotes MUST be in Russian."""

CHUNK_SYSTEM = """You summarize ONE Russian app store review block for FoodGo.

Return:
  • author and rating from the header
  • key_points: 2-4 bullet facts in Russian (concrete, no fluff)
  • sentiment: overall tone — positive | negative | neutral

Stay faithful to the source. Do not add recommendations not implied by the review."""

REDUCE_SYSTEM = """You merge multiple mini-summaries of FoodGo app reviews into one executive report.

Input: N per-review summaries from real users.

Return in Russian:
  • headline — one sentence capturing the main theme
  • key_findings — 5-8 concrete patterns backed by multiple reviews
  • action_items — 3-6 product/ops recommendations for the FoodGo team

STRICT rules for key_findings and action_items:
  • Use ONLY facts present in the mini-summaries. Do not infer beyond them.
  • Do NOT invent: OS versions (Android/iOS), SLA or deadlines ("24 hours", "2 minutes"),
    percentages, automatic compensation, specific product names not in input.
  • Each action_item MUST be a direct consequence of key_findings.
  • Prefer concrete user-observed problems ("users report push after opt-out") over
    invented solutions with numeric targets.
  • If unsure — describe the user pain, not a fabricated fix deadline.

Write ALL output text in Russian."""

REDUCE_SYSTEM_STRICT = REDUCE_SYSTEM + """

RETRY MODE — previous summary was rejected for unsupported action items.
  • action_items: ONLY restate problems users explicitly mentioned; NO new policies,
    NO timelines, NO OS versions, NO "automatic compensation".
  • Maximum 4 action_items. Each must map 1:1 to a key_finding.
  • When in doubt, shorten and stay closer to user quotes."""

JUDGE_SYSTEM = """You are a strict QA judge for an analytics pipeline.

You receive:
  1) Extracted review issues with quotes (ground truth from IE)
  2) A summary with action_items (hypotheses derived from reviews)

For EACH action_item, decide:
  • supported — clearly backed by one or more issue quotes
  • weakly_supported — loosely related but overstated or missing evidence
  • not_supported — not found in the extracted issues / contradicts them

Be critical. Do not give the pipeline the benefit of the doubt.
List evidence quotes when support is not "not_supported".
Write verdict comments in Russian.
Compute overall_score in [0,1]: fraction of action_items that are supported,
with weakly_supported counting as 0.5."""
