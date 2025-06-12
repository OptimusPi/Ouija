/**
 * @file ouija_config.cl
 * @brief Definition of the OuijaConfig structure shared between host and device
 */

#ifndef OUIJA_CONFIG_H
#define OUIJA_CONFIG_H

#include "lib/ouija.cl" // Include the necessary headers for item and jokerdata types

// Enhanced desire structure with per-item ante requirement
typedef struct {
    item value;               // Item or Joker ID
    item jokeredition;        // Edition of the joker, or RETRY if not a joker
    int desireByAnte;         // Ante by which this item should be found (Changed back to int)
} Desire;

typedef struct {
    int numNeeds;                      // Number of Needs (Changed back to int)
    int numWants;                      // Number of Wants (Changed back to int)
    Desire Needs[MAX_DESIRES_KERNEL];  // Array of Needs
    Desire Wants[MAX_DESIRES_KERNEL];  // Array of Wants
    int maxSearchAnte;                 // Maximum Ante to search through (Changed back to int)
    item deck;                         // Deck to use
    item stake;                        // Stake to use
    bool scoreNaturalNegatives;    // Score jokers that are naturally negative
    bool scoreDesiredNegatives;   // Score desired jokers that are naturally negative or from skip tag negative mechanic
} OuijaConfig;

#endif
