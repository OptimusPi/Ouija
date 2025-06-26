#include "lib/ouija.cl"
#include "lib/ouija_config.cl" 
#include "lib/ouija_result.cl" 

void ouija_filter(instance *inst, __constant OuijaConfig *config, __global OuijaResult *result);

// Optimized kernel with coalesced memory access and better work distribution
__kernel void ouija_search(char8 starting_seed_char8,
                           long num_seeds_for_this_dispatch,
                           __constant OuijaConfig *config,
                           __global OuijaResult *results,
                           long batch_seed_offset) {
    
    // Get work-item info
    size_t gid = get_global_id(0);
    size_t lid = get_local_id(0);
    size_t group_id = get_group_id(0);
    size_t group_size = get_local_size(0);
    
    // Early exit for out-of-bounds work items
    if (gid >= num_seeds_for_this_dispatch) {
        return;
    }
    
    // Optimize seed distribution for coalesced access
    // Instead of sequential seeds per work-item, we stripe them
    // This ensures neighboring work-items process neighboring memory
    size_t seeds_per_workitem = (num_seeds_for_this_dispatch + get_global_size(0) - 1) / get_global_size(0);
    size_t my_start_seed = gid * seeds_per_workitem;
    size_t my_end_seed = min(my_start_seed + seeds_per_workitem, (size_t)num_seeds_for_this_dispatch);
    
    // Initialize base seed
    seed base_seed = s_new_c8(starting_seed_char8);
    
    // Process multiple seeds per work-item for better efficiency
    for (size_t seed_idx = my_start_seed; seed_idx < my_end_seed; seed_idx++) {
        // Calculate absolute seed position
        size_t absolute_offset = batch_seed_offset + seed_idx;
        
        // Create seed for this iteration
        seed current_seed = base_seed;
        s_skip(&current_seed, absolute_offset);
        
        // Create instance and run filter
        instance inst = i_new(current_seed);
        
        // Clear result first (important for sparse results)
        results[seed_idx].seed[0] = '\0';
        results[seed_idx].TotalScore = 0;
        
        // Run the filter
        ouija_filter(&inst, config, &results[seed_idx]);
    }
    
    // Memory fence to ensure all writes complete
    barrier(CLK_GLOBAL_MEM_FENCE);
}

// Alternative kernel for AMD GPUs with wavefront-optimized access
__kernel void ouija_search_amd(char8 starting_seed_char8,
                               long num_seeds_for_this_dispatch,
                               __constant OuijaConfig *config,
                               __global OuijaResult *results,
                               long batch_seed_offset) {
    
    size_t gid = get_global_id(0);
    size_t lid = get_local_id(0);
    
    // AMD wavefront size is 64
    const size_t WAVEFRONT_SIZE = 64;
    size_t wavefront_id = lid / WAVEFRONT_SIZE;
    size_t lane_id = lid % WAVEFRONT_SIZE;
    
    // Calculate seeds to process with wavefront-aligned access
    size_t seeds_per_wave = (num_seeds_for_this_dispatch + get_global_size(0) - 1) / get_global_size(0);
    size_t wave_start = (gid / WAVEFRONT_SIZE) * WAVEFRONT_SIZE * seeds_per_wave;
    size_t my_seed_idx = wave_start + lane_id;
    
    seed base_seed = s_new_c8(starting_seed_char8);
    
    // Process seeds with coalesced access within wavefront
    for (size_t i = 0; i < seeds_per_wave && my_seed_idx < num_seeds_for_this_dispatch; i++) {
        size_t absolute_offset = batch_seed_offset + my_seed_idx;
        
        seed current_seed = base_seed;
        s_skip(&current_seed, absolute_offset);
        
        instance inst = i_new(current_seed);
        
        // Clear and process
        results[my_seed_idx].seed[0] = '\0';
        results[my_seed_idx].TotalScore = 0;
        ouija_filter(&inst, config, &results[my_seed_idx]);
        
        // Move to next seed with wavefront stride
        my_seed_idx += WAVEFRONT_SIZE;
    }
    
    barrier(CLK_GLOBAL_MEM_FENCE);
}

// Optimized kernel for NVIDIA GPUs with warp-level optimization
__kernel void ouija_search_nvidia(char8 starting_seed_char8,
                                  long num_seeds_for_this_dispatch,
                                  __constant OuijaConfig *config,
                                  __global OuijaResult *results,
                                  long batch_seed_offset) {
    
    size_t gid = get_global_id(0);
    size_t lid = get_local_id(0);
    
    // NVIDIA warp size is 32
    const size_t WARP_SIZE = 32;
    size_t warp_id = lid / WARP_SIZE;
    size_t lane_id = lid % WARP_SIZE;
    
    // Warp-aligned seed distribution
    size_t seeds_per_warp = (num_seeds_for_this_dispatch + get_global_size(0) - 1) / get_global_size(0);
    size_t warp_start = (gid / WARP_SIZE) * WARP_SIZE * seeds_per_warp;
    size_t my_seed_idx = warp_start + lane_id;
    
    seed base_seed = s_new_c8(starting_seed_char8);
    
    // Process with warp-coalesced access
    for (size_t i = 0; i < seeds_per_warp && my_seed_idx < num_seeds_for_this_dispatch; i++) {
        size_t absolute_offset = batch_seed_offset + my_seed_idx;
        
        seed current_seed = base_seed;
        s_skip(&current_seed, absolute_offset);
        
        instance inst = i_new(current_seed);
        
        results[my_seed_idx].seed[0] = '\0';
        results[my_seed_idx].TotalScore = 0;
        ouija_filter(&inst, config, &results[my_seed_idx]);
        
        my_seed_idx += WARP_SIZE;
    }
    
    barrier(CLK_GLOBAL_MEM_FENCE);
}

// High-throughput kernel for simple filters
__kernel void ouija_search_simple(char8 starting_seed_char8,
                                  long num_seeds_for_this_dispatch,
                                  __constant OuijaConfig *config,
                                  __global OuijaResult *results,
                                  long batch_seed_offset,
                                  __local OuijaResult *local_results) {
    
    size_t gid = get_global_id(0);
    size_t lid = get_local_id(0);
    size_t group_size = get_local_size(0);
    
    // Each work-item processes multiple seeds
    const int SEEDS_PER_ITEM = 16;
    size_t my_start = gid * SEEDS_PER_ITEM;
    
    seed base_seed = s_new_c8(starting_seed_char8);
    
    // Process seeds in chunks
    for (int i = 0; i < SEEDS_PER_ITEM && (my_start + i) < num_seeds_for_this_dispatch; i++) {
        size_t seed_idx = my_start + i;
        size_t absolute_offset = batch_seed_offset + seed_idx;
        
        seed current_seed = base_seed;
        s_skip(&current_seed, absolute_offset);
        
        instance inst = i_new(current_seed);
        
        // Use local memory for temporary storage
        local_results[lid * SEEDS_PER_ITEM + i].seed[0] = '\0';
        local_results[lid * SEEDS_PER_ITEM + i].TotalScore = 0;
        
        ouija_filter(&inst, config, &local_results[lid * SEEDS_PER_ITEM + i]);
    }
    
    // Sync before writing back
    barrier(CLK_LOCAL_MEM_FENCE);
    
    // Coalesced write back to global memory
    for (int i = 0; i < SEEDS_PER_ITEM && (my_start + i) < num_seeds_for_this_dispatch; i++) {
        size_t seed_idx = my_start + i;
        results[seed_idx] = local_results[lid * SEEDS_PER_ITEM + i];
    }
    
    barrier(CLK_GLOBAL_MEM_FENCE);
}