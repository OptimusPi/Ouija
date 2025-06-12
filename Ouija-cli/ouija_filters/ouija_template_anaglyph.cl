#include "lib/ouija.cl"

void ouija_filter(instance *inst, __constant OuijaConfig *config,
                  __global OuijaResult *result) {
  bool valid = true;
  // Initialize result struct
  result->TotalScore = 1;
  result->NaturalNegativeJokers = 0;
  result->DesiredNegativeJokers = 0;

  // Initialize ScoreWants array
  for (int i = 0; i < MAX_DESIRES_KERNEL; i++) {
    result->ScoreWants[i] = 0;
  }

  // Clamp parameters
  int clampedNumNeeds = min(max(config->numNeeds, 0), MAX_DESIRES_KERNEL);
  int clampedNumWants = min(max(config->numWants, 0), MAX_DESIRES_KERNEL);

  set_deck(inst, config->deck);
  set_stake(inst, config->stake);
  init_locks(inst, 1, false, true);
  bool ScoreNeeds[MAX_DESIRES_KERNEL] = {false};
  int maxSearchAnte = config->maxSearchAnte;
  int totalDoubleTags = 0;

  // Joker slot management
  int jokerSlots = 5;  // Start with 5 joker slots
  int filledSlots = 0; // Track how many slots are filled

  // Negative tag tracking
  int negativeTagApplications = 0; // Available negative tag applications
  bool zoneTriggered = false; // Whether we are in the trigger zone

  for (int ante = 1; ante <= maxSearchAnte && valid; ante++) {
    init_unlocks(inst, ante, false);

    // Handle voucher and its effects on joker slots
    item voucher = next_voucher(inst, ante);
    item smallBlindTag = next_tag(inst, ante);

    // Check if negative tag is triggered and calculate applications
    if (smallBlindTag == Negative_Tag) {
      // Search wants for the first tag no matter what kind it is:
      for (int x = 0; x < clampedNumWants; x++) {
        if (config->Wants[x].value == Negative_Tag) {
          result->ScoreWants[x] += 1;
        }
      }
      // Negative tag gives 1 + totalDoubleTags applications
      negativeTagApplications = 1 + totalDoubleTags;
    } else {
      negativeTagApplications = 0; // Reset if not negative tag
    }

    // Count double tags
    if (smallBlindTag == Double_Tag) {
      totalDoubleTags++;
    }

    // Score needs for tags and vouchers
    for (int x = 0; x < clampedNumNeeds; x++) {
      bool isSmallBlind = (config->Needs[x].value == smallBlindTag);
      bool isVoucher = (config->Needs[x].value == voucher);
      ScoreNeeds[x] |= (isSmallBlind | isVoucher);
    }

    // Score wants for tags and vouchers
    for (int x = 0; x < clampedNumWants; x++) {
      if (config->Wants[x].value == smallBlindTag || config->Wants[x].value == voucher) {
          result->ScoreWants[x] += 1;
      }
    }

    // Process shop items
    int shCount = (ante == 1) ? 4 : 6;
    bool inTriggerZone = false;
    if (negativeTagApplications > 0 && smallBlindTag == Negative_Tag) {
      shCount += ante;
    }
    for (int sh = 0; sh < shCount; sh++) {
      shopitem shItem = next_shop_item(inst, ante);
      if (shItem.value == RETRY)
        continue;

      if (shItem.value == Showman) {
        inst->params.showman = true;
      }      
      if (shItem.type == ItemType_Joker) {
        // Score negative jokers based on config flags
        bool isNaturallyNegative = (shItem.joker.edition == Negative);
        bool isDesiredJoker = false;

        // Check if this joker is in our wants list (desired)
        for (int x = 0; x < clampedNumWants; x++) {
          if ((config->Wants[x].jokeredition != RETRY) &&
              (config->Wants[x].value == shItem.joker.joker) &&
              ((config->Wants[x].jokeredition == No_Edition) ||
               (config->Wants[x].jokeredition == shItem.joker.edition))) {
            isDesiredJoker = true;
            break;
          }
        }

        // Check if we can make this joker negative via skip tag mechanics
        // This happens when we have negative tag applications available and can skip to make jokers negative
        if (negativeTagApplications > 0 && isDesiredJoker && smallBlindTag == Negative_Tag && sh > 1) {
            inTriggerZone = true; // We are now in the trigger zone
        }

        bool canBeMadeNegative = false; // Can this joker be made negative?
        if (inTriggerZone){
          if(negativeTagApplications > 0) {
            canBeMadeNegative = true;
          }
          else {
            inTriggerZone = false; // Exit trigger zone after using applications
          }
        }
        
        // Score based on config flags
        if (config->scoreNaturalNegatives && isNaturallyNegative) {
          result->NaturalNegativeJokers += 1;
        }
        if (config->scoreDesiredNegatives && isDesiredJoker && (isNaturallyNegative || canBeMadeNegative)) {
          result->DesiredNegativeJokers += 1;
        }
      } else {
        for (int x = 0; x < clampedNumNeeds; x++) {
          if (config->Needs[x].value == shItem.value && shItem.type != ItemType_Joker) {
            ScoreNeeds[x] = true;
          }
        }
      }

      // Score wants from shop with proper slot management
      for (int x = 0; x < clampedNumWants; x++) {
        bool jokerMatch =
            (shItem.type == ItemType_Joker) &&
            (config->Wants[x].jokeredition != RETRY) &&
            (config->Wants[x].value == shItem.joker.joker) &&
            ((config->Wants[x].jokeredition == No_Edition) ||
             (config->Wants[x].jokeredition == shItem.joker.edition));
        bool regularMatch = (config->Wants[x].value == shItem.value) &&
                            (shItem.type != ItemType_Joker);

        if (config->Wants[x].value == shItem.value && shItem.type != ItemType_Joker) {
          result->ScoreWants[x] += 1;        
        }
      }
    }

    // Get big blind tag and store for next ante's transition check
    item bigBlindTag = next_tag(inst, ante);

    // Search wants for the first tag no matter what kind it is:
    for (int x = 0; x < clampedNumWants; x++) {
      if (config->Wants[x].value == bigBlindTag && bigBlindTag != Negative_Tag) {
        result->ScoreWants[x] += 1;
      }
      if (config->Wants[x].value == smallBlindTag && smallBlindTag != Negative_Tag) {
        result->ScoreWants[x] += 1;
      }
    }

    // And Needs
    for (int x = 0; x < clampedNumNeeds; x++) {
      if (config->Needs[x].value == bigBlindTag && bigBlindTag != Negative_Tag) {
        ScoreNeeds[x] = true;
      }
      if (config->Needs[x].value == smallBlindTag && smallBlindTag != Negative_Tag) {
        ScoreNeeds[x] = true;
      }
    }

    if (bigBlindTag == Double_Tag) {
      totalDoubleTags++;
    }

    // Anaglyph deck gets +1 free double tag after beating each boss blind
    if (config->deck == Anaglyph_Deck) {
      totalDoubleTags++;
    }

    // Check per-need ante requirements
    for (int n = 0; n < clampedNumNeeds; n++) {
      bool needNotMetByRequiredAnte =
          (ante == config->Needs[n].desireByAnte) && ScoreNeeds[n] == false;
      if (needNotMetByRequiredAnte) {
        valid = false;
        break;
      }
    }
  }  // Calculate final score
  if (valid) {
    int wants_score = 0;
    for (int w = 0; w < clampedNumWants; w++) {
      wants_score += result->ScoreWants[w] > 0 ? 1 : 0;
    }
    result->TotalScore += wants_score;
    
    // Add negative joker scores based on configuration
    if (config->scoreNaturalNegatives) {
      result->TotalScore += result->NaturalNegativeJokers;
    }
    if (config->scoreDesiredNegatives) {
      result->TotalScore += result->DesiredNegativeJokers;
    }

    text s_str = s_to_string(&inst->seed);
    for (int i = 0; i < 9; i++) {
      result->seed[i] = s_str.str[i];
    }
  } else {
    result->TotalScore = 0;
  }
}
