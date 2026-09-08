---
name: autocad-structural-translation
description: Use when translating Chinese AutoCAD DWG annotations into English, translating only preselected drawing objects, translating an entire structural drawing, auditing existing bilingual CAD text, preventing duplicate English, or resuming and verifying a pyautocad translation run.
compatibility: Windows AutoCAD with ActiveX, Python 3, pyautocad and comtypes; offline helpers use Python standard library.
---

# AutoCAD Structural Translation

## Core principle

Preserve the source DWG and every Chinese source object. For each in-scope Chinese
occurrence, search for an existing English counterpart first. Skip only a confirmed
counterpart, translate only missing text, and write English to an explicit copy.

All AutoCAD interaction must go through one pyautocad connection created with
`Autocad(create_if_not_exists=False)`. Never use AutoLISP, `SendCommand`, command
strings, or a separate pywin32 CAD connection.

## Choose and freeze the scope

Choose exactly one mode:

| Mode | Translation sources | Global read-only scan |
|---|---|---|
| `selected` | Selected text-bearing objects plus visible text descendants of each selected insert occurrence | Required for counterpart and collision checks |
| `drawing` | Every discovered Chinese display-field occurrence | Required |

In selected mode, capture `doc.PickfirstSelectionSet` before activation, zoom,
selection commands, or edits. Selecting one block insertion does not select other
insertions of that definition. Unselected geometry may block placement and unselected
English may prove a counterpart, but unselected Chinese must never receive new text.
Read [selection-scope.md](references/selection-scope.md) before a selected run.

## Required workflow

### 1. Confirm the live document and capture evidence

Verify `acad.doc.FullName`, not just the basename. Preserve the original disk hash
and note unsaved source state. Read the project sibling skill
`.agent/skills/pyautocad/SKILL.md`, then [object-coverage.md](references/object-coverage.md).

Use a Python interpreter that imports pyautocad; it may differ from shell `python`.

```powershell
$cadPython = 'C:/Users/Venchy/AppData/Local/Programs/Python/Python312/python.exe'
& $cadPython -X utf8 .agent/skills/autocad-structural-translation/scripts/inspect_drawing.py `
  --expect-name target.dwg --expect-path E:/path/target.dwg --output run-001
python .agent/skills/autocad-structural-translation/scripts/analyze_inventory.py `
  run-001/inventory.json --output run-001/analysis
```

The scanner reads layouts, definitions, nested inserts, attributes, ATTDEF,
dimensions, leaders/MLeaders, tables, and other probed text properties. A zero-error
scan does not erase reported occurrence gaps. Proxy/zombie, xref, dynamic-block,
MINSERT, field, non-+Z, and unknown-class gaps remain explicit.

### 2. Build the immutable source boundary

```powershell
python .agent/skills/autocad-structural-translation/scripts/scope_manifest.py `
  run-001/analysis/occurrences.json --mode selected `
  --selection run-001/selection.json --output run-001/scope.json
```

Use `--mode drawing` without `--selection` for a whole-drawing run. Occurrence keys
have the form `layout/insert-handle/.../entity-handle::property`; repeated block
instances are separate. Preserve the raw source string exactly.

### 3. Check existing English before translating every source

Search the full read-only inventory, including nested and unselected text. Generate
candidate evidence with `counterpart_candidates.py`, then review it using
[counterpart-confidence.md](references/counterpart-confidence.md).

```powershell
python .agent/skills/autocad-structural-translation/scripts/counterpart_candidates.py `
  run-001/analysis/occurrences.json run-001/decisions.json `
  --output run-001/counterpart-candidates.json
```

A confirmed skip requires both semantic/token agreement and spatial or structural
association. Proximity, magenta color, Latin characters, an `EN` layer, or word
similarity alone never proves a translation. Hidden English, competing candidates,
opposite-direction terms, another block instance, or an unrelated table column is
`uncertain_existing` or rejected—not an automatic skip.

Use dispositions `already_translated`, `needs_translation`, `uncertain_existing`,
`excluded`, and `blocked`. Every skip records the English occurrence ID and evidence.
Do not improve or duplicate imperfect existing English unless the user requested
editing it.

### 4. Translate with protected content intact

Apply, in order: reviewed project glossary, confirmed observed glossary, then a new
structural-engineering translation. Keep terminology evidence separate from proposed
wording. Never treat the exemplar glossary as universally correct.

Preserve identifiers, member marks, grades, quantities, units, scales, tolerances,
dimension placeholders, fields, and SHX codes, including `WL`, `M12(4.6s)`, `1:10`,
`<>`, `[]`, `%%c`, `%%d`, `%%p`, `%%132`, `\S...;`, and `%<...>%`. Do not evaluate
fields or write normalized comparison strings back to CAD.

Validate manifest accounting before placement:

```powershell
python .agent/skills/autocad-structural-translation/scripts/translation_rules.py `
  run-001/analysis/occurrences.json run-001/decisions.json --scope run-001/scope.json
```

### 5. Derive style and rehearse placement offline

Derive style, height, color, orientation, attachment, and scale from reviewed
bilingual examples in the target drawing. Values learned from `新块.dwg`—MTEXT,
`TSSD_Rein`, height 350, ACI 6—are evidence for that drawing only.

Use `placement_planner.py` primitives with a spatial index. Offline width is a
conservative feasibility estimate, not a final extent. Choose individual near-source
placement for isolated labels. Use an atomic aligned English column for three or more
rows belonging to the same table or note paragraph. Read
[column-placement.md](references/column-placement.md) and
[placement-and-writing.md](references/placement-and-writing.md).

```powershell
python .agent/skills/autocad-structural-translation/scripts/placement_planner.py `
  run-001/analysis/occurrences.json run-001/scope.json run-001/decisions.json `
  --output run-001/placement-plan.json
```

No-space results remain blocked with translations and diagnostics. Do not indefinitely
increase distance, shrink text below readability, mask geometry, or partially write a
failed column group.

### 6. Dry-run, write one copy, and resume safely

The generic writer defaults to a no-CAD dry run. Review its `--help`, then supply
inventory, occurrences, scope, decisions, plan, source/output paths, and journal.
Only pass `--apply` after all uncertain cases and styles are reviewed.

```powershell
& $cadPython -X utf8 .agent/skills/autocad-structural-translation/scripts/apply_translations.py `
  --inventory run-001/inventory.json --occurrences run-001/analysis/occurrences.json `
  --scope run-001/scope.json --manifest run-001/decisions.json `
  --plan run-001/placement-plan.json --source-dwg E:/path/source.dwg `
  --output-dwg E:/path/output_EN.dwg --journal run-001/write-journal.json `
  --expect-active E:/path/source.dwg
```

The writer must recheck the source raw value and existing-English review immediately
before each insertion. It records `intent`, `created_unplaced`, and `placed` states.
Resume removes only a logged orphan whose handle and English text still match the run.
Column groups are all-or-none. Known transient COM rejection errors receive bounded
backoff; other errors stop the run.

For drawings with hundreds of sources, follow
[large-drawing-workflow.md](references/large-drawing-workflow.md). Never embed title
block, sample-area, or table coordinates in reusable code; store reviewed regions and
roles in the run manifest.

### 7. Verify after save and reopen

Use `verify_translation.py` for offline reconciliation and perform live checks through
pyautocad: output full path, created handles, text/style/layer/color/height/rotation,
actual bounding boxes, visibility, collision clearance, original-object properties,
and unchanged source disk hash. Save, close, reopen, rescan, and reconcile again.

Chinese intentionally remains; “no Chinese found” is not success. Re-run counterpart
and scope decisions against the output. A completed run proposes zero additional
English for every successfully covered source.

## Stop conditions

Stop automatic writing and report the affected source when any of these occurs:

- Active full path, frozen selection, source raw text, or inventory fingerprint changed.
- Existing-English evidence is ambiguous or contradicts protected tokens.
- Text is rendered but unreadable through verified APIs.
- Transform/projection, xref, proxy, field, table content, or owner layout is unresolved.
- Target style/font is missing or the placement cannot meet readability and clearance.
- Recovery cannot prove an object belongs to the current run.

## Required final report

Report source/output/recovery paths; mode and frozen selection count; database entities,
layouts, definitions, resolved occurrences, Chinese sources in scope; existing English
skipped; English added; excluded/uncertain/blocked; extraction and projection gaps;
individual/column placement results; save/reopen and visual checks; source hash/property
integrity; repeat-run additions; and artifact paths.

Read [production-run-evidence.md](references/production-run-evidence.md) for measured
large-run results and current limits. Read [learned-conventions.md](references/learned-conventions.md)
and [worked-example.md](references/worked-example.md) only when using the reference
drawing or calibrating a comparable drafting style.
