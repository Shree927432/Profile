# How to direct agents on this project

What worked for the reference, adapted for one person.

## Setup
- This folder is the shared memory. Every agent reads CLAUDE.md first.
- Decisions go in docs/05-decisions.md the moment they are made. An agent that
  starts tomorrow must not re-ask what was settled today.
- One agent per object or task. Two agents never edit the same file.

## The brief
A good brief has: the premise sentence, the one object or page in scope, the
contract file to follow, what done looks like, and a reference image if taste
is involved. Short. The docs carry the rest.

Example:
    Read CLAUDE.md. Build scene/objects/lamp.js per CONTRACT.md. Mesh name is
    "lamp_switch". Click toggles a point light and the lamp's emissive. Reduced
    motion: instant. Done when it works on click, keyboard (L), and touch.
    Show me a screenshot.

## The feedback loop
- Ask for a running preview or screenshot, not a description.
- Look on a phone and a laptop.
- Critique in plain words about what you see: "lamp too yellow", "can't find
  the back button", "feels cheap". Do not prescribe code.
- Ask for two or three options when it is about taste.
- Say "cut it" freely.

## Holding the line (anti-drift)
- Premise sentence at the top of every brief.
- Decisions file read at start, appended at end.
- Phase gates: nothing from the next phase until this one is online.
- A weekly look at the whole thing, not just the newest object.

## What to keep for yourself
Taste, content, interaction design, scope, and the final look at every change.
Hand over mechanics, research, and grunt work.
