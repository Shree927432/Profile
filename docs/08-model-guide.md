# Which model and effort to use

Rule: start cheap, move up only when you see a reason. Judge cost per finished
task, not per message. A cheap model that needs three retries is not cheap.

## By phase

| Phase | Work | Agent | Model | Effort |
|---|---|---|---|---|
| 0 | Writing content, vision, deciding premise | (you, or designer for options) | Opus | high |
| 1 | Astro static site | builder | Sonnet | medium |
| 2 | First 2D screen module | builder | Sonnet | medium |
| 3 | Three.js shell, pick map, quality ladder | builder | Sonnet | high |
| 4 | Blender room, lighting, look | designer | Fable 5.1 (since 2026-10-22) | high |
| 4 | 2D design sheets, briefs, simple stills | designer | Opus | high |
| 5 | Simple objects (lamp, coffee, clock) | builder | Sonnet | medium |
| 5 | Close-ups, floating objects, audio | designer | Opus | high |
| 6 | Sound, performance tuning, accessibility | builder | Sonnet | high |
| 7 | Polish, deciding what to cut | designer | Opus | high |
| any | Typos, content edits, renames, small fixes | quick | Haiku | low |

## Move up a level when

- The same mistake happens twice.
- The task is about taste: look, feel, what to cut.
- It must reason across many files at once.
- A bug survives one honest attempt.

## Move down a level when

- The task is written out step by step.
- It is mechanical: scaffolding, wiring, renaming, formatting.
- It is a one-file, few-line change.

## Effort

- low: one-line edits, lookups, content changes.
- medium: the default for well-specified building.
- high: design, debugging, anything where being wrong is expensive.
- xhigh / max: rarely. Only when high visibly falls short on a hard problem.

## Agents in .claude/agents/

- builder: Sonnet, medium. Mechanical building per the docs.
- designer: Opus, high. Taste, 3D, lighting, polish, cutting. Its file says Opus; for Phase 4 modelling,
  launch it with the model set to Fable 5.1 (`model: "fable"` on the agent call).
- quick: Haiku, low. Small edits only.

Ask for one by name: "use the builder agent to do Phase 2".

## Check yourself weekly

Ask Claude "explain my usage". If most usage went to Opus doing mechanical
work, move those rows in the table down a level.
