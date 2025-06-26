#include "lib/ouija.cl"

void ouija_filter(instance *inst, __constant OuijaConfig *config, OuijaResult *result) {
  set_deck(inst, Erratic_Deck);
  
  // Fixed order: _2, _3, _4, _5, _6, _7, _8, _9, _10, Jack, Queen, King, Ace
  // This means we can directly map rank_counts[0..12] to ScoreWants[0..12]
  int rank_counts[13] = {0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0};
  item deck[52];
  init_deck(inst, deck);
  
  // Simple approach: count each rank directly
  int max_score = 0;
  #pragma unroll
  for (int i = 0; i < 52; i++) {
    int rank_index = rank(deck[i]) - _2;  // 0-12 for _2 through Ace
    int new_count = ++rank_counts[rank_index];
    if (new_count > max_score) {
      max_score = new_count;
    }
  }
  
  // Direct assignment since we know the exact order
  // ScoreWants[0] = count of _2, ScoreWants[1] = count of _3, etc.
  #pragma unroll
  for (int i = 0; i < 13; i++) {
    result->ScoreWants[i] = rank_counts[i];
  }
  
  result->TotalScore = max_score;
  result->NaturalNegativeJokers = 0;
  result->DesiredNegativeJokers = 0;
  
  // Convert seed to string
  text s_str = s_to_string(&inst->seed);
  
  // Copy seed string efficiently 
  #pragma unroll
  for (int i = 0; i < 9; i++) {
    result->seed[i] = s_str.str[i];
  }
}
