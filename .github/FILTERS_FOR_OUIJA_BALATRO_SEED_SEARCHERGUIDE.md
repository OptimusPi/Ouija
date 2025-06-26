# Ouija Filter JSON Config Guide

> **For AI/Automation (GitHub Copilot, etc):**
> - This file is the canonical reference for creating, editing, and understanding Ouija JSON filter configs.
> - When asked to create a new filter config, always use the real game items, mechanics, and structure as described in `BALATRO_GAME_ITEMS_AND_MECHANICS.md`.
> - Do not invent or hallucinate items, tags, or mechanics. Only use those documented in the official mechanics guide.
> - Example configs and field explanations are provided below. Update this file as the config schema evolves.

---

## What is a Ouija Filter Config?
A Ouija filter config is a JSON file that tells Ouija (the Balatro seed analyzer) what to search for in a run. It describes the jokers, items, tags, and other conditions you want to find, and how to score or filter seeds.

## Example Filter Config
```json
{
  "name": "Legendary Joker Finder",
  "description": "Finds seeds with The_Soul and any legendary joker by Ante 3.",
  "maxSearchAnte": 3,
  "Needs": [
    { "type": "joker", "value": "The_Soul" },
    { "type": "joker", "value": "Perkeo" }
  ],
  "Wants": [
    { "type": "joker", "value": "Baron" },
    { "type": "joker", "value": "Brainstorm" }
  ],
  "scoreNaturalNegatives": true,
  "scoreDesiredNegatives": false
}
```

## Field Reference
- `name`: Human-readable name for the filter.
- `description`: What this filter is for.
- `maxSearchAnte`: How many antes to simulate (1-8).
- `Needs`: List of required items (jokers, tags, etc). All must be found for a seed to be valid.
- `Wants`: List of desired items. Each found increases the score.
- `scoreNaturalNegatives`: If true, score natural negative jokers.
- `scoreDesiredNegatives`: If true, score desired negative jokers.

## How to Edit or Create a Filter
1. Copy the example above and change the `Needs`/`Wants` to match your goals.
2. Only use real item names and mechanics from the official mechanics guide.
3. Save as a `.ouija.json` file in the `ouija_configs/` folder.
4. Ask Copilot to generate a new config by describing what you want to find!

---

**Keep this guide up to date as Ouija and Balatro mechanics evolve.**
