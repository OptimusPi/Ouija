#include "lib/ouija.cl"
// #define CACHE_SIZE 800
// #define _debugPrintsMAGIC
// #define _debugPrints1

void ouija_filter(instance *inst, __constant OuijaConfig *config,
                  __global OuijaResult *result) {

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

  if (config->deck == Erratic_Deck) {
    item deck[52];
    init_deck(inst, deck);
    int bestScore = 0;
    for (int i = 0; i < 52; i++) {
      item r = rank(deck[i]);
      item s = suit(deck[i]);
      for (int w = 0; w < clampedNumWants; w++) {
        if (r == config->Wants[w].value || s == config->Wants[w].value) {
          result->ScoreWants[w] += 1;
          if (result->ScoreWants[w] > result->TotalScore) {
            result->TotalScore = result->ScoreWants[w];
          }
        }
      }
      for (int n = 0; n < clampedNumNeeds; n++) {
        if (r == config->Needs[n].value || s == config->Needs[n].value) {
          ScoreNeeds[n] = true;
        }
      }
    }
    if (result->TotalScore < 10) {
      // If the score is less than 10, we can skip the ante loop
      valid = false;
    }
  }

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
    int shCount = (ante == 1) ? 4 : (ante == 2) ? 6 : 8;
    for (int sh = 0; sh < shCount; sh++) {
      shopitem shItem = next_shop_item(inst, ante);
      if (shItem.value == RETRY)
        continue;
      if (shItem.value == Showman)
        inst->params.showman = true;

      if (config->scoreNaturalNegatives) {
        result->NaturalNegativeJokers += (shItem.type == ItemType_Joker && shItem.joker.edition == Negative) ? 1 : 0;
      }

      for (int x = 0; x < clampedNumNeeds; x++) {
        bool jokerMatch =
            (config->Needs[x].jokeredition != RETRY) &&
            (shItem.type == ItemType_Joker) &&
            (config->Needs[x].value == shItem.value) &&
            ((config->Needs[x].jokeredition == No_Edition) ||
             (config->Needs[x].jokeredition == shItem.joker.edition));
        bool regularMatch = (shItem.type != ItemType_Joker &&
                             config->Needs[x].value == shItem.value);
        if (jokerMatch || regularMatch)
          ScoreNeeds[x] = true;
        if (jokerMatch && shItem.joker.edition == Negative) {
          if (config->scoreNaturalNegatives) {
            result->NaturalNegativeJokers += 1;
          }
          if (config->scoreDesiredNegatives) {
            result->DesiredNegativeJokers += 1;
          }
        }
      }
      for (int x = 0; x < clampedNumWants; x++) {       
        int jokerMatch =
            (config->Wants[x].jokeredition != RETRY) &&
            (shItem.type == ItemType_Joker) &&
            (config->Wants[x].value == shItem.value) &&
            ((config->Wants[x].jokeredition == No_Edition) ||
             (config->Wants[x].jokeredition == shItem.joker.edition));
        int regularMatch = (shItem.type != ItemType_Joker &&
                            config->Wants[x].value == shItem.value);        
        if (jokerMatch && (result->ScoreWants[x] == 0 || inst->params.showman == true)) {
          result->ScoreWants[x] += 1;
        }
        result->ScoreWants[x] += regularMatch ? 1 : 0;
      }
    }
    int packChecks = (ante == 1) ? 4 : 6;
    // Track if any Arcana Pack was found
    bool foundArcanaPack = false;
    for (int p = 0; p < packChecks; p++) {
      pack _pack = pack_info(next_pack(inst, ante));
      jokerdata jokers[5];
      item arcanaCards[5];
      item spectralCards[5];
      switch (_pack.type) {
        case Buffoon_Pack:
          buffoon_pack_detailed(jokers, _pack.size, inst, ante);
          for (int t = 0; t < _pack.size; t++) {
            if (jokers[t].joker == RETRY) continue;
            if (jokers[t].joker == Showman) inst->params.showman = true;
            if (config->scoreNaturalNegatives) {
              result->NaturalNegativeJokers += (jokers[t].edition == Negative);
            }
            bool desiredNegative = false;
            for (int x = 0; x < clampedNumNeeds; x++) {
              bool jokerMatch =
                (config->Needs[x].jokeredition != RETRY) &&
                (config->Needs[x].value == jokers[t].joker) &&
                ((config->Needs[x].jokeredition == No_Edition) ||
                 (config->Needs[x].jokeredition == jokers[t].edition));
              if (jokerMatch) ScoreNeeds[x] = true;
              if (jokerMatch && jokers[t].edition == Negative) desiredNegative = true;
            }
            for (int x = 0; x < clampedNumWants; x++) {
              bool jokerMatch =
                (config->Wants[x].jokeredition != RETRY) &&
                (config->Wants[x].value == jokers[t].joker) &&
                ((config->Wants[x].jokeredition == No_Edition) ||
                 (config->Wants[x].jokeredition == jokers[t].edition));
              if (jokerMatch && (result->ScoreWants[x] == 0 || inst->params.showman == true)) {
                result->ScoreWants[x] += 1;
              }
              if (jokerMatch && jokers[t].edition == Negative) desiredNegative = true;
            }
            if (desiredNegative && config->scoreDesiredNegatives) {
              result->DesiredNegativeJokers += 1;
            }
          }
          break;
        case Arcana_Pack:
          arcana_pack(arcanaCards, _pack.size, inst, ante);
          for (int t = 0; t < _pack.size; t++) {
            if (arcanaCards[t] == RETRY) continue;
            if (arcanaCards[t] == The_Soul) {
              jokerdata soulJoker = next_joker_with_info(inst, S_Soul, ante);
              if (soulJoker.joker == RETRY) continue;
              bool isNegative = soulJoker.edition == Negative;
              bool isDesiredNegative = false;
              if (config->scoreNaturalNegatives && isNegative) {
                result->NaturalNegativeJokers += 1;
              }
              for (int x = 0; x < clampedNumNeeds; x++) {
                bool soulMatch = (config->Needs[x].value == The_Soul);
                bool jokerMatch =
                  (config->Needs[x].jokeredition != RETRY) &&
                  (config->Needs[x].value == soulJoker.joker) &&
                  ((config->Needs[x].jokeredition == No_Edition) ||
                   (config->Needs[x].jokeredition == soulJoker.edition));
                if (soulMatch || jokerMatch) {
                  ScoreNeeds[x] = true;
                  if (jokerMatch && isNegative) isDesiredNegative = true;
                }
              }
              for (int x = 0; x < clampedNumWants; x++) {
                bool soulMatch = (config->Wants[x].value == The_Soul);
                bool jokerMatch =
                  (config->Wants[x].jokeredition != RETRY) &&
                  (config->Wants[x].value == soulJoker.joker) &&
                  ((config->Wants[x].jokeredition == No_Edition) ||
                   (config->Wants[x].jokeredition == soulJoker.edition));
                if (soulMatch || jokerMatch) {
                  if (result->ScoreWants[x] == 0 || inst->params.showman == true) {
                    result->ScoreWants[x] += 1;
                  }
                  if (jokerMatch && isNegative) isDesiredNegative = true;
                }
              }
              if (config->scoreDesiredNegatives && isDesiredNegative) {
                result->DesiredNegativeJokers += 1;
              }
            } else {
              for (int x = 0; x < clampedNumNeeds; x++) {
                bool matched = (config->Needs[x].value == arcanaCards[t]);
                ScoreNeeds[x] |= matched;
              }
              for (int x = 0; x < clampedNumWants; x++) {
                result->ScoreWants[x] += (config->Wants[x].value == arcanaCards[t]);
              }
            }
          }
          foundArcanaPack = true;
          break;
        case Spectral_Pack:
          spectral_pack(spectralCards, _pack.size, inst, ante);
          for (int t = 0; t < _pack.size; t++) {
            if (spectralCards[t] == RETRY) continue;
            if (spectralCards[t] == The_Soul) {
              jokerdata soulJoker = next_joker_with_info(inst, S_Soul, ante);
              if (soulJoker.joker == RETRY) continue;
              bool isNegative = soulJoker.edition == Negative;
              bool isDesiredNegative = false;
              if (config->scoreNaturalNegatives && isNegative) {
                result->NaturalNegativeJokers += 1;
              }
              for (int x = 0; x < clampedNumNeeds; x++) {
                bool soulMatch = (config->Needs[x].value == The_Soul);
                bool jokerMatch =
                  (config->Needs[x].jokeredition != RETRY) &&
                  (config->Needs[x].value == soulJoker.joker) &&
                  ((config->Needs[x].jokeredition == No_Edition) ||
                   (config->Needs[x].jokeredition == soulJoker.edition));
                if (soulMatch || jokerMatch) {
                  ScoreNeeds[x] = true;
                  if (jokerMatch && isNegative) isDesiredNegative = true;
                }
              }
              for (int x = 0; x < clampedNumWants; x++) {
                bool soulMatch = (config->Wants[x].value == The_Soul);
                bool jokerMatch =
                  (config->Wants[x].jokeredition != RETRY) &&
                  (config->Wants[x].value == soulJoker.joker) &&
                  ((config->Wants[x].jokeredition == No_Edition) ||
                   (config->Wants[x].jokeredition == soulJoker.edition));
                if (soulMatch || jokerMatch) {
                  if (result->ScoreWants[x] == 0 || inst->params.showman == true) {
                    result->ScoreWants[x] += 1;
                  }
                  if (jokerMatch && isNegative) isDesiredNegative = true;
                }
              }
              if (config->scoreDesiredNegatives && isDesiredNegative) {
                result->DesiredNegativeJokers += 1;
              }
            } else {
              for (int x = 0; x < clampedNumNeeds; x++) {
                if (config->Needs[x].value == spectralCards[t]) {
                  ScoreNeeds[x] = true;
                }
              }
              for (int x = 0; x < clampedNumWants; x++) {
                result->ScoreWants[x] += config->Wants[x].value == spectralCards[t] ? 1 : 0;
              }
            }
          }
          break;
        default:
          break;
      }
    }

    // After pack loop, check for Charm_Tag and missing Arcana Pack
    if (!foundArcanaPack && smallBlindTag == Charm_Tag) {
      item megaArcana[5];
      arcana_pack(megaArcana, 5, inst, ante);
      for (int i = 0; i < 5; i++) {
        // Handle The_Soul and other cards as you do in your normal Arcana_Pack logic
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

    // Check per-need ante requirements at the end of each ante
    for (int n = 0; n < clampedNumNeeds; n++) {
      bool needNotMetByRequiredAnte =
          (ante >= config->Needs[n].desireByAnte) && ScoreNeeds[n] == false;

      if (needNotMetByRequiredAnte) {
        valid = false;
        break;
      }
    }
  } // End of ante loop

  // Calculate total score efficiently only if valid
  if (valid) {
    // Efficiently calculate score from wants
    int wants_score = 0;
    for (int w = 0; w < clampedNumWants; w++) {
      // Combine operations to reduce branches
      wants_score += (result->ScoreWants[w] > 0) + result->ScoreWants[w];
    }

    result->TotalScore += wants_score;
    if (config->scoreNaturalNegatives) {
      // Add natural negative jokers to total score
      result->TotalScore += result->NaturalNegativeJokers;
    }
    if (config->scoreDesiredNegatives) {
      // Add desired negative jokers to total score
      result->TotalScore += result->DesiredNegativeJokers;
    }
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
