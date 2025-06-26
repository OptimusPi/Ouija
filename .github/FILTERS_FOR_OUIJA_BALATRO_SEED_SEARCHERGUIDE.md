# Balatro Filter Coding Guide

## Overview

This document summarizes the key mechanics and best practices for writing deterministic, bug-free Balatro seed analyzers and filters (e.g., for Ouija, Immolate, etc). Reference this guide whenever you are writing or reviewing code for Balatro-related filters!

---

## Core Mechanics

### 1. **Pack Generation**
- **Ante 1:** 2 shops × 2 packs = 4 packs (first is always Buffoon).
- **Ante 2+:** 3 shops × 2 packs = 6 packs.
- **No rerolls** for packs; their contents are fixed for the ante.
- **First pack in Ante 1 is always Buffoon_Pack** (guaranteed Joker for player).

### 2. **Shop Items**
- Shop always shows two items per reroll.
- Only No_Edition Jokers are eligible for Negative Tag grabs.
- Non-joker items (planets, tarots, etc.) must be processed for RNG advancement but are not eligible for grabs.

### 3. **Tags and Vouchers**
- Both small blind and big blind tags can trigger special packs (e.g., Charm_Tag for Mega Arcana, Ethereal_Tag for Mega Spectral).
- Vouchers can affect shop/pack size, but basic logic assumes default sizes unless otherwise handled.

### 4. **Negative Tag Mechanic**
- When a Negative Tag is popped, **all Double Tags are consumed** at once.
- All visible No_Edition shop jokers are eligible for “free” negative edition.
- The tag inventory is wiped after popping the Negative Tag.

### 5. **Legendary Jokers (The_Soul)**
- The_Soul (from Arcana/Spectral packs) produces a random legendary joker.
- **Always check if the legendary joker matches any needs/wants** in your config, not just The_Soul itself.
- Score both The_Soul and the resulting legendary joker for needs/wants.

### 6. **Mega Packs from Tags**
- If no Arcana/Spectral pack is found in the normal pack checks, but a Charm_Tag/Ethereal_Tag is present (small or big blind), simulate a Mega Arcana/Spectral Pack (size 5) and process its contents.

---

## Coding Best Practices

- **Always advance the RNG for every shop/pack slot, even if skipping scoring.**
- **Use fixed-size arrays** for packs (size 5 is safe for all pack types).
- **Declare arrays outside of switch/if blocks** to avoid OpenCL memory bugs.
- **Never hard-code specific legendary jokers** (e.g., Perkeo); always use config-driven needs/wants.
- **Add debug prints** for pack/shop contents and legendary joker rolls when troubleshooting.
- **Handle all pack types in a switch statement**; add a `default:` case for future-proofing.
- **For each The_Soul found, roll a legendary joker and check against all needs/wants.**
- **When simulating Mega Packs from tags, use the correct pack function and size (5).**

---

## Example: Legendary Joker Handling

```opencl
if (cards[i] == The_Soul) {
    jokerdata jkr = next_joker_with_info(inst, S_Soul, ante);
    for (int x = 0; x < clampedNumNeeds; x++) {
        if (config->Needs[x].value == The_Soul || config->Needs[x].value == jkr.joker) {
            ScoreNeeds[x] = true;
        }
    }
    for (int x = 0; x < clampedNumWants; x++) {
        if (config->Wants[x].value == The_Soul || config->Wants[x].value == jkr.joker) {
            result->ScoreWants[x]++;
        }
    }
}
```

---

## Reference: Shop Loop Example

```opencl
for (int reroll = 0; reroll < ante && grabs > 0; reroll++) {
  for (int i = 0; i < 2 && grabs > 0; i++) {
    shopitem _shopitem = next_shop_item(inst, ante);
    if (_shopitem.value == RETRY) continue;
    if (_shopitem.type != ItemType_Joker || _shopitem.joker.edition != No_Edition) continue;
    // Only decrement grabs and score for valid jokers
    grabs--;
    // ...scoring logic...
  }
}
```

---

## Checklist for New Filters

- [ ] Handle all packs and shop items for every ante.
- [ ] Correctly simulate Mega Packs from tags if no normal pack found.
- [ ] Score both The_Soul and the legendary joker it produces.
- [ ] Use config-driven needs/wants for all scoring.
- [ ] Use fixed-size arrays and declare them outside of control blocks.
- [ ] Add debug prints as needed for troubleshooting.
- [ ] Always advance the RNG for every slot, even if skipping scoring.

---

**Keep this guide updated as Balatro mechanics evolve or new edge cases are discovered!**