# AI Agent Instructions for Creating Ouija Balatro Seed Filters

## Overview
These instructions are for AI agents tasked with creating `.ouija.json` filter configuration files for the Ouija Balatro seed finder tool. Follow these rules strictly to ensure filters work correctly.

## File Structure Requirements

### 1. JSON Format
- Use valid JSON syntax with proper escaping
- Include comments using `//` (the parser supports this)
- Maintain consistent indentation (4 spaces recommended)

### 2. Required Top-Level Fields
```json
{
    "name": "filter_name_snake_case",
    "description": "Detailed description of the filter strategy and goals",
    "author": "Your Name/Organization",
    "filter_config": {
        // Filter configuration goes here
    }
}
```

### 3. Filter Configuration Structure
```json
"filter_config": {
    "numNeeds": <integer 0-20>,
    "numWants": <integer 0-20>,
    "Needs": [/* array of need objects */],
    "Wants": [/* array of want objects */],
    "maxSearchAnte": <integer 1-8>,
    "deck": "<valid_deck_name>",
    "stake": "<valid_stake_name>",
    "scoreNaturalNegatives": <boolean>,
    "scoreDesiredNegatives": <boolean>
}
```

## Item Naming Rules

### CRITICAL: Use Only Valid Item Names
- **ALWAYS** reference `host_items.h` for valid item names
- **NEVER** invent item names - they must exist in the enum
- Use exact enum names (case-sensitive with underscores)

### Valid Item Categories:
1. **Jokers**: `Joker`, `DNA`, `Perkeo`, `Triboulet`, etc.
2. **Vouchers**: `Telescope`, `Observatory`, `Overstock`, etc.
3. **Tarot Cards**: `The_Fool`, `The_Magician`, `Death`, etc.
4. **Spectral Cards**: `Immolate`, `Cryptid`, `The_Soul`, `Ankh`, etc.
5. **Tags**: `Negative_Tag`, `Double_Tag`, `Charm_Tag`, etc.
6. **Decks**: `Red_Deck`, `Anaglyph_Deck`, `Plasma_Deck`, etc.
7. **Stakes**: `White_Stake`, `Red_Stake`, `Gold_Stake`, etc.
8. **Ranks**: `_2`, `_3`, `_4`, `_5`, `_6`, `_7`, `_8`, `_9`, `_10`, `Jack`, `Queen`, `King`, `Ace`

### Edition Rules:
- **ONLY** add `"jokeredition"` field to **Jokers**
- **NEVER** add `"jokeredition"` to: Tags, Tarot Cards, Spectral Cards, Vouchers, Ranks, etc.
- Valid editions: `"No_Edition"`, `"Foil"`, `"Holographic"`, `"Polychrome"`, `"Negative"`

## Object Structure Rules

### Need Objects:
```json
{
    "value": "<valid_item_name>",
    "jokeredition": "<edition_name>",  // ONLY for Jokers
    "desireByAnte": <integer 1-8>
}
```

### Want Objects:
```json
{
    "value": "<valid_item_name>",
    "jokeredition": "<edition_name>"   // ONLY for Jokers
}
```

## Validation Checklist

Before creating a filter, verify:

### ✅ Item Validation:
- [ ] All item names exist in `host_items.h` enum
- [ ] No invented/made-up item names
- [ ] Correct case and underscore usage
- [ ] Ranks use underscore prefix (`_2`, not `2`)

### ✅ Edition Validation:
- [ ] `jokeredition` field ONLY on Jokers
- [ ] No `jokeredition` on Tags, Tarots, Spectrals, Vouchers
- [ ] Valid edition names from enum

### ✅ Deck/Stake Validation:
- [ ] Deck name exists in enum (e.g., `"Anaglyph_Deck"`)
- [ ] Stake name exists in enum (e.g., `"White_Stake"`)

### ✅ Logical Validation:
- [ ] `numNeeds` matches length of `Needs` array
- [ ] `numWants` matches length of `Wants` array
- [ ] `maxSearchAnte` is reasonable (1-8)
- [ ] `desireByAnte` values ≤ `maxSearchAnte`

## Common Mistakes to Avoid

### ❌ DON'T:
- Invent item names like `"Chaos_Tag"`, `"Mathematician"`, `"Golden_Tag"`
- Add `jokeredition` to non-Jokers
- Use `"Immolation"` (correct: `"Immolate"`)
- Use rank numbers without underscore (`"2"` instead of `"_2"`)
- Create impossible combinations
- Use more than 20 Needs or Wants

### ✅ DO:
- Reference `host_items.h` for all item names
- Use descriptive filter names and descriptions
- Create thematically coherent strategies
- Test logic mentally (can these items synergize?)
- Use appropriate decks for the strategy

## Example Template:
```json
{
    "name": "example_synergy_filter",
    "description": "Seeks powerful synergy between [specific items] for [strategy goal]. This filter hunts for [explanation of why these items work together].",
    "author": "AI Agent",
    "filter_config": {
        "numNeeds": 2,
        "numWants": 5,
        "Needs": [
            {
                "value": "Blueprint",
                "jokeredition": "No_Edition",
                "desireByAnte": 2
            },
            {
                "value": "Brainstorm",
                "jokeredition": "No_Edition",
                "desireByAnte": 3
            }
        ],
        "Wants": [
            {
                "value": "Negative_Tag"
            },
            {
                "value": "DNA",
                "jokeredition": "No_Edition"
            },
            {
                "value": "The_Soul"
            },
            {
                "value": "Perkeo",
                "jokeredition": "No_Edition"
            },
            {
                "value": "Double_Tag"
            }
        ],
        "maxSearchAnte": 3,
        "deck": "Red_Deck",
        "stake": "White_Stake",
        "scoreNaturalNegatives": true,
        "scoreDesiredNegatives": true
    }
}
```

## Final Verification Steps:

1. **Cross-reference every item** with `host_items.h`
2. **Verify edition usage** (only on Jokers)
3. **Check array lengths** match num fields
4. **Validate logical coherence** of strategy
5. **Test JSON syntax** validity
6. **Ensure thematic consistency** in description

Following these rules will ensure your filters work correctly with the Ouija seed finder! 🎰
