# Worked example: identify, skip, then plan only missing translations

## Start from the selected evidence

The user selected 203 objects in `新块.dwg`. `Model/916` is a block occurrence whose
children `91B`–`922` contain all eight English exemplars. Read its definition and
apply its insertion offset. Do not conclude “no translations” because the selected
top-level TEXT is Chinese. Do not explode the block to access the child strings.

## Decisions for the eleven selected Chinese sources

| Source key | Chinese | Existing English | Disposition |
|---|---|---|---|
| Model/6E4::TextString | 檩托详图 | Model/916/91E — Purlin Bracket | already_translated; title is abbreviated |
| Model/75A::TextString | 中间跨 | Model/916/91C — Middle Span | already_translated |
| Model/75B::TextString | 边跨 | Model/916/91F — Side Span | already_translated |
| Model/769::TextString | 檩托 | None | needs_translation |
| Model/801::TextString | 钢梁 | Model/916/91D — Steel Beam | already_translated |
| Model/824::TextString | 钢梁 | Model/916/922 — Steel Beam | already_translated |
| Model/832::TextString | 檩托 | None | needs_translation |
| Model/8C5::TextString | 钢梁 | Model/916/920 — Steel Beam | already_translated |
| Model/8D5::TextOverride | 外挑尺寸 | Model/916/921 — Overhang Dimension | already_translated |
| Model/8E2::TextString | 详平面 | None | needs_translation |
| Model/8E5::TextString | WL与钢梁搭接详图 | Model/916/91B — Detailed Drawing of WL and Steel Beam Lapping | already_translated |

The already-translated dimension remains completely untouched. The Chinese title
`檩托详图` is already covered even though its English omits “Detail”. Report the
abbreviation; do not create a second English title. The two other `檩托` callouts are
different occurrences, so they are not covered by that title's English. `WL`, bolt
grades, numeric dimensions and scales are identifiers/values, not English counterpart
evidence and generally need no translation on their own.

For a selected-area request, only the three `needs_translation` entries are eligible
for placement. The copy-only trial used `Purlin Bracket` for each callout and `See Plan`
for `详平面`. It also exercised the 24 missing occurrences outside the selection as a
separate whole-drawing trial. In a new selected run, those 24 remain out of scope even
though the full drawing is scanned for counterpart and collision evidence.

That whole-drawing run was subsequently carried out on this same drawing and verified.
All 27 were placed, the 8 existing translations were skipped, and all 1781 pre-existing
entities compared identical afterwards. Use `doc/20260907/dwg-trial/` as a concrete
precedent: `decisions.json` for a real 35-row manifest, `trial-report.json` for accepted
placements with their rejected candidates and obstacle handles, `refinement-report.json`
for before/after repositioning, and `final-report.md` for the report shape this skill
requires. It is one drawing and one run, not a general guarantee.

## Decision manifest schema

Use a JSON object with `drawing`, `inventory_sha256`, `claims_complete`, and a
`decisions` array. Every Chinese display-field source needs one row, even when excluded
by scope. For a partial run use `excluded` with a scope reason for out-of-scope rows.
`claims_complete` means inventory accounting is complete, not that translation or
visual checks passed. Keep the final QA results in separate fields.

Example row for a confirmed skip:

```json
{
  "source_key": "Model/8D5::TextOverride",
  "source_raw": "外挑尺寸",
  "status": "already_translated",
  "existing_check": {
    "completed": true,
    "searched": "Same detail, including nested and unselected text; semantic and spatial match verified"
  },
  "existing_english_ids": ["Model/916/921"],
  "reason": "Overhang Dimension corresponds to this dimension override in the selected detail."
}
```

Example row for missing text, before placement is authorized by a translation task:

```json
{
  "source_key": "Model/769::TextString",
  "source_raw": "檩托",
  "status": "needs_translation",
  "existing_check": {
    "completed": true,
    "searched": "All English occurrences in the model; the remote Purlin Bracket title belongs to source 6E4"
  },
  "existing_english_ids": [],
  "reason": "No counterpart for this individual callout."
}
```

During a requested translation, add `new_english` and a `placement` only to
`needs_translation` rows after wording and collision planning. An uncertain existing
pair gets `uncertain_existing` and candidate IDs within `existing_check`, never a
new insertion. `blocked` requires an actionable reason (unreadable object, unresolved
term, unsupported transform or no clear location), not an empty “unknown” label.

## Reproduce the reference profile

Run `scripts/build_example_profile.py` only on this captured exemplar's inventory.
It checks the eight raw pairs and their occurrence IDs and then writes the measured
profile and observed glossary. Its handle mappings are sample-specific evidence,
not a general automatic matcher. On another drawing, perform matching anew.

```powershell
python .agent/skills/autocad-structural-translation/scripts/build_example_profile.py doc/20260907/translation-learning-v2/inventory.json --output translation-profile-review
```

Expected: 8 confirmed pairs, 6 distinct observed English phrases, 35 Chinese display
fields, 27 lacking counterparts, 3 of those selected. Keep the original capture and
its hash so the result can be traced to actual drawing objects.
