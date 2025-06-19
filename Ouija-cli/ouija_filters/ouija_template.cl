#include "lib/ouija.cl"

// Helper function to handle The Soul joker from packs
void handle_the_soul(instance *inst, __constant OuijaConfig *config, OuijaResult *result, 
                     int ante, int clampedNumNeeds, int clampedNumWants) {
    jokerdata soulJoker = next_joker_with_info(inst, S_Soul, ante);
    
    if (config->scoreNaturalNegatives) {
        result->NaturalNegativeJokers += (soulJoker.edition == Negative);
    }
    if (config->scoreDesiredNegatives) {
        result->DesiredNegativeJokers += (soulJoker.edition == Negative);
    }
    
    // Check needs
    for (int x = 0; x < clampedNumNeeds; x++) {
        bool soulMatch = config->Needs[x].value == soulJoker.joker;
        bool jokereditionMatch = (config->Needs[x].jokeredition == No_Edition || 
                                  config->Needs[x].jokeredition == soulJoker.edition);
        if (soulMatch && jokereditionMatch) {
            // This would need to be passed by reference or handled differently
            // ScoreNeeds[x] = true;
            if (soulJoker.edition == Negative && config->scoreDesiredNegatives) {
                result->DesiredNegativeJokers += 1;
                result->NaturalNegativeJokers += 1;
            }
        }
    }
    
    // Check wants
    for (int x = 0; x < clampedNumWants; x++) {
        bool soulMatch = config->Wants[x].value == soulJoker.joker;
        bool jokereditionMatch = (config->Wants[x].jokeredition == No_Edition || 
                                  config->Wants[x].jokeredition == soulJoker.edition);
        bool jokerMatch = (config->Wants[x].jokeredition != RETRY) && soulMatch && jokereditionMatch;
        
        if ((soulMatch || jokerMatch) && (result->ScoreWants[x] == 0 || inst->params.showman == true)) {
            result->ScoreWants[x] += 1;
            if (soulJoker.edition == Negative && config->scoreDesiredNegatives) {
                result->DesiredNegativeJokers += 1;
                result->NaturalNegativeJokers += 1;
            }
        }
    }
}

// Helper function to process arcana packs
void process_arcana_pack(instance *inst, __constant OuijaConfig *config, OuijaResult *result,
                         pack _pack, int ante, int clampedNumNeeds, int clampedNumWants, 
                         bool *ScoreNeeds) {
    item tarotCards[5] = {RETRY, RETRY, RETRY, RETRY, RETRY};
    arcana_pack(tarotCards, _pack.size, inst, ante);
    
    for (int t = 0; t < _pack.size; t++) {
        if (tarotCards[t] == RETRY) continue;
        
        if (tarotCards[t] == The_Soul) {
            handle_the_soul(inst, config, result, ante, clampedNumNeeds, clampedNumWants);
        } else {
            // Check needs
            for (int x = 0; x < clampedNumNeeds; x++) {
                if (config->Needs[x].value == tarotCards[t]) {
                    ScoreNeeds[x] = true;
                }
            }
            // Check wants
            for (int x = 0; x < clampedNumWants; x++) {
                if (config->Wants[x].value == tarotCards[t]) {
                    result->ScoreWants[x] += 1;
                }
            }
        }
    }
}

// Helper function to process spectral packs
void process_spectral_pack(instance *inst, __constant OuijaConfig *config, OuijaResult *result,
                           pack _pack, int ante, int clampedNumNeeds, int clampedNumWants,
                           bool *ScoreNeeds) {
    item spectralCards[5] = {RETRY, RETRY, RETRY, RETRY, RETRY};
    spectral_pack(spectralCards, _pack.size, inst, ante);
    
    for (int t = 0; t < _pack.size; t++) {
        if (spectralCards[t] == RETRY) continue;
        
        if (spectralCards[t] == The_Soul) {
            handle_the_soul(inst, config, result, ante, clampedNumNeeds, clampedNumWants);
        } else {
            // Check needs
            for (int x = 0; x < clampedNumNeeds; x++) {
                if (config->Needs[x].value == spectralCards[t]) {
                    ScoreNeeds[x] = true;
                }
            }
            // Check wants
            for (int x = 0; x < clampedNumWants; x++) {
                if (config->Wants[x].value == spectralCards[t]) {
                    result->ScoreWants[x] += 1;
                }
            }
        }
    }
}

// Helper function to process buffoon packs
void process_buffoon_pack(instance *inst, __constant OuijaConfig *config, OuijaResult *result,
                          pack _pack, int ante, int clampedNumNeeds, int clampedNumWants,
                          bool *ScoreNeeds) {
    jokerdata buffoonJokers[5];
    buffoon_pack_detailed(buffoonJokers, _pack.size, inst, ante);
    
    for (int t = 0; t < _pack.size; t++) {
        if (buffoonJokers[t].joker == RETRY) continue;
        
        if (buffoonJokers[t].joker == Showman) {
            inst->params.showman = true;
        }
        
        if (config->scoreNaturalNegatives) {
            result->NaturalNegativeJokers += (buffoonJokers[t].edition == Negative);
        }
        
        bool desiredNegative = false;
        
        // Check needs
        for (int x = 0; x < clampedNumNeeds; x++) {
            bool jokerMatch = (config->Needs[x].jokeredition != RETRY) &&
                            (config->Needs[x].value == buffoonJokers[t].joker) &&
                            ((config->Needs[x].jokeredition == No_Edition) ||
                             (config->Needs[x].jokeredition == buffoonJokers[t].edition));
            if (jokerMatch) {
                ScoreNeeds[x] = true;
                if (buffoonJokers[t].edition == Negative) {
                    desiredNegative = true;
                }
            }
        }
        
        // Check wants
        for (int x = 0; x < clampedNumWants; x++) {
            bool jokerMatch = (config->Wants[x].jokeredition != RETRY) &&
                            (config->Wants[x].value == buffoonJokers[t].joker) &&
                            ((config->Wants[x].jokeredition == No_Edition) ||
                             (config->Wants[x].jokeredition == buffoonJokers[t].edition));
            if (jokerMatch && (result->ScoreWants[x] == 0 || inst->params.showman == true)) {
                result->ScoreWants[x] += 1;
                if (buffoonJokers[t].edition == Negative) {
                    desiredNegative = true;
                }
            }
        }
        
        if (desiredNegative && config->scoreDesiredNegatives) {
            result->DesiredNegativeJokers += 1;
        }
    }
}

// Helper function to check and process a pack
void check_next_pack(instance *inst, __constant OuijaConfig *config, OuijaResult *result,
                     int ante, int clampedNumNeeds, int clampedNumWants, bool *ScoreNeeds) {
    pack _pack = pack_info(next_pack(inst, ante));
    
    if (_pack.type == Arcana_Pack) {
        process_arcana_pack(inst, config, result, _pack, ante, clampedNumNeeds, clampedNumWants, ScoreNeeds);
    } else if (_pack.type == Spectral_Pack) {
        process_spectral_pack(inst, config, result, _pack, ante, clampedNumNeeds, clampedNumWants, ScoreNeeds);
    } else if (_pack.type == Buffoon_Pack) {
        process_buffoon_pack(inst, config, result, _pack, ante, clampedNumNeeds, clampedNumWants, ScoreNeeds);
    }
}

// Helper function to process shop items for an ante
void process_shop_items(instance *inst, __constant OuijaConfig *config, OuijaResult *result,
                        int ante, int clampedNumNeeds, int clampedNumWants, bool *ScoreNeeds) {
    int shCount = (ante == 1) ? 4 : (ante == 2) ? 6 : 8;
    
    for (int sh = 0; sh < shCount; sh++) {
        shopitem shItem = next_shop_item(inst, ante);
        if (shItem.value == RETRY) continue;
        
        if (shItem.value == Showman) {
            inst->params.showman = true;
        }

        if (config->scoreNaturalNegatives) {
            result->NaturalNegativeJokers += (shItem.type == ItemType_Joker && shItem.joker.edition == Negative) ? 1 : 0;
        }

        // Check needs
        for (int x = 0; x < clampedNumNeeds; x++) {
            bool jokerMatch =
                (config->Needs[x].jokeredition != RETRY) &&
                (shItem.type == ItemType_Joker) &&
                (config->Needs[x].value == shItem.value) &&
                ((config->Needs[x].jokeredition == No_Edition) ||
                 (config->Needs[x].jokeredition == shItem.joker.edition));
            bool regularMatch = (shItem.type != ItemType_Joker &&
                                 config->Needs[x].value == shItem.value);
            if (jokerMatch || regularMatch) {
                ScoreNeeds[x] = true;
            }
            if (jokerMatch && shItem.joker.edition == Negative) {
                if (config->scoreNaturalNegatives) {
                    result->NaturalNegativeJokers += 1;
                }
                if (config->scoreDesiredNegatives) {
                    result->DesiredNegativeJokers += 1;
                }
            }
        }
        
        // Check wants
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
}

// Helper function to process an ante
void process_ante(instance *inst, __constant OuijaConfig *config, OuijaResult *result,
                  int ante, int clampedNumNeeds, int clampedNumWants, bool *ScoreNeeds) {
    init_unlocks(inst, ante, false);
    
    // Process voucher
    item voucher = next_voucher(inst, ante);
    if (ante > 1 && voucher != Hieroglyph && voucher != Petroglyph) {
        activate_voucher(inst, voucher);
    }
    
    // Process tags
    item smallBlindTag = next_tag(inst, ante);
    item bigBlindTag = next_tag(inst, ante);
    
    for (int x = 0; x < clampedNumNeeds; x++) {
        bool isSmallBlind = (config->Needs[x].value == smallBlindTag);
        bool isBigBlind = (config->Needs[x].value == bigBlindTag);
        bool isVoucher = (config->Needs[x].value == voucher);
        if (isSmallBlind || isBigBlind || isVoucher) {
            ScoreNeeds[x] = true; 
        }
    }
    
    for (int x = 0; x < clampedNumWants; x++) {
        int isSmallBlind = (config->Wants[x].value == smallBlindTag) ? 1 : 0;
        int isBigBlind = (config->Wants[x].value == bigBlindTag) ? 1 : 0;
        int isVoucher = (config->Wants[x].value == voucher) ? 1 : 0;
        result->ScoreWants[x] += (isSmallBlind + isBigBlind + isVoucher);
    }
    
    // Process shop items
    process_shop_items(inst, config, result, ante, clampedNumNeeds, clampedNumWants, ScoreNeeds);
    
    // Process packs
    int packChecks = (ante == 1) ? 4 : 6;
    for (int p = 0; p < packChecks; p++) {
        check_next_pack(inst, config, result, ante, clampedNumNeeds, clampedNumWants, ScoreNeeds);
    }
}

// Helper function to process erratic deck
bool process_erratic_deck(instance *inst, __constant OuijaConfig *config, OuijaResult *result,
                          int clampedNumNeeds, int clampedNumWants, bool *ScoreNeeds) {
    item deck[52];
    init_deck(inst, deck);
    
    for (int i = 0; i < 52; i++) {
        item r = rank(deck[i]);
        item s = suit(deck[i]);
        
        // Check wants
        for (int w = 0; w < clampedNumWants; w++) {
            if (r == config->Wants[w].value || s == config->Wants[w].value) {
                result->ScoreWants[w] += 1;
                if (result->ScoreWants[w] > result->TotalScore) {
                    result->TotalScore = result->ScoreWants[w];
                }
            }
        }
        
        // Check needs
        for (int n = 0; n < clampedNumNeeds; n++) {
            if (r == config->Needs[n].value || s == config->Needs[n].value) {
                ScoreNeeds[n] = true;
            }
        }
    }
    
    // If the score is less than 10, we can skip the ante loop
    if (result->TotalScore < 10) {
        return false;
    }
    
    return true;
}

// Main filter function
OuijaResult ouija_filter(instance *inst, __constant OuijaConfig *config) {
    // Create local result to return
    OuijaResult result;

    // Initialize result struct efficiently
    bool valid = true;
    result.TotalScore = 1;
    result.NaturalNegativeJokers = 0;
    result.DesiredNegativeJokers = 0;

    // Initialize ScoreWants array explicitly
    for (int i = 0; i < MAX_DESIRES_KERNEL; i++) {
        result.ScoreWants[i] = 0;
    }

    // Clamp numNeeds and numWants defensively
    int clampedNumNeeds = config->numNeeds;
    int clampedNumWants = config->numWants;
    if (clampedNumNeeds > MAX_DESIRES_KERNEL) clampedNumNeeds = MAX_DESIRES_KERNEL;
    if (clampedNumNeeds < 0) clampedNumNeeds = 0;
    if (clampedNumWants > MAX_DESIRES_KERNEL) clampedNumWants = MAX_DESIRES_KERNEL;
    if (clampedNumWants < 0) clampedNumWants = 0;

    set_deck(inst, config->deck);
    set_stake(inst, config->stake);
    init_locks(inst, 1, false, true);

    bool ScoreNeeds[MAX_DESIRES_KERNEL] = {false};
    int maxSearchAnte = config->maxSearchAnte;

    // Handle erratic deck
    if (config->deck == Erratic_Deck) {
        valid = process_erratic_deck(inst, config, &result, clampedNumNeeds, clampedNumWants, ScoreNeeds);
    }

    // Process each ante
    for (int ante = 1; ante <= maxSearchAnte && valid; ante++) {
        process_ante(inst, config, &result, ante, clampedNumNeeds, clampedNumWants, ScoreNeeds);

        // Check per-need ante requirements at the end of each ante
        for (int n = 0; n < clampedNumNeeds; n++) {
            bool needNotMetByRequiredAnte =
                (ante >= config->Needs[n].desireByAnte) && ScoreNeeds[n] == false;

            if (needNotMetByRequiredAnte) {
                valid = false;
                break;
            }
        }
    }

    // Calculate total score efficiently only if valid
    if (valid) {
        // Efficiently calculate score from wants
        int wants_score = 0;
        for (int w = 0; w < clampedNumWants; w++) {
            // Combine operations to reduce branches
            wants_score += (result.ScoreWants[w] > 0) + result.ScoreWants[w];
        }

        result.TotalScore += wants_score;
        if (config->scoreNaturalNegatives) {
            result.TotalScore += result.NaturalNegativeJokers;
        }
        if (config->scoreDesiredNegatives) {
            result.TotalScore += result.DesiredNegativeJokers;
        }
    } else {
        // Invalid seed gets zero score
        result.TotalScore = 0;
    }

    // Always perform seed string conversion
    text s_str = s_to_string(&inst->seed);

    // Use efficient copying
    #pragma unroll
    for (int i = 0; i < 9; i++) {
        result.seed[i] = s_str.str[i];
    }

    return result;
}
