#include "lib/ouija.cl"

void ouija_filter(instance *inst, __constant OuijaConfig *config, __global OuijaResult *result) {
  result->NaturalNegativeJokers = 0;
  int maxAnte = config->maxSearchAnte == 0 ? 8 : config->maxSearchAnte;
  int bestScore = 0;
  for (int ante = 1; ante <= maxAnte; ante++) {
    int anteScore = 0;
    for (int i = 0; i < 8; i++) {
      if (next_joker_edition(inst, S_Soul, ante) == Negative) {
        anteScore += 1;
        if (anteScore > bestScore) {
          bestScore = anteScore;
        }
      } else {
        i=8;
      }
    }
  }
  result->TotalScore = bestScore;
  
  // Convert seed to string
  text s_str = s_to_string(&inst->seed);
  
  // Copy seed string efficiently 
  #pragma unroll
  for (int i = 0; i < 9; i++) {
    result->seed[i] = s_str.str[i];
  }
}