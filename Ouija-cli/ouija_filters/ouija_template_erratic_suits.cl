#include "lib/ouija.cl"

OuijaResult ouija_filter(instance *inst, __constant OuijaConfig *config) {
  set_deck(inst, Erratic_Deck);

  // Create local result to return
  OuijaResult result;

  int suit_counts[4] = {0, 0, 0, 0};
  item deck[52];
  init_deck(inst, deck);

  // Simple approach: count each rank directly
  int max_score = 0;
#pragma unroll
  for (int i = 0; i < 52; i++) {
    int rank_index = suit(deck[i]) - Hearts;
    int new_count = ++suit_counts[rank_index];
    if (new_count > max_score) {
      max_score = new_count;
    }
  }

#pragma unroll
  for (int i = 0; i < 4; i++) {
    result.ScoreWants[i] = suit_counts[i];
  }

  result.TotalScore = max_score;
  result.NaturalNegativeJokers = 0;
  result.DesiredNegativeJokers = 0;

  // Convert seed to string
  text s_str = s_to_string(&inst->seed);

// Copy seed string efficiently
#pragma unroll
  for (int i = 0; i < 9; i++) {
    result.seed[i] = s_str.str[i];
  }
  
  return result;
}
