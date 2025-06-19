#include "lib/ouija.cl"
#include "lib/ouija_config.cl" 
#include "lib/ouija_result.cl" 

OuijaResult ouija_filter(instance *inst, __constant OuijaConfig *config);

__kernel void ouija_search(char8 starting_seed_char8, // Renamed to avoid conflict with seed type
                           long num_seeds_for_this_dispatch, // Total seeds this kernel dispatch should handle
                           __constant OuijaConfig *config,
                           __global OuijaResult *results, // Note: OuijaResult and OuijaHostResult are binary compatible
                           long batch_seed_offset) { // Changed from pointer to value
    size_t current_global_id = get_global_id(0); // Original OpenCL type: size_t
    size_t total_global_size = get_global_size(0); // Original OpenCL type: size_t
    
    // Calculate seeds per work-item (block-based distribution)
    long seeds_per_work_item = (num_seeds_for_this_dispatch + total_global_size - 1) / total_global_size;
    
    // Calculate starting offset for this work-item
    long work_item_start_offset = batch_seed_offset + (current_global_id * seeds_per_work_item);
    
    // Initialize seed and skip to starting position (expensive but done once per work-item)
    seed _seed = s_new_c8(starting_seed_char8);
    s_skip(&_seed, work_item_start_offset);    // Initialize best result for this work-item (local reduction)
    OuijaResult best_result;
    best_result.TotalScore = 0; // Use max value as "no result found" sentinel
    for (int i = 0; i < 9; i++) best_result.seed[i] = '\0'; // Clear seed
    
    // Process multiple seeds in this work-item, keeping only the best
    for (long i = 0; i < seeds_per_work_item; i++) {
        // Check bounds
        long current_seed_index = work_item_start_offset + i - batch_seed_offset;
        if (current_seed_index >= num_seeds_for_this_dispatch) {
            break; // Don't process beyond the batch
        }
        
        // Process this seed
        instance inst = i_new(_seed);
        OuijaResult temp_result = ouija_filter(&inst, config);
        
        // Keep the best result (highest score)
        if (temp_result.TotalScore > best_result.TotalScore) {
            best_result = temp_result;
        }
        
        // Advance to next seed (only 1 step - much faster)
        s_next(&_seed);
    }
    
    // Store the best result from this work-item
    results[current_global_id] = best_result;
    
    // Sync at end of batch to ensure all work-items complete before returning
    barrier(CLK_GLOBAL_MEM_FENCE);
}