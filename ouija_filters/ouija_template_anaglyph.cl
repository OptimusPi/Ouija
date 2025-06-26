#include "lib/ouija.cl"
#define CACHE_SIZE 64
// #define _debugPrintsMAGIC
// #define _debugPrints1

void ouija_filter(instance *inst, __constant OuijaConfig *config, OuijaResult *result) {

  // Use faster primitive initialization
  bool valid = true;
  // Initialize result struct efficiently
  result->TotalScore = 1;
  result->NaturalNegativeJokers = 0;
  result->DesiredNegativeJokers = 0;

  // Initialize ScoreWants array explicitly (host clearing was unreliable)
  for (int i = 0; i < MAX_DESIRES_KERNEL; i++) {
    result->ScoreWants[i] = 0;
  }

  // Clamp numNeeds and numWants defensively
  int clampedNumNeeds = config->numNeeds;
  int clampedNumWants = config->numWants;
  if (clampedNumNeeds > MAX_DESIRES_KERNEL)
    clampedNumNeeds = MAX_DESIRES_KERNEL;
  if (clampedNumNeeds < 0)
    clampedNumNeeds = 0;
  if (clampedNumWants > MAX_DESIRES_KERNEL)
    clampedNumWants = MAX_DESIRES_KERNEL;
  if (clampedNumWants < 0)
    clampedNumWants = 0;

  // Memory fence

#ifdef _debugPrints
  printf("[Kernel] Starting filter\n");
  printf("[Kernel] Deck id: %d\n", config->deck);
  printf("[Kernel] Stake id: %d\n", config->stake);
  printf("[Kernel] Num Needs: %d (clamped: %d)\n", config->numNeeds,
         clampedNumNeeds);
  printf("[Kernel] Num Wants: %d (clamped: %d)\n", config->numWants,
         clampedNumWants);
  printf("[Kernel] Max Search Ante: %d\n", config->maxSearchAnte);
  printf("[Kernel] Seed: [%s]\n", debug_Seed.str);
#endif

  set_deck(inst, config->deck);
  set_stake(inst, config->stake);
  init_locks(inst, 1, false, true);

  int ante = 0;
  bool ScoreNeeds[MAX_DESIRES_KERNEL] = {false};
  int maxSearchAnte = config->maxSearchAnte;
  int dt = 0;
  bool allNeedsMet = false;


  for (int ante = 1; ante <= maxSearchAnte && valid; ante++) {
    init_unlocks(inst, ante, false);
    item voucher = next_voucher(inst, ante);
#ifdef _debugPrints
    printf("[Kernel] Ante %d Voucher: ", ante);
    print_item(voucher);
    printf("\n");
#endif
    if (ante > 1 && voucher != Hieroglyph && voucher != Petroglyph) {
      activate_voucher(inst, voucher);
    }
    item smallBlindTag = next_tag(inst, ante);
    item bigBlindTag = next_tag(inst, ante);

    // Score tags (including Negative_Tag) and vouchers from the blinds.
    // This is the same logic as the default template.
    for (int x = 0; x < clampedNumNeeds; x++) {
      bool isSmallBlind = (config->Needs[x].value == smallBlindTag);
      bool isBigBlind = (config->Needs[x].value == bigBlindTag);
      bool isVoucher = (config->Needs[x].value == voucher);
      if (isSmallBlind || isBigBlind || isVoucher){
        ScoreNeeds[x] = true; 
      }
    }
    for (int x = 0; x < clampedNumWants; x++) {
      int isSmallBlind = (config->Wants[x].value == smallBlindTag) ? 1 : 0;
      int isBigBlind = (config->Wants[x].value == bigBlindTag) ? 1 : 0;
      int isVoucher = (config->Wants[x].value == voucher) ? 1 : 0;
      result->ScoreWants[x] += (isSmallBlind + isBigBlind + isVoucher);
    }
    if (smallBlindTag == Double_Tag) {
      dt++;
    }

    if (smallBlindTag != Negative_Tag && ante > 1 && allNeedsMet) {
        //dt++;
        //continue;
    }
    
    int packChecks = (ante == 1) ? 4 : 6;
    if (allNeedsMet) {
      // If all needs are met, we can skip the pack checks
      packChecks = 0;
    }
    // Track if any Arcana Pack was found
    bool foundArcanaPack = false;
    for (int p = 0; p < packChecks; p++) {
        item _pack_item = next_pack(inst, ante);
        pack _pack = pack_info(_pack_item);
        if (_pack.type == Arcana_Pack) {
            foundArcanaPack = true;
        }
        jokerdata jokers[5];
        card stdcards[5];
        item consumables[5];
        switch (_pack.type) {
        case Buffoon_Pack:
          buffoon_pack_detailed(jokers, _pack.size, inst, ante);
          for (int i = 0; i < _pack.size; i++) {
            for (int x = 0; x < clampedNumNeeds; x++) {
              if (config->Needs[x].value == jokers[i].joker &&
                  config->Needs[x].jokeredition == jokers[i].edition) {
                ScoreNeeds[x] = true;
              }
            }
          }
          break;
        case Arcana_Pack:
          arcana_pack(consumables, _pack.size, inst, ante);
          for (int i = 0; i < _pack.size; i++) {
            if (consumables[i] == The_Soul) {
              jokerdata soulJoker = next_joker_with_info(inst, S_Soul, ante);
              for (int x = 0; x < clampedNumNeeds; x++) {
                if (config->Needs[x].value == The_Soul || config->Needs[x].value == soulJoker.joker) {
                  ScoreNeeds[x] = true;
                }
              }
              for (int x = 0; x < clampedNumWants; x++) {
                if (config->Wants[x].value == The_Soul || config->Wants[x].value == soulJoker.joker) {
                  result->ScoreWants[x]++;
                }
              }
            } else {
              for (int x = 0; x < clampedNumNeeds; x++) {
                if (config->Needs[x].value == consumables[i]) {
                  ScoreNeeds[x] = true;
                }
              }
              for (int x = 0; x < clampedNumWants; x++) {
                if (config->Wants[x].value == consumables[i]) {
                  result->ScoreWants[x]++;
                }
              }
            }
          }
          break;
        case Celestial_Pack:
          celestial_pack(consumables, _pack.size, inst, ante);
          for (int i = 0; i < _pack.size; i++) {
            for (int x = 0; x < clampedNumNeeds; x++) {
              if (config->Needs[x].value == consumables[i]) {
                ScoreNeeds[x] = true;
              }
            }
            for (int x = 0; x < clampedNumWants; x++) {
              if (config->Wants[x].value == consumables[i]) {
                result->ScoreWants[x]++;
              }
            }
          }
          break;
        case Spectral_Pack:
          spectral_pack(consumables, _pack.size, inst, ante);
          for (int i = 0; i < _pack.size; i++) {
            for (int x = 0; x < clampedNumNeeds; x++) {
              if (config->Needs[x].value == consumables[i]) {
                ScoreNeeds[x] = true;
              }
            }
          }
          break;
        case Standard_Pack:
          standard_pack(stdcards, _pack.size, inst, ante);
          // Needs/wants for standard packs are not supported in this filter yet.
          break;
        default:
          break;
        }
    }

    if (smallBlindTag == Negative_Tag) {
      // Simulate player choice for using the Negative Tag.
      // The player "waits" for a desired joker to appear, then starts grabbing.
      int grabs = 1 + dt;
      bool isGrabbing = false; // True once the player "chooses" to start.
      
      // Skip the initial two shop jokers -- but may as well check for showman!
      shopitem skip1 = next_shop_item(inst, ante);
      if (skip1.value == Showman) {
          inst->params.showman = true;
      }
      shopitem skip2 = next_shop_item(inst, ante);
      if (skip2.value == Showman) {
          inst->params.showman = true;
      }

      // Loop through the shop, simulating some shop re-rolls to "find" the start of our negative run
      
      int loopAmountDuringGrabCheck = ante*2; // estimating how many shop reroll swe can afford
      for (int rerollCheck = 0; rerollCheck < loopAmountDuringGrabCheck; rerollCheck++) {
        int grabCheckSecondCard = 0; // the reroll of shop shows TWO cards, so we need to "spend" the negative tag regardless of whether we like the first joker, if we do like the second joker
        for (int i = 0; i < 2; i++) {
            shopitem _shopitem = next_shop_item(inst, ante);

            // Break if shop is empty (no more items or rerolls available)
            if (_shopitem.value == RETRY) {
                continue;
            }

            // We can only make No_Edition jokers negative.
            if (_shopitem.type != ItemType_Joker || _shopitem.joker.edition != No_Edition) {
                continue;
            }

            // Check if the current joker is one the player desires.
            bool isDesired = false;
            for (int x = 0; x < clampedNumNeeds; x++) {
                if (_shopitem.type == ItemType_Joker &&
                    config->Needs[x].value == _shopitem.joker.joker &&
                    config->Needs[x].jokeredition == No_Edition) {
                    isDesired = true;
                    break;
                }
            }
            if (!isDesired) {
                for (int x = 0; x < clampedNumWants; x++) {
                    if (_shopitem.type == ItemType_Joker &&
                        config->Wants[x].value == _shopitem.joker.joker &&
                        config->Wants[x].jokeredition == No_Edition) {
                        isDesired = true;
                        break;
                    }
                }
            }

            if (isGrabbing) {
                // Already started grabbing, so this joker consumes a grab.
                grabs--;

                // Only score if it's a desired joker.
                if (isDesired) {
                    for (int x = 0; x < clampedNumNeeds; x++) {
                        if (config->Needs[x].value == _shopitem.joker.joker &&
                            config->Needs[x].jokeredition == No_Edition) {
                            ScoreNeeds[x] = true;
                        }
                    }
                    for (int x = 0; x < clampedNumWants; x++) {
                        if (config->Wants[x].value == _shopitem.joker.joker &&
                            config->Wants[x].jokeredition == No_Edition) {
                            result->ScoreWants[x] += 1;
                            result->DesiredNegativeJokers += 1;
                        }
                    }
                }
                if (grabs <= 0) {
                loopAmountDuringGrabCheck = 0;
                    break; // No more grabs left.
                }
            } else if (isDesired) {
                // This is the first desired joker. The player "chooses" to start grabbing.
                isGrabbing = true;
                grabs--;
                if (grabCheckSecondCard == 1) {
                    grabs--;
                }
                loopAmountDuringGrabCheck += grabs;

                // Score this first joker.
                for (int x = 0; x < clampedNumNeeds; x++) {
                    if (config->Needs[x].value == _shopitem.joker.joker &&
                        config->Needs[x].jokeredition == No_Edition) {
                        ScoreNeeds[x] = true;
                    }
                }
                for (int x = 0; x < clampedNumWants; x++) {
                    if (config->Wants[x].value == _shopitem.joker.joker &&
                        config->Wants[x].jokeredition == No_Edition) {
                        result->ScoreWants[x] += 1;
                        result->DesiredNegativeJokers += 1;
                    }
                }
                if (grabs <= 0) {
                    break; // No more grabs left.
                }
            }
            // If !isGrabbing and !isDesired, we continue, simulating a skip/reroll.
            grabCheckSecondCard++;
        }
        // The Negative Tag is now used up, so reset the Double Tag counter.
        dt = 0;
      }
    }

    if (bigBlindTag == Double_Tag) {
      dt++;
    }
   
    if (config->deck == Anaglyph_Deck)
        dt++;

    // Check per-need ante requirements at the end of each ante
    allNeedsMet = true;
    for (int n = 0; n < clampedNumNeeds; n++) {
      if (ScoreNeeds[n] == false) {
        allNeedsMet = false;
      }

      // A need is not met if its deadline has passed and it's still not scored.
      // We also check that it's a valid need (not RETRY).
      bool needNotMetByRequiredAnte =
          (config->Needs[n].value != RETRY) &&
          (ante >= config->Needs[n].desireByAnte) && 
          (ScoreNeeds[n] == false);

      if (needNotMetByRequiredAnte) {
        valid = false;
        break; // Exit the needs-checking loop
      }
    }

    // After pack loop, check for Charm_Tag and missing Arcana Pack
    if (!foundArcanaPack && smallBlindTag == Charm_Tag) {
        item megaArcana[5];
        arcana_pack(megaArcana, 5, inst, ante);
        for (int i = 0; i < 5; i++) {
            if (megaArcana[i] == The_Soul) {
                jokerdata soulJoker = next_joker_with_info(inst, S_Soul, ante);
                for (int x = 0; x < clampedNumNeeds; x++) {
                    if (config->Needs[x].value == The_Soul || config->Needs[x].value == soulJoker.joker) {
                        ScoreNeeds[x] = true;
                    }
                }
                for (int x = 0; x < clampedNumWants; x++) {
                    if (config->Wants[x].value == The_Soul || config->Wants[x].value == soulJoker.joker) {
                        result->ScoreWants[x]++;
                    }
                }
            } else {
                for (int x = 0; x < clampedNumNeeds; x++) {
                    if (config->Needs[x].value == megaArcana[i]) {
                        ScoreNeeds[x] = true;
                    }
                }
                for (int x = 0; x < clampedNumWants; x++) {
                    if (config->Wants[x].value == megaArcana[i]) {
                        result->ScoreWants[x]++;
                    }
                }
            }
        }
    }
  } // End of ante loop

  // Calculate total score efficiently only if valid
  if (valid) {
    // For this Anaglyph-specific filter, the score is simply the number of desired negative jokers.
    result->TotalScore = result->DesiredNegativeJokers;
  } else {
    // Invalid seed gets zero score
    result->TotalScore = 0;
  }

  // Always perform seed string conversion since filtering is done in host
  text s_str = s_to_string(&inst->seed);

// Use efficient copying
#pragma unroll
  for (int i = 0; i < 9; i++) {
    result->seed[i] = s_str.str[i];
  }

  return;
}
