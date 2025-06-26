#include "lib/ouija.h"
#include "lib/host_items.h"
#include "lib/ouija_config_loader.h"
#include "lib/ouija_host_result.h"
#include "lib/utils.h"

#include <time.h>
#include <CL/cl.h>
#include <assert.h>
#include <inttypes.h>

#define DEFAULT_BATCH_MULTIPLIER 100
#define MAX_RESULTS_PER_BATCH 65536  // Conservative for sparse results

// Cross-platform compatibility
#ifndef _WIN32
    #include <sys/stat.h>
    #define fopen_s(pFile, filename, mode) ((*(pFile) = fopen((filename), (mode))) ? 0 : errno)
#endif

// Vendor detection for optimization
typedef enum {
    VENDOR_UNKNOWN = 0,
    VENDOR_NVIDIA,
    VENDOR_AMD,
    VENDOR_INTEL
} gpu_vendor_t;

gpu_vendor_t detect_vendor(cl_device_id device) {
    char vendor[256];
    clGetDeviceInfo(device, CL_DEVICE_VENDOR, sizeof(vendor), vendor, NULL);
    
    if (strstr(vendor, "NVIDIA")) return VENDOR_NVIDIA;
    if (strstr(vendor, "AMD") || strstr(vendor, "Advanced Micro")) return VENDOR_AMD;
    if (strstr(vendor, "Intel")) return VENDOR_INTEL;
    return VENDOR_UNKNOWN;
}

// Safe buffer size calculation to prevent AMD crashes
size_t calculate_safe_batch_size(cl_device_id device, gpu_vendor_t vendor, size_t base_size) {
    cl_ulong max_alloc, global_mem;
    clGetDeviceInfo(device, CL_DEVICE_MAX_MEM_ALLOC_SIZE, sizeof(cl_ulong), &max_alloc, NULL);
    clGetDeviceInfo(device, CL_DEVICE_GLOBAL_MEM_SIZE, sizeof(cl_ulong), &global_mem, NULL);
    
    // Conservative limits by vendor to prevent crashes
    size_t vendor_limit;
    switch(vendor) {
        case VENDOR_AMD:
            // AMD crashes above 25% in practice despite reporting 50%
            vendor_limit = global_mem / 4;
            break;
        case VENDOR_INTEL:
            // Intel benefits from page-aligned smaller buffers
            vendor_limit = global_mem / 8;
            break;
        case VENDOR_NVIDIA:
        default:
            // NVIDIA is most stable but still enforce 25% limit
            vendor_limit = global_mem / 4;
            break;
    }
    
    size_t safe_size = (max_alloc < vendor_limit) ? max_alloc : vendor_limit;
    size_t result_size = sizeof(OuijaHostResult) * base_size;
    
    // Ensure we don't exceed safe limits
    while (result_size > safe_size && base_size > 1024) {
        base_size /= 2;
        result_size = sizeof(OuijaHostResult) * base_size;
    }
    
    return base_size;
}

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

int main(int argc, char **argv)
{
    // Print version
    printf_s("Ouija-CLI Optimized v0.5.0\n");
    printf_s("Now with vendor-specific optimizations!\n");
    fflush(stdout);

    // Handle CLI arguments
    unsigned int platformID = 0;
    unsigned int deviceID = 0;
    size_t numGroups = 0;  // 0 = auto-detect
    cl_char8 startingSeed;
    for (int i = 0; i < 8; i++) {
        startingSeed.s[i] = '\0';
    }
    cl_long numSeeds = 2318107019761;
    int cutoff = 1;
    int auto_cutoff_mode = 0;
    int use_double_buffer = 1;  // New: enable double buffering by default
    
    // Default config values
    OuijaConfig config;
    config.numNeeds = 0;
    config.numWants = 0;
    config.maxSearchAnte = 8;
    cl_uint batchMultiplier = DEFAULT_BATCH_MULTIPLIER;

    char *filter = "ouija_template";
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
                    "-g <G>    Sets the number of thread groups to G. Auto-detects if 0. Defaults to 0.\n"
                    "-b <B>    Sets batch multiplier to B. Higher values process more seeds per batch. Defaults to 100.\n"
                    "--no-double-buffer  Disables double buffering (not recommended).\n"
                    "--config <JSON>  Load configuration from a JSON file.\n"
                    "--list_devices   Lists information about the detected CL devices.\n");
            return 0;
        }
        if (strcmp(argv[i], "--no-double-buffer") == 0) {
            use_double_buffer = 0;
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
            printf_s("   Starting seed set to %s\n", seedStr);
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
                    cl_ulong global_mem;
                    
                    clGetDeviceInfo(devices[d], CL_DEVICE_NAME, sizeof(name_buf), name_buf, NULL);
                    printf_s("Name: %s\n", name_buf);
                    
                    clGetDeviceInfo(devices[d], CL_DEVICE_VENDOR, sizeof(vendor_buf), vendor_buf, NULL);
                    printf_s("Vendor: %s\n", vendor_buf);
                    
                    gpu_vendor_t vendor = detect_vendor(devices[d]);
                    printf_s("Detected as: %s\n", 
                            vendor == VENDOR_NVIDIA ? "NVIDIA" :
                            vendor == VENDOR_AMD ? "AMD" :
                            vendor == VENDOR_INTEL ? "Intel" : "Unknown");
                    
                    clGetDeviceInfo(devices[d], CL_DEVICE_MAX_COMPUTE_UNITS, sizeof(compute_units), &compute_units, NULL);
                    printf_s("Compute Units: %u\n", compute_units);
                    
                    clGetDeviceInfo(devices[d], CL_DEVICE_MAX_CLOCK_FREQUENCY, sizeof(max_freq), &max_freq, NULL);
                    printf_s("Clock Frequency: %uMHz\n", max_freq);
                    
                    clGetDeviceInfo(devices[d], CL_DEVICE_GLOBAL_MEM_SIZE, sizeof(global_mem), &global_mem, NULL);
                    printf_s("Global Memory: %.1f GB\n", global_mem / (1024.0 * 1024.0 * 1024.0));
                }
                free(devices);
            }
            free(platforms);
            return 0;
        }
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

    // Detect vendor for optimizations
    gpu_vendor_t vendor = detect_vendor(device);
    printf_s("Detected GPU vendor: %s\n", 
            vendor == VENDOR_NVIDIA ? "NVIDIA" :
            vendor == VENDOR_AMD ? "AMD" :
            vendor == VENDOR_INTEL ? "Intel" : "Unknown");

    // Get device info for batch sizing
    cl_uint compute_units;
    clGetDeviceInfo(device, CL_DEVICE_MAX_COMPUTE_UNITS, sizeof(compute_units), &compute_units, NULL);
    printf_s("Using device with %u compute units\n", compute_units);

    // Auto-detect optimal work group size if not specified
    if (numGroups == 0) {
        switch(vendor) {
            case VENDOR_AMD:
                numGroups = 64;  // AMD wavefront size
                break;
            case VENDOR_NVIDIA:
                numGroups = 32;  // NVIDIA warp size
                break;
            case VENDOR_INTEL:
                numGroups = 16;  // Conservative for Intel
                break;
            default:
                numGroups = 16;
                break;
        }
        printf_s("Auto-detected work group size: %zu\n", numGroups);
    }

    // Create context and queues
    cl_context ctx = clCreateContext(NULL, 1, &device, NULL, NULL, &err);
    if (err != CL_SUCCESS) {
        printf_s("Failed to create OpenCL context\n");
        free(devices);
        free(platforms);
        return 1;
    }

    // Create multiple queues for double buffering
    cl_command_queue compute_queue = clCreateCommandQueue(ctx, device, 0, &err);
    if (err != CL_SUCCESS) {
        printf_s("Failed to create compute queue\n");
        clReleaseContext(ctx);
        free(devices);
        free(platforms);
        return 1;
    }

    cl_command_queue transfer_queue = NULL;
    if (use_double_buffer) {
        transfer_queue = clCreateCommandQueue(ctx, device, 0, &err);
        if (err != CL_SUCCESS) {
            printf_s("Warning: Failed to create transfer queue, disabling double buffering\n");
            use_double_buffer = 0;
        }
    }

    // --- Load/Build Kernel ---
    char executable_dir[MAX_PATH];
    char kernel_path[MAX_PATH];
    char binary_path[MAX_PATH];
    char include_path[MAX_PATH + 6];
    
    getExecutableDir(executable_dir);
    snprintf(include_path, sizeof(include_path), "-I \"%s\"", executable_dir);
    createBinaryPath(executable_dir, filter, binary_path, MAX_PATH);

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
        printf_s("$Building kernel from source for filter: %s\n", filter);
        
        snprintf(kernel_path, sizeof(kernel_path), "%s%slib\\ouija_search.cl", executable_dir, PATH_SEPARATOR);
        if (fopen_s(&fp, kernel_path, "r") != 0 || !fp) {
            printf_s("Error: Cannot find kernel source at %s\n", kernel_path);
            clReleaseCommandQueue(compute_queue);
            if (transfer_queue) clReleaseCommandQueue(transfer_queue);
            clReleaseContext(ctx);
            free(devices);
            free(platforms);
            return 1;
        }

        char *kernel_code = malloc(MAX_CODE_SIZE);
        snprintf(kernel_code, MAX_CODE_SIZE, "#include \"ouija_filters/%s.cl\"\n\n", filter);
        
        size_t current_len = strlen(kernel_code);
        size_t bytes_read = fread(kernel_code + current_len, 1, MAX_CODE_SIZE - current_len - 1, fp);
        kernel_code[current_len + bytes_read] = '\0';
        fclose(fp);

        size_t kernel_size = strlen(kernel_code);
        ssKernelProgram = clCreateProgramWithSource(ctx, 1, (const char **)&kernel_code, &kernel_size, &err);
        free(kernel_code);
        
        if (err != CL_SUCCESS) {
            printf_s("Failed to create program from source\n");
            clReleaseCommandQueue(compute_queue);
            if (transfer_queue) clReleaseCommandQueue(transfer_queue);
            clReleaseContext(ctx);
            free(devices);
            free(platforms);
            return 1;
        }
    }

    // Build program with vendor-specific optimizations
    char build_options[512];
    snprintf(build_options, sizeof(build_options), "%s -cl-fast-relaxed-math", include_path);
    
    // Add vendor-specific options
    switch(vendor) {
        case VENDOR_NVIDIA:
            strcat(build_options, " -cl-nv-opt-level=3");
            break;
        case VENDOR_AMD:
            // AMD doesn't need special flags
            break;
        case VENDOR_INTEL:
            strcat(build_options, " -cl-intel-no-prera-scheduling");
            break;
    }

    err = clBuildProgram(ssKernelProgram, 1, &device, build_options, NULL, NULL);
    if (err != CL_SUCCESS) {
        size_t log_size;
        clGetProgramBuildInfo(ssKernelProgram, device, CL_PROGRAM_BUILD_LOG, 0, NULL, &log_size);
        char *log = malloc(log_size);
        clGetProgramBuildInfo(ssKernelProgram, device, CL_PROGRAM_BUILD_LOG, log_size, log, NULL);
        printf_s("Build failed:\n%s\n", log);
        free(log);
        clReleaseProgram(ssKernelProgram);
        clReleaseCommandQueue(compute_queue);
        if (transfer_queue) clReleaseCommandQueue(transfer_queue);
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
        clReleaseCommandQueue(compute_queue);
        if (transfer_queue) clReleaseCommandQueue(transfer_queue);
        clReleaseContext(ctx);
        free(devices);
        free(platforms);
        return 1;
    }

    // Check work group size
    size_t max_work_group_size;
    clGetKernelWorkGroupInfo(ssKernel, device, CL_KERNEL_WORK_GROUP_SIZE, 
                            sizeof(size_t), &max_work_group_size, NULL);
    if (numGroups > max_work_group_size) {
        numGroups = max_work_group_size;
        printf_s("Adjusted work group size to %zu\n", numGroups);
    }

    // --- Create Buffers ---
    // Calculate safe batch size
    cl_long base_batch_size = numGroups * compute_units;
    cl_long batch_capacity = base_batch_size * batchMultiplier;
    
    // Apply vendor-specific safety limits
    batch_capacity = calculate_safe_batch_size(device, vendor, batch_capacity);
    
    printf_s("Batch capacity: %" PRId64 " seeds per batch (~%.1f MB)\n", 
             batch_capacity, (batch_capacity * sizeof(OuijaHostResult)) / (1024.0 * 1024.0));

    // Config buffer (small, read-only)
    cl_mem configBuf = clCreateBuffer(ctx, CL_MEM_READ_ONLY, sizeof(OuijaConfig), NULL, &err);
    if (err != CL_SUCCESS) {
        printf_s("Failed to create config buffer\n");
        goto cleanup;
    }
    clEnqueueWriteBuffer(compute_queue, configBuf, CL_TRUE, 0, sizeof(OuijaConfig), &config, 0, NULL, NULL);

    // Create result buffers (double buffering if enabled)
    int num_buffers = use_double_buffer ? 2 : 1;
    cl_mem resultBuffers[2] = {NULL, NULL};
    OuijaHostResult* hostResults[2] = {NULL, NULL};
    
    for (int i = 0; i < num_buffers; i++) {
        resultBuffers[i] = clCreateBuffer(ctx, CL_MEM_WRITE_ONLY, 
                                         sizeof(OuijaHostResult) * batch_capacity, NULL, &err);
        if (err != CL_SUCCESS) {
            printf_s("Failed to create result buffer %d\n", i);
            goto cleanup;
        }
        
        // Allocate pinned host memory for faster transfers
        hostResults[i] = (OuijaHostResult*)malloc(sizeof(OuijaHostResult) * batch_capacity);
        if (!hostResults[i]) {
            printf_s("Failed to allocate host memory\n");
            goto cleanup;
        }
    }

    // Set static kernel arguments
    clSetKernelArg(ssKernel, 0, sizeof(cl_char8), &startingSeed);
    clSetKernelArg(ssKernel, 2, sizeof(cl_mem), &configBuf);

    // Print CSV header
    printf_s("+Seed,Score");
    if (config.scoreNaturalNegatives) printf_s(",Natural Negative Jokers");
    if (config.scoreDesiredNegatives) printf_s(",Desired Negative Jokers");
    
    for (int w = 0; w < config.numWants; w++) {
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

    clock_t start_time = clock();
    clock_t last_report = start_time;
    
    cl_long seeds_remaining = numSeeds;
    cl_long current_offset = 0;
    cl_long total_processed = 0;
    cl_long total_found = 0;
    
    int first_batch = 1;
    int current_buffer = 0;
    cl_event kernel_event = NULL, transfer_event = NULL;
    
    printf_s("\n    Starting search of %" PRId64 " seeds:\n\n", numSeeds);
    fflush(stdout);

    while (seeds_remaining > 0) {
        // Calculate batch size
        cl_long batch_size = (seeds_remaining > batch_capacity) ? batch_capacity : seeds_remaining;
        
        // Set kernel arguments for this batch
        clSetKernelArg(ssKernel, 1, sizeof(cl_long), &batch_size);
        clSetKernelArg(ssKernel, 3, sizeof(cl_mem), &resultBuffers[current_buffer]);
        clSetKernelArg(ssKernel, 4, sizeof(cl_long), &current_offset);
        
        // Calculate work sizes
        size_t global_work_size = ((batch_size + numGroups - 1) / numGroups) * numGroups;
        size_t local_work_size = numGroups;
        
        // Wait for previous transfer if double buffering
        if (use_double_buffer && transfer_event != NULL) {
            clWaitForEvents(1, &transfer_event);
            clReleaseEvent(transfer_event);
            transfer_event = NULL;
        }
        
        // Launch kernel
        err = clEnqueueNDRangeKernel(compute_queue, ssKernel, 1, NULL, 
                                    &global_work_size, &local_work_size, 
                                    0, NULL, &kernel_event);
        if (err != CL_SUCCESS) {
            printf_s("Kernel launch failed: %d\n", err);
            break;
        }
        
        // Process previous results while kernel runs (if double buffering)
        if (use_double_buffer && !first_batch) {
            int prev_buffer = 1 - current_buffer;
            int batch_high_score = cutoff;
            
            for (cl_long i = 0; i < batch_size; i++) {
                if (hostResults[prev_buffer][i].seed[0] == '\0') continue;
                
                if (hostResults[prev_buffer][i].TotalScore > batch_high_score) {
                    batch_high_score = hostResults[prev_buffer][i].TotalScore;
                }
                
                if (hostResults[prev_buffer][i].TotalScore >= cutoff) {
                    total_found++;
                    printf_s("|%s,%d", hostResults[prev_buffer][i].seed, 
                            hostResults[prev_buffer][i].TotalScore);
                    if (config.scoreNaturalNegatives) 
                        printf_s(",%d", hostResults[prev_buffer][i].NaturalNegativeJokers);
                    if (config.scoreDesiredNegatives) 
                        printf_s(",%d", hostResults[prev_buffer][i].DesiredNegativeJokers);
                    for (int w = 0; w < config.numWants; w++) {
                        printf_s(",%d", (int)hostResults[prev_buffer][i].ScoreWants[w]);
                    }
                    printf_s("\n");
                }
            }
            fflush(stdout);
            
            // Update cutoff in auto mode
            if (auto_cutoff_mode && batch_high_score > cutoff) {
                cutoff = batch_high_score;
            }
        }
        
        // Wait for kernel completion
        clWaitForEvents(1, &kernel_event);
        
        // Start async transfer for double buffering
        if (use_double_buffer) {
            err = clEnqueueReadBuffer(transfer_queue ? transfer_queue : compute_queue, 
                                     resultBuffers[current_buffer], CL_FALSE,
                                     0, sizeof(OuijaHostResult) * batch_size, 
                                     hostResults[current_buffer], 
                                     1, &kernel_event, &transfer_event);
        } else {
            // Synchronous read for single buffering
            err = clEnqueueReadBuffer(compute_queue, resultBuffers[current_buffer], CL_TRUE,
                                     0, sizeof(OuijaHostResult) * batch_size, 
                                     hostResults[current_buffer], 
                                     1, &kernel_event, NULL);
            
            // Process results immediately
            int batch_high_score = cutoff;
            for (cl_long i = 0; i < batch_size; i++) {
                if (hostResults[current_buffer][i].seed[0] == '\0') continue;
                
                if (hostResults[current_buffer][i].TotalScore > batch_high_score) {
                    batch_high_score = hostResults[current_buffer][i].TotalScore;
                }
                
                if (first_batch && auto_cutoff_mode && 
                    hostResults[current_buffer][i].TotalScore <= cutoff) {
                    continue;
                }

                if (hostResults[current_buffer][i].TotalScore >= cutoff) {
                    total_found++;
                    printf_s("|%s,%d", hostResults[current_buffer][i].seed, 
                            hostResults[current_buffer][i].TotalScore);
                    if (config.scoreNaturalNegatives) 
                        printf_s(",%d", hostResults[current_buffer][i].NaturalNegativeJokers);
                    if (config.scoreDesiredNegatives) 
                        printf_s(",%d", hostResults[current_buffer][i].DesiredNegativeJokers);
                    for (int w = 0; w < config.numWants; w++) {
                        printf_s(",%d", (int)hostResults[current_buffer][i].ScoreWants[w]);
                    }
                    printf_s("\n");
                }
            }
            fflush(stdout);
            
            // Update cutoff in auto mode
            if (auto_cutoff_mode && batch_high_score > cutoff) {
                cutoff = batch_high_score;
                if (first_batch) {
                    printf_s("[AUTO] First batch cutoff set to %d\n", cutoff);
                }
            }
        }
        
        clReleaseEvent(kernel_event);
        kernel_event = NULL;
        
        first_batch = 0;
        
        // Update counters
        total_processed += batch_size;
        current_offset += batch_size;
        seeds_remaining -= batch_size;
        
        // Switch buffers for double buffering
        if (use_double_buffer) {
            current_buffer = 1 - current_buffer;
        }
        
        // Progress report
        clock_t now = clock();
        if ((now - last_report) > 250) {
            double elapsed = (double)(now - start_time) / CLOCKS_PER_SEC;
            double rate = total_processed / elapsed;
            double eta_seconds = seeds_remaining / rate;
            
            // Calculate elapsed time components
            int elapsed_minutes = (int)(elapsed / 60);
            int elapsed_seconds_remainder = (int)elapsed % 60;
            
            // Calculate ETA components
            int eta_days = (int)(eta_seconds / (60 * 60 * 24));
            int eta_hours = (int)((eta_seconds - (eta_days * 60 * 60 * 24)) / 3600);
            int eta_minutes = (int)((eta_seconds - (eta_days * 60 * 60 * 24) - (eta_hours * 3600)) / 60);
            
            // Format elapsed time string
            char elapsed_string[64];
            if (elapsed_minutes > 0) {
                snprintf(elapsed_string, sizeof(elapsed_string), "in %d minutes and %d seconds", 
                         elapsed_minutes, elapsed_seconds_remainder);
            } else {
                snprintf(elapsed_string, sizeof(elapsed_string), "in %d seconds", 
                         elapsed_seconds_remainder);
            }
            
            // Format ETA string  
            char eta_string[128];
            if (eta_days >= 1) {
                snprintf(eta_string, sizeof(eta_string), "(ETA: %d days %d hours)", 
                         eta_days, eta_hours);
            } else if (eta_hours >= 1) {
                snprintf(eta_string, sizeof(eta_string), "(ETA: %d hours %d minutes)", 
                         eta_hours, eta_minutes);
            } else if (eta_minutes >= 1) {
                snprintf(eta_string, sizeof(eta_string), "(ETA: %d minutes %d seconds)",
                        eta_minutes, (int)eta_seconds % 60);
            } else {
                snprintf(eta_string, sizeof(eta_string), "(ETA: %d seconds)",
                        (int)eta_seconds);
            }
            
            // Calculate rarity percentage
            double rarity_percent = (total_processed > 0) ? (100.0 * total_found / total_processed) : 0.0;
            
            // Format searched count with appropriate units
            char searched_string[32];
            if (total_processed >= 1000000) {
                snprintf(searched_string, sizeof(searched_string), "%.1fM", total_processed / 1000000.0);
            } else if (total_processed >= 1000) {
                snprintf(searched_string, sizeof(searched_string), "%.1fK", total_processed / 1000.0);
            } else {
                snprintf(searched_string, sizeof(searched_string), "%" PRId64, total_processed);
            }
            
            // Enhanced progress with vendor info
            printf_s("$Found %" PRId64 " valid seeds of %s searched so far. (%.8f%% Rarity!) %s. %s :clock: %.1fK/s [%s]\n",
                     total_found, searched_string, rarity_percent, elapsed_string, eta_string, rate / 1000.0,
                     vendor == VENDOR_NVIDIA ? "NVIDIA" :
                     vendor == VENDOR_AMD ? "AMD" :
                     vendor == VENDOR_INTEL ? "Intel" : "Unknown");
                    
            fflush(stdout);
            last_report = now;
        }
    }
    
    // Process final buffer if double buffering
    if (use_double_buffer && transfer_event != NULL) {
        clWaitForEvents(1, &transfer_event);
        clReleaseEvent(transfer_event);
        
        // Process final results
        int final_buffer = 1 - current_buffer;
        for (cl_long i = 0; i < batch_capacity; i++) {
            if (hostResults[final_buffer][i].seed[0] == '\0') continue;
            
            if (hostResults[final_buffer][i].TotalScore >= cutoff) {
                total_found++;
                printf_s("|%s,%d", hostResults[final_buffer][i].seed, 
                        hostResults[final_buffer][i].TotalScore);
                if (config.scoreNaturalNegatives) 
                    printf_s(",%d", hostResults[final_buffer][i].NaturalNegativeJokers);
                if (config.scoreDesiredNegatives) 
                    printf_s(",%d", hostResults[final_buffer][i].DesiredNegativeJokers);
                for (int w = 0; w < config.numWants; w++) {
                    printf_s(",%d", (int)hostResults[final_buffer][i].ScoreWants[w]);
                }
                printf_s("\n");
            }
        }
        fflush(stdout);
    }
    
    // Final report
    double total_time = (double)(clock() - start_time) / CLOCKS_PER_SEC;
    printf_s("$Search Complete! Found %" PRId64 " viable out of %" PRId64 " total seeds @%.1f seeds/s\n",
             total_found, total_processed,
             (total_time > 0) ? (total_processed / total_time) : 0.0);
    fflush(stdout);

cleanup:
    // --- Cleanup ---
    for (int i = 0; i < num_buffers; i++) {
        if (resultBuffers[i]) clReleaseMemObject(resultBuffers[i]);
        if (hostResults[i]) free(hostResults[i]);
    }
    if (configBuf) clReleaseMemObject(configBuf);
    if (ssKernel) clReleaseKernel(ssKernel);
    if (ssKernelProgram) clReleaseProgram(ssKernelProgram);
    if (compute_queue) clReleaseCommandQueue(compute_queue);
    if (transfer_queue) clReleaseCommandQueue(transfer_queue);
    if (ctx) clReleaseContext(ctx);
    free(devices);
    free(platforms);
    
    return 0;
}