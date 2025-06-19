#include "lib/ouija.h"
#include "lib/host_items.h"
#include "lib/ouija_config_loader.h"
#include "lib/ouija_host_result.h"
#include "lib/utils.h"

#include <time.h>
#include <CL/cl.h>
#include <assert.h>
#include <inttypes.h>
#include <string.h>
#include <stdbool.h>

#define DEFAULT_BATCH_MULTIPLIER 1

// Cross-platform compatibility
#ifndef _WIN32
    #include <sys/stat.h>
    #define fopen_s(pFile, filename, mode) ((*(pFile) = fopen((filename), (mode))) ? 0 : errno)
#endif

// Helper function to create binary path
void createBinaryPath(const char *executable_dir, const char *filter_name, char *binary_path, size_t max_len)
{
    char filter_dir_path[MAX_PATH];
    snprintf(filter_dir_path, MAX_PATH, "%s%souija_filters", executable_dir, PATH_SEPARATOR);
    
#ifdef _WIN32
    CreateDirectoryA(filter_dir_path, NULL);
#else
    mkdir(filter_dir_path, 0755);
#endif

    snprintf(binary_path, max_len, "%s%souija_filters%s%s.bin", 
             executable_dir, PATH_SEPARATOR, PATH_SEPARATOR, filter_name);
}

// AMD device check
static bool is_amd_device(cl_device_id device) {
    char vendor[256] = {0};
    clGetDeviceInfo(device, CL_DEVICE_VENDOR, sizeof(vendor), vendor, NULL);
    return (strstr(vendor, "AMD") != NULL || strstr(vendor, "Advanced Micro") != NULL);
}

// Determine optimal local work size based on vendor
static size_t get_optimal_work_group_size(cl_device_id device, cl_kernel kernel, bool is_amd) {
    size_t preferred_multiple = 0;
    clGetKernelWorkGroupInfo(kernel, device, CL_KERNEL_PREFERRED_WORK_GROUP_SIZE_MULTIPLE,
                              sizeof(size_t), &preferred_multiple, NULL);
    size_t max_wg_size = 0;
    clGetDeviceInfo(device, CL_DEVICE_MAX_WORK_GROUP_SIZE, 
                    sizeof(size_t), &max_wg_size, NULL);
    if (is_amd) {
        const size_t wave = 64;
        size_t opt = preferred_multiple ? preferred_multiple : wave;
        opt = (opt / wave) * wave;
        if (opt == 0) opt = wave;
        return opt;
    } else {
        const size_t warp = 32;
        size_t opt = preferred_multiple ? preferred_multiple : warp;
        opt = (opt / warp) * warp;
        if (opt == 0) opt = warp;
        return opt;
    }
}

int main(int argc, char **argv)
{
    // Print version
    printf_s("Ouija-CLI Beta v0.4.3\n");
    printf_s("pifreak loves you!\n");
    fflush(stdout);

    // Handle CLI arguments
    unsigned int platformID = 0;
    unsigned int deviceID = 0;
    size_t numGroups = 16;
    cl_char8 startingSeed;
    for (int i = 0; i < 8; i++) {
        startingSeed.s[i] = '\0';    }
    cl_long numSeeds = 1000000000;  // Reasonable default: 1 billion seeds
    int cutoff = 1;
    int auto_cutoff_mode = 0;
    
    // Default config values
    OuijaConfig config;
    config.numNeeds = 0;
    config.numWants = 0;
    config.maxSearchAnte = 8;
    cl_uint batchMultiplier = DEFAULT_BATCH_MULTIPLIER;    char *filter = "ouija_template";  // default filter
    char filter_name_clean[MAX_PATH];
    strcpy_s(filter_name_clean, MAX_PATH, filter);
    size_t filter_len = strlen(filter_name_clean);
    if (filter_len > 6 && strcmp(filter_name_clean + filter_len - 6, "_fixed") == 0) {
        filter_name_clean[filter_len - 6] = '\0';
    }
    char *config_file = NULL;

    // --- Argument Parsing Loop ---
    for (int i = 0; i < argc; i++) {
        if (strcmp(argv[i], "-h") == 0) {
            printf_s("Valid command line arguments:\n"
                    "-h        Shows this help dialog.\n"
                    "-f <F>    Sets the filter used by Ouija to F. Defaults to ouija_template\n"
                    "-s <S>    Sets the starting seed to S. Defaults to empty seed. Use \"random\" for a random starting seed.\n"
                    "-n <N>    Sets the number of seeds to search to N. Defaults to full seed pool.\n"
                    "-c <C>    Sets the cutoff score for filtering results. Use 'auto' for dynamic cutoff. Defaults to 1.\n"
                    "-p <P>    Sets the platform ID of the CL device being used to P. Defaults to 0.\n"
                    "-d <D>    Sets the device ID of the CL device being used to D. Defaults to 0.\n"
                    "-g <G>    Sets the number of thread groups to G. Defaults to 16.\n"
                    "-b <B>    Sets batch multiplier to B. Higher values process more seeds per batch. Defaults to 100.\n"
                    "--config <JSON>  Load configuration from a JSON file.\n"
                    "--list_devices   Lists information about the detected CL devices.\n");
            return 0;
        }
        if (strcmp(argv[i], "--config") == 0 && i + 1 < argc) {
            config_file = argv[i + 1];
            i++;
        }
        if (strcmp(argv[i], "-b") == 0 && i + 1 < argc) {
            batchMultiplier = (cl_uint)atoi(argv[i + 1]);
            i++;
        }
        if (strcmp(argv[i], "-p") == 0 && i + 1 < argc) {
            platformID = atoi(argv[i + 1]);
            i++;
        }
        if (strcmp(argv[i], "-f") == 0 && i + 1 < argc) {
            filter = argv[i + 1];
            i++;
        }
        if (strcmp(argv[i], "-d") == 0 && i + 1 < argc) {
            deviceID = atoi(argv[i + 1]);
            i++;
        }
        if (strcmp(argv[i], "-g") == 0 && i + 1 < argc) {
            numGroups = atoi(argv[i + 1]);
            i++;
        }
        if (strcmp(argv[i], "-n") == 0 && i + 1 < argc) {
            numSeeds = strtoll(argv[i + 1], NULL, 10);
            i++;
        }
        if (strcmp(argv[i], "-c") == 0 && i + 1 < argc) {
            if (strcmp(argv[i + 1], "auto") == 0) {
                auto_cutoff_mode = 1;
                cutoff = 1;
                printf_s("Cutoff set to AUTO (dynamic)\n");
            } else {
                cutoff = atoi(argv[i + 1]);
                auto_cutoff_mode = 0;
                printf_s("Cutoff set to %d\n", cutoff);
            }
            i++;
        }
        if (strcmp(argv[i], "-s") == 0 && i + 1 < argc) {
            if (strcmp(argv[i + 1], "random") == 0 || strlen(argv[i + 1]) > 8) {
                srand((unsigned int)time(NULL));
                char seedCharacters[] = "123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ";
                for (int j = 0; j < 8; j++) {
                    startingSeed.s[j] = seedCharacters[rand() % 35];
                }
            } else {
                int seedLength = (int)strlen(argv[i + 1]);
                for (int j = 0; j < seedLength; j++) {
                    startingSeed.s[j] = argv[i + 1][j];
                }
                for (int j = seedLength; j < 8; j++) {
                    startingSeed.s[j] = '\0';
                }
            }
            // Print the seed
            char seedStr[9] = {0};
            for (int j = 0; j < 8 && startingSeed.s[j] != '\0'; j++) {
                seedStr[j] = startingSeed.s[j];
            }
            printf_s("Starting seed set to %s\n", seedStr);
            fflush(stdout);
            i++;
        }
        if (strcmp(argv[i], "--list_devices") == 0) {
            cl_int err;
            cl_uint numPlatforms;
            
            err = clGetPlatformIDs(0, NULL, &numPlatforms);
            if (err != CL_SUCCESS || numPlatforms == 0) {
                printf_s("No OpenCL devices found.\n");
                return 0;
            }

            cl_platform_id *platforms = malloc(sizeof(cl_platform_id) * numPlatforms);
            err = clGetPlatformIDs(numPlatforms, platforms, NULL);
            
            for (unsigned int p = 0; p < numPlatforms; p++) {
                cl_uint numDevices;
                err = clGetDeviceIDs(platforms[p], CL_DEVICE_TYPE_ALL, 0, NULL, &numDevices);
                if (err != CL_SUCCESS || numDevices == 0) continue;

                cl_device_id *devices = malloc(sizeof(cl_device_id) * numDevices);
                err = clGetDeviceIDs(platforms[p], CL_DEVICE_TYPE_ALL, numDevices, devices, NULL);

                for (unsigned int d = 0; d < numDevices; d++) {
                    printf_s("\nPlatform ID %i, Device ID %i\n", p, d);

                    char name_buf[1024];
                    char vendor_buf[1024];
                    cl_uint compute_units;
                    cl_uint max_freq;
                    
                    clGetDeviceInfo(devices[d], CL_DEVICE_NAME, sizeof(name_buf), name_buf, NULL);
                    printf_s("Name: %s\n", name_buf);
                    
                    clGetDeviceInfo(devices[d], CL_DEVICE_VENDOR, sizeof(vendor_buf), vendor_buf, NULL);
                    printf_s("Vendor: %s\n", vendor_buf);
                    
                    clGetDeviceInfo(devices[d], CL_DEVICE_MAX_COMPUTE_UNITS, sizeof(compute_units), &compute_units, NULL);
                    printf_s("Compute Units: %u\n", compute_units);
                    
                    clGetDeviceInfo(devices[d], CL_DEVICE_MAX_CLOCK_FREQUENCY, sizeof(max_freq), &max_freq, NULL);
                    printf_s("Clock Frequency: %uMHz\n", max_freq);
                }
                free(devices);
            }
            free(platforms);
            return 0;        }
    }

    // Load configuration if specified
    if (config_file != NULL) {
        if (!load_config_from_json(config_file, &config)) {
            printf_s("Failed to load configuration from %s. Using defaults.\n", config_file);
        } else {
            printf_s("Configuration loaded: %d needs, %d wants, max ante %d\n",
                     config.numNeeds, config.numWants, config.maxSearchAnte);
        }
    }

    // Validate config
    if (config.numNeeds > MAX_DESIRES_HOST) config.numNeeds = MAX_DESIRES_HOST;
    if (config.numWants > MAX_DESIRES_HOST) config.numWants = MAX_DESIRES_HOST;

    // --- OpenCL Setup ---
    cl_int err;
    
    // Get platforms
    cl_uint numPlatforms;
    err = clGetPlatformIDs(0, NULL, &numPlatforms);
    if (err != CL_SUCCESS || numPlatforms == 0 || platformID >= numPlatforms) {
        printf_s("Platform %u not found.\n", platformID);
        return 1;
    }

    cl_platform_id *platforms = malloc(sizeof(cl_platform_id) * numPlatforms);
    clGetPlatformIDs(numPlatforms, platforms, NULL);
    cl_platform_id platform = platforms[platformID];

    // Get devices
    cl_uint numDevices;
    err = clGetDeviceIDs(platform, CL_DEVICE_TYPE_ALL, 0, NULL, &numDevices);
    if (err != CL_SUCCESS || numDevices == 0 || deviceID >= numDevices) {
        printf_s("Device %u not found on platform %u.\n", deviceID, platformID);
        free(platforms);
        return 1;
    }

    cl_device_id *devices = malloc(sizeof(cl_device_id) * numDevices);
    clGetDeviceIDs(platform, CL_DEVICE_TYPE_ALL, numDevices, devices, NULL);
    cl_device_id device = devices[deviceID];

    // Get device info for batch sizing
    cl_uint compute_units = 32; // Default
    clGetDeviceInfo(device, CL_DEVICE_MAX_COMPUTE_UNITS, sizeof(compute_units), &compute_units, NULL);
    printf_s("Using device with %u compute units\n", compute_units);

    // --- Check if device is AMD and determine optimal sizes ---
    bool amd = is_amd_device(device);

    // Create context and queue
    cl_context ctx = clCreateContext(NULL, 1, &device, NULL, NULL, &err);
    if (err != CL_SUCCESS) {
        printf_s("Failed to create OpenCL context\n");
        free(devices);
        free(platforms);
        return 1;
    }

    cl_command_queue queue = clCreateCommandQueue(ctx, device, 0, &err);
    if (err != CL_SUCCESS) {
        printf_s("Failed to create command queue\n");
        clReleaseContext(ctx);
        free(devices);
        free(platforms);
        return 1;
    }

    // --- Load/Build Kernel ---
    char executable_dir[MAX_PATH];
    char kernel_path[MAX_PATH];
    char binary_path[MAX_PATH];
    char include_path[MAX_PATH + 6];
    
    getExecutableDir(executable_dir);
    snprintf(include_path, sizeof(include_path), "-I \"%s\"", executable_dir);
    createBinaryPath(executable_dir, filter_name_clean, binary_path, MAX_PATH);

    cl_program ssKernelProgram = NULL;
    FILE *fp = NULL;
    
    // Try to load binary first
    if (fopen_s(&fp, binary_path, "rb") == 0 && fp != NULL) {
        fseek(fp, 0, SEEK_END);
        size_t binary_size = ftell(fp);
        rewind(fp);
        
        if (binary_size > 0) {
            unsigned char *binary_data = malloc(binary_size);
            if (fread(binary_data, 1, binary_size, fp) == binary_size) {
                cl_int binary_status;
                ssKernelProgram = clCreateProgramWithBinary(ctx, 1, &device,
                                                           &binary_size,
                                                           (const unsigned char **)&binary_data,
                                                           &binary_status, &err);
                if (err != CL_SUCCESS || binary_status != CL_SUCCESS) {
                    if (ssKernelProgram) clReleaseProgram(ssKernelProgram);
                    ssKernelProgram = NULL;
                }
            }
            free(binary_data);
        }
        fclose(fp);
    }

    // If no binary, compile from source    
    if (!ssKernelProgram) {
        printf_s("Building kernel from source for filter: %s\n", filter_name_clean);
        snprintf(kernel_path, sizeof(kernel_path), "%s%slib\\ouija_search.cl", executable_dir, PATH_SEPARATOR);
        
        // Open source file
        if (fopen_s(&fp, kernel_path, "r") != 0) {
            printf_s("ERROR: Failed to open kernel source file: %s\n", kernel_path);
            clReleaseCommandQueue(queue);
            clReleaseContext(ctx);
            free(devices);
            free(platforms);
            return 1;
        }
        
        // Load kernel source
        char *kernel_code = malloc(MAX_CODE_SIZE);
        snprintf(kernel_code, MAX_CODE_SIZE, "#include \"ouija_filters/%s.cl\"\n\n", filter_name_clean);
        
        size_t current_len = strlen(kernel_code);
        size_t bytes_read = fread(kernel_code + current_len, 1, MAX_CODE_SIZE - current_len - 1, fp);
        kernel_code[current_len + bytes_read] = '\0';
        fclose(fp);

        size_t kernel_size = strlen(kernel_code);
        ssKernelProgram = clCreateProgramWithSource(ctx, 1, (const char **)&kernel_code, &kernel_size, &err);
        free(kernel_code);
        
        if (err != CL_SUCCESS) {
            printf_s("Failed to create program from source\n");
            clReleaseCommandQueue(queue);
            clReleaseContext(ctx);
            free(devices);
            free(platforms);
            return 1;
        }
    }

    // Build program
    err = clBuildProgram(ssKernelProgram, 1, &device, include_path, NULL, NULL);
    if (err != CL_SUCCESS) {
        size_t log_size;
        clGetProgramBuildInfo(ssKernelProgram, device, CL_PROGRAM_BUILD_LOG, 0, NULL, &log_size);
        char *log = malloc(log_size);
        clGetProgramBuildInfo(ssKernelProgram, device, CL_PROGRAM_BUILD_LOG, log_size, log, NULL);
        printf_s("Build failed:\n%s\n", log);
        free(log);
        clReleaseProgram(ssKernelProgram);
        clReleaseCommandQueue(queue);
        clReleaseContext(ctx);
        free(devices);
        free(platforms);
        return 1;
    }

    // Save binary if we compiled from source
    if (fp) { // fp was set if we compiled from source
        size_t binary_size;
        clGetProgramInfo(ssKernelProgram, CL_PROGRAM_BINARY_SIZES, sizeof(size_t), &binary_size, NULL);
        if (binary_size > 0) {
            unsigned char *binary = malloc(binary_size);
            unsigned char *binaries[1] = {binary};
            clGetProgramInfo(ssKernelProgram, CL_PROGRAM_BINARIES, sizeof(unsigned char *), binaries, NULL);
            
            if (fopen_s(&fp, binary_path, "wb") == 0) {
                fwrite(binary, 1, binary_size, fp);
                fclose(fp);
                printf_s("Saved compiled kernel to cache\n");
            }
            free(binary);
        }
    }    
    
    // Create kernel
    cl_kernel ssKernel = clCreateKernel(ssKernelProgram, "ouija_search", &err);
    if (err != CL_SUCCESS) {
        printf_s("Failed to create kernel\n");
        clReleaseProgram(ssKernelProgram);
        clReleaseCommandQueue(queue);
        clReleaseContext(ctx);
        free(devices);
        free(platforms);
        return 1;
    }

    // Handle kernel pre-compilation case (numSeeds = 0)
    if (numSeeds == 0) {
        printf_s("Kernel pre-compilation mode detected (numSeeds = 0)\n");
        printf_s("Kernel compiled and cached successfully. Exiting.\n");
        clReleaseKernel(ssKernel);
        clReleaseProgram(ssKernelProgram);
        clReleaseCommandQueue(queue);
        clReleaseContext(ctx);
        free(devices);
        free(platforms);
        return 0;
    }

    // Use the cleaned filter name, not the raw input, for consistency
    const char *filter_to_print = filter_name_clean;
    printf_s("Using filter: %s\n", filter_to_print);

    // Check work group size
    size_t max_work_group_size;
    clGetKernelWorkGroupInfo(ssKernel, device, CL_KERNEL_WORK_GROUP_SIZE, 
                            sizeof(size_t), &max_work_group_size, NULL);
    if (numGroups > max_work_group_size) {
        numGroups = max_work_group_size;
        printf_s("Adjusted work group size to %zu\n", numGroups);
    }
    
    // --- Create Buffers ---    // Calculate reasonable number of work-items (NOT all seeds!)
    // Each work-item will process many seeds and return only the best result
    size_t compute_units_limit = compute_units > 64 ? 64 : compute_units; // Cap at 64 CUs
    size_t work_items_per_batch = numGroups * compute_units_limit * batchMultiplier; // Use user's batch multiplier
    
    // Only apply minimum work-items for NVIDIA GPUs (they need warp-aligned sizes)
    if (!amd) {  // Assume non-AMD = NVIDIA for now
        size_t min_work_items = 32 * compute_units; // NVIDIA warp size = 32
        if (work_items_per_batch < min_work_items) {
            work_items_per_batch = min_work_items;
            printf_s("[DEBUG] Increased work_items_per_batch to minimum NVIDIA-friendly size: %zu\n", work_items_per_batch);
        }
    }
    
    // Buffer size is now work-items, not total seeds processed!
    size_t buffer_capacity = work_items_per_batch; // Each work-item returns 1 result
      printf_s("[DEBUG] numGroups=%zu, compute_units=%u (limited to %zu)\n", 
             numGroups, compute_units, compute_units_limit);
    printf_s("[DEBUG] work_items_per_batch=%zu\n", work_items_per_batch);
    printf_s("[DEBUG] Batch calculation: numGroups(%zu) * compute_units(%u) * batchMultiplier(%u) = %zu seeds per batch\n",
             numGroups, compute_units, batchMultiplier, (size_t)numGroups * compute_units * batchMultiplier);
    printf_s("[DEBUG] Each work-item processes ~%" PRId64 " seeds\n", 
             (numSeeds + work_items_per_batch - 1) / work_items_per_batch);printf_s("Buffer size: %" PRId64 " results (~%.1f MB)\n", 
             buffer_capacity, (buffer_capacity * sizeof(OuijaHostResult)) / (1024.0 * 1024.0));
    
    // Config buffer (small, read-only, so traditional buffer is fine)
    cl_mem configBuf = clCreateBuffer(ctx, CL_MEM_READ_ONLY, sizeof(OuijaConfig), NULL, &err);
    clEnqueueWriteBuffer(queue, configBuf, CL_TRUE, 0, sizeof(OuijaConfig), &config, 0, NULL, NULL);
    
    // --- AMD-safe buffer and work group sizes ---
    // Check device limits and adjust buffer and work group sizes for AMD
    size_t max_alloc = 0;
    clGetDeviceInfo(device, CL_DEVICE_MAX_MEM_ALLOC_SIZE, sizeof(max_alloc), &max_alloc, NULL);
    size_t max_results = (size_t)(max_alloc * (amd ? 0.4 : 0.9)) / sizeof(OuijaHostResult);
    size_t batch_capacity = buffer_capacity < max_results ? buffer_capacity : max_results;
    size_t local_work_size = get_optimal_work_group_size(device, ssKernel, amd);
    size_t global_work_size = ((batch_capacity + local_work_size - 1) / local_work_size) * local_work_size;

    // Create results buffer with AMD-safe capacity
    cl_mem resultsBuf = clCreateBuffer(ctx, CL_MEM_WRITE_ONLY, sizeof(OuijaHostResult) * batch_capacity, NULL, &err);
    if (err != CL_SUCCESS) {
        printf_s("ERROR: Failed to allocate results buffer: %d\n", err);
        clReleaseKernel(ssKernel);
        clReleaseProgram(ssKernelProgram);
        clReleaseMemObject(configBuf);
        clReleaseCommandQueue(queue);
        clReleaseContext(ctx);
        free(devices);
        free(platforms);
        return 1;
    }
    
    // Host memory for results
    OuijaHostResult* results = (OuijaHostResult*)malloc(sizeof(OuijaHostResult) * batch_capacity);

    // Set static kernel arguments (arguments that don't change per batch)
    clSetKernelArg(ssKernel, 0, sizeof(cl_char8), &startingSeed);
    clSetKernelArg(ssKernel, 2, sizeof(cl_mem), &configBuf);
    clSetKernelArg(ssKernel, 3, sizeof(cl_mem), &resultsBuf);
    
    // Print CSV header - output headers for the configured wants
    printf_s("+Seed,Score");
    if (config.scoreNaturalNegatives) printf_s(",Natural Negative Jokers");
    if (config.scoreDesiredNegatives) printf_s(",Desired Negative Jokers");
      // Output headers for configured wants only
    for (cl_int w = 0; w < config.numWants; w++) {
        printf_s(",");
        if (config.Wants[w].jokeredition != RETRY && config.Wants[w].jokeredition != No_Edition) {
            print_item_host(config.Wants[w].jokeredition);
            printf_s("_");
            print_item_host(config.Wants[w].value);
        } else {
            print_item_host(config.Wants[w].value);
        }
    }
    printf_s("\n");
    fflush(stdout);
    // Variables for seed loop, timing, and results
    clock_t start_time, last_report;
    cl_long seeds_remaining, current_offset, total_processed, total_found;
    int first_batch;// Initialize timing and counters
    start_time = clock();
    last_report = start_time;

    seeds_remaining = numSeeds;
    current_offset = 0;
    total_processed = 0;
    total_found = 0;
    first_batch = 1;

    // Handle kernel pre-compilation case (numSeeds = 0)
    if (numSeeds == 0) {
        printf_s("Kernel pre-compilation complete. Exiting.\n");
        
        // Cleanup
        free(results);
        clReleaseMemObject(resultsBuf);
        clReleaseMemObject(configBuf);
        clReleaseKernel(ssKernel);
        clReleaseProgram(ssKernelProgram);
        clReleaseCommandQueue(queue);
        clReleaseContext(ctx);
        free(devices);
        free(platforms);
        
        return 0;
    }    printf_s("Starting search of %" PRId64 " seeds...\n", numSeeds);
    
    while (seeds_remaining > 0) {        
        // Calculate proper batch size using user parameters:
        // batch_size = numGroups (-g) * compute_units (auto-detected) * batchMultiplier (-b)
        cl_long proper_batch_size = (cl_long)numGroups * (cl_long)compute_units * (cl_long)batchMultiplier;
        
        // Use the smaller of: proper batch size or remaining seeds
        cl_long batch_size = seeds_remaining < proper_batch_size ? seeds_remaining : proper_batch_size;
          // Calculate how many seeds each work-item should process
        cl_long seeds_per_work_item = (batch_size + work_items_per_batch - 1) / work_items_per_batch;
        if (seeds_per_work_item < 1) seeds_per_work_item = 1;

        printf_s("[DEBUG] Processing batch: offset=%" PRId64 ", batch_size=%" PRId64 ", seeds_per_work_item=%" PRId64 "\n",
                 current_offset, batch_size, seeds_per_work_item);

        // Update kernel arguments
        clSetKernelArg(ssKernel, 1, sizeof(cl_long), &batch_size);
        clSetKernelArg(ssKernel, 4, sizeof(cl_long), &current_offset);

        // Clear the results buffer before each kernel launch (0 = no result found)
        memset(results, 0, sizeof(OuijaHostResult) * buffer_capacity);
        err = clEnqueueWriteBuffer(queue, resultsBuf, CL_TRUE, 0, 
                                   sizeof(OuijaHostResult) * buffer_capacity, 
                                   results, 0, NULL, NULL);
        if (err != CL_SUCCESS) {
            printf_s("Error clearing results buffer: %d\n", err);
            break;
        }

        // Launch kernel - let OpenCL choose optimal work-group size
        size_t global_work_size = work_items_per_batch;
        err = clEnqueueNDRangeKernel(queue, ssKernel, 1, NULL,
                                     &global_work_size, NULL, 0, NULL, NULL);
        if (err != CL_SUCCESS) {
            printf_s("Kernel launch failed: %d\n", err);
            break;
        }
        clFinish(queue);

        // Read results from device
        err = clEnqueueReadBuffer(queue, resultsBuf, CL_TRUE, 0,
                                  sizeof(OuijaHostResult) * buffer_capacity, results, 0, NULL, NULL);
        if (err != CL_SUCCESS) {
            printf_s("Failed to read results buffer: %d\n", err);
            break;
        }        // Process results
        int batch_high_score = cutoff;
        for (size_t i = 0; i < buffer_capacity; i++) {
            if (results[i].TotalScore == 0) continue; // Skip invalid results
            if (results[i].TotalScore > batch_high_score) {
                batch_high_score = results[i].TotalScore;
            }
            // For manual cutoff (-c param), include results >= cutoff (inclusive)
            if (results[i].TotalScore >= cutoff) {
                total_found++;
                printf_s("|%s,%d", results[i].seed, results[i].TotalScore);
                if (config.scoreNaturalNegatives) printf_s(",%d", results[i].NaturalNegativeJokers);
                if (config.scoreDesiredNegatives) printf_s(",%d", results[i].DesiredNegativeJokers);
                for (int w = 0; w < config.numWants; w++) {
                    printf_s(",%d", (int)results[i].ScoreWants[w]);
                }
                printf_s("\n");
            }
        }
        fflush(stdout);

        // Adjust cutoff dynamically
        if (auto_cutoff_mode && batch_high_score > cutoff) {
            cutoff = batch_high_score;
        }
        first_batch = 0;

        // Update counters
        total_processed += batch_size;
        current_offset += batch_size;
        seeds_remaining -= batch_size;

        // Report progress every 5s or on last batch
        clock_t current_time = clock();
        if ((double)(current_time - last_report) / CLOCKS_PER_SEC >= 5.0 || seeds_remaining <= 0) {
            double elapsed = (double)(current_time - start_time) / CLOCKS_PER_SEC;
            double rate = total_processed / elapsed;
            double percent = (total_processed * 100.0) / numSeeds;
            printf_s("[PROGRESS] %.1f%% - %" PRId64 "/%" PRId64 " seeds processed, %" PRId64 " found @%.1f seeds/s\n",
                     percent, total_processed, numSeeds, total_found, rate);
            fflush(stdout);
            last_report = current_time;
        }
    }

    // Final report
    double total_time = (double)(clock() - start_time) / CLOCKS_PER_SEC;
    printf_s("$Search Complete! Found %" PRId64 " viable out of %" PRId64 " total seeds @%.1f seeds/s\n",
             total_found, total_processed,
             (total_time > 0.0) ? (total_processed / total_time) : 0.0);
    fflush(stdout);    // --- Cleanup ---
    free(results);
    clReleaseMemObject(resultsBuf);
    clReleaseMemObject(configBuf);
    clReleaseKernel(ssKernel);
    clReleaseProgram(ssKernelProgram);
    clReleaseCommandQueue(queue);
    clReleaseContext(ctx);
    free(devices);
    free(platforms);
    
    return 0;
}