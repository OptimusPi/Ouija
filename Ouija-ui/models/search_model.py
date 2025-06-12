"""
Search Model - Handles search process logic for Ouija seed finder
"""

import os
import signal
import subprocess
import threading
import time        
import sys


class SearchModel:
    """Model for handling seed search operations"""

    # Maps for dropdown values to command-line arguments
    THREAD_GROUP_MAP = {
        "Single": "1",  # Added to handle "Single" from UI
        "1": "1",
        "16": "16",  # Added 16 as a valid option, assuming it's supported
        "32": "32", "64": "64",
        "128": "128",
        "256": "256",
    }

    SEED_COUNT_MAP = {
        "All": None,  # No -n parameter (search all seeds)
        "All Seeds": None,  # Handle default config value (search all seeds)
        "1 Single Seed": "1",  # Match the UI dropdown value
        "1K": "1000",
        "100K": "100000",
        "1M": "1000000",
        "100M": "100000000",        
        "1B": "1000000000",
        "10B": "10000000000",
        "100B": "100000000000",    }

    def __init__(self):
        """Initialize the search model"""
        self.active_processes = []
        self.results_callback = None
        self.console_callback = None
        self.process_finished_callback = None
        self.cutoff = None  # Add cutoff
        self.gpu_batch = None  # Add gpu_batch

    def set_callbacks(
            self,
            results_callback=None,
            console_callback=None,
            process_finished_callback=None,
    ):
        """Set callbacks for handling search results and output"""
        self.results_callback = results_callback
        self.console_callback = console_callback
        self.process_finished_callback = process_finished_callback

    def start_search(
        self,
        config_name_for_cli,
        starting_seed,
        thread_groups,
        number_of_seeds,
        db_model,
        cutoff,
        gpu_batch,
        template
    ):
        """Start a new search process"""
        try:
            # Build the command using consolidated logic
            command_parts = [self._get_cli_path()]

            # Add template filter
            if template:
                command_parts.extend(["-f", template])

            # Add starting seed
            if starting_seed.lower() == "random":
                command_parts.extend(["-s", "random"])
            else:
                command_parts.extend(["-s", starting_seed.upper()])

            # Add thread groups
            thread_groups_value = self.THREAD_GROUP_MAP.get(str(thread_groups), "32")
            command_parts.extend(["-g", thread_groups_value])

            # Add number of seeds
            if number_of_seeds.lower() in ["all", "all seeds"]:
                pass  # Don't add -n for "All Seeds"
            else:
                n_value = self.SEED_COUNT_MAP.get(number_of_seeds, number_of_seeds)
                command_parts.extend(["-n", str(n_value)])

            # Add config name
            command_parts.extend(["--config", config_name_for_cli])

            # Add cutoff score
            if cutoff:
                command_parts.extend(["-c", str(cutoff)])

            # Add GPU batch size
            if gpu_batch:
                command_parts.extend(["-b", str(gpu_batch)])

            # Log and execute the command
            command = " ".join(command_parts)
            if self.console_callback:
                self.console_callback(f"COMMAND: {command}\n")
                self.console_callback(f"WORKING DIR: {os.getcwd()}\n")

            process = subprocess.Popen(
                command_parts,
                shell=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=os.getcwd()
            )
            self.active_processes.append(process)
            threading.Thread(
                target=self._read_process_output, args=(process, db_model), daemon=True
            ).start()
            return True
        except Exception as e:
            if self.console_callback:
                self.console_callback(f"Error starting search: {str(e)}\n")
            return False

    def _get_cli_path(self):
        """Retrieve the path to the Ouija-CLI executable"""
        cli_path = os.path.join(os.getcwd(), "Ouija-CLI.exe")
        if not os.path.exists(cli_path):
            raise FileNotFoundError(f"Ouija-CLI executable not found at {cli_path}")
        return cli_path

    def _read_process_output(self, process, db_model):
        """Read and process output from the search command"""
        header_columns = None
        header_found = False
        db_table_created = False
        last_db_ping_time = time.time()
        db_ping_interval = (
            1.0  # Notify controller every 1 second that new data might be in DB
        )        # If we already have results in the database, we don't need to load them here.
        # The controller will handle refreshing from DB.
        if db_model and db_model.conn and db_model.table_exists():
            db_table_created = True  # Assume table structure is known if DB exists
            # Try to get headers if table exists, to avoid issues if Ouija-CLI.exe doesn't print them
            try:
                existing_df = db_model.query_results(
                    limit=1
                )
                if existing_df is not None and not existing_df.empty:
                    existing_headers = existing_df.columns.tolist()
                    # Don't automatically use existing headers - wait for CLI to send new ones
                    # This prevents mismatch issues when the CLI config changes
                    if self.console_callback:
                        self.console_callback(f"Existing DB table has columns: {existing_headers}\n")
            except Exception as e:
                if self.console_callback:
                    self.console_callback(
                        f"Error getting headers from existing DB: {str(e)}\n"
                    )
        try:
            while True:
                # Check if process has terminated
                if process.poll() is not None:
                    break
                line = process.stdout.readline()

                  # Parse CSV header
                if not header_found and line.strip().startswith("+Seed,"):
                    # Validate headers to ensure they are distinct and valid
                    header_columns = [
                        col.strip()
                        for col in line.replace("+Seed", "Seed")
                        .strip()
                        .replace("!", "")
                        .split(",")
                        if col.strip() != ""
                    ]

                    # Relax header validation to allow duplicates but log a warning
                    if len(header_columns) != len(set(header_columns)):
                        if self.console_callback:
                            self.console_callback(
                                f"Warning: Duplicate headers found: {header_columns}\n"
                            )  # Validate header names but only warn about truly problematic ones

                    header_found = True

                    # Create table in database
                    if db_model and db_model.conn and not db_table_created:
                        db_model.create_table(header_columns)
                        db_table_created = True

                    continue                # Process result lines (those starting with '|')
                if line.startswith("|"):
                    if not header_columns:  # Wait for header
                        if self.console_callback:
                            self.console_callback(
                                f"Skipping result line, header not yet found: {line.strip()}\n"
                            )
                        continue

                    try:
                        # Process the CSV line directly using DuckDB's CSV parser
                        result = db_model.process_csv_line(line, header_columns)

                        if not result:
                            continue

                        # Unpack the result
                        parsed_headers, parsed_values = result

                        # If we didn't have headers before, use the ones from parsing (should not happen if logic above is correct)
                        if not header_columns:
                            header_columns = parsed_headers
                            if db_model and db_model.conn and not db_table_created:
                                db_model.create_table(header_columns)
                                db_table_created = True

                        # Store in database using upsert
                        if db_model and db_model.conn and db_table_created:
                            db_model.insert_result(header_columns, parsed_values)

                        # Periodically notify controller to refresh from DB
                        current_time = time.time()                        
                        if (current_time - last_db_ping_time) >= db_ping_interval:
                            if (
                                    self.results_callback
                            ):  # This callback now signals to refresh from DB
                                self.results_callback(
                                    None, None
                                )  # Pass None, None as data is in DB
                                last_db_ping_time = current_time
                    except Exception as e:
                        import traceback
                        if self.console_callback:
                            tb_str = traceback.format_exc()
                            self.console_callback(
                                f"Error processing CSV line for DB insertion: {str(e)}\nLine: {line.strip()}\nHeaders: {header_columns}\nTraceback:\n{tb_str}\n"
                            )
                # Handle status bar messages (lines starting with "$")
                elif line.startswith("$") and line.strip() != "$":
                    # Pass status messages to the application controller via console callback
                    # with a special prefix that the controller will recognize
                    if self.console_callback:
                        status_message = line.strip()[1:].strip()
                        self.console_callback(f"STATUS:{status_message}\n")

                else:
                    # Display unprocessed CLI lines (mark as CLI messages, not UI messages)
                    self.console_callback(f"CLI:{line.rstrip()}\n", color="blue")

            # Make sure to send one final notification to controller after process ends
            if self.results_callback:
                self.results_callback(None, None)

            # Process stderr after stdout is done
            for line in process.stderr:
                if self.console_callback:
                    self.console_callback(f"ERROR: {line}")

            # Remove process from active list
            if process in self.active_processes:
                self.active_processes.remove(process)            # Call process finished callback
            if self.process_finished_callback:
                self.process_finished_callback()

        except Exception as e:
            import traceback
            if self.console_callback:
                tb_str = traceback.format_exc()
                self.console_callback(f"ERROR_MODEL: Error processing output: {str(e)}\nTraceback:\n{tb_str}\n")

            # Call process finished callback on error
            if self.process_finished_callback:
                self.process_finished_callback()

    def stop_all_searches(self):
        """Stop all active search processes"""
        # First try to stop the processes we're tracking
        for process in self.active_processes:
            try:
                if process.poll() is None:  # If process is still running
                    if os.name == "nt":  # Windows
                        subprocess.call(
                            ["taskkill", "/F", "/T", "/PID", str(process.pid)]
                        )
                    else:  # Unix/Linux/Mac
                        os.kill(process.pid, signal.SIGKILL)
            except Exception as e:
                print(f"Error stopping process: {e}")        # Also look for any Ouija-CLI.exe processes that might have been left behind
        try:
            if os.name == "nt":  # Windows
                # Kill any remaining Ouija-CLI.exe processes
                subprocess.call(
                    ["taskkill", "/F", "/IM", "Ouija-CLI.exe"], stderr=subprocess.DEVNULL
                )
            else:  # Unix/Linux/Mac
                # Find and kill any Ouija processes
                subprocess.call(["pkill", "-f", "Ouija-CLI.exe"], stderr=subprocess.DEVNULL)
        except Exception as e:
            print(f"Error cleaning up Ouija-CLI processes: {e}")

        # Clear the list
        self.active_processes.clear()

        # Call process finished callback
        if self.process_finished_callback:
            self.process_finished_callback()

        return True

    def has_active_searches(self):
        """Check if there are any active search processes"""
        # Remove any completed processes
        self.active_processes = [p for p in self.active_processes if p.poll() is None]
        return len(self.active_processes) > 0

    def _handle_output_line(self, line: str, db_model):
        """Handle a line of stdout output from the CLI process"""
        if not line.strip():
            return
            
        # Pass through to the existing output processing logic
        if self.console_callback:
            self.console_callback(f"{line}\n")
            
        # Handle CSV results and status messages
        if line.startswith("+"):
            # This is a CSV result line - use the existing DB insertion logic
            self._process_csv_line(line, db_model)
        elif line.startswith("$"):
            # This is a status message
            self._process_status_line(line)
            
    def _handle_error_line(self, line: str):
        """Handle a line of stderr output from the CLI process"""
        if self.console_callback:
            self.console_callback(f"ERROR: {line}\n")
            
    def _process_csv_line(self, line: str, db_model):
        """Process a CSV result line and insert into database"""
        try:
            if db_model and db_model.conn:
                # Use existing CSV processing logic
                parts = line.strip().split(',')
                if len(parts) >= 2:  # At least seed and score
                    db_model.insert_result_from_csv_parts(parts)
        except Exception as e:
            if self.console_callback:
                self.console_callback(f"Error processing CSV line: {e}\n")
                
    def _process_status_line(self, line: str):
        """Process a status line from the CLI"""
        if self.console_callback:
            # Remove the "$" prefix and format the status message
            status_message = line.strip()[1:].strip()
            if "$clock$" in status_message:
                parts = status_message.split("$clock$")
                status_message = f"{parts[0].strip()} ⏱️{parts[1].strip()}"
            self.console_callback(f"STATUS:{status_message}\n")
    
    def _parse_seed_count_shorthand(self, s_val):
        """Parse shorthand seed count values (e.g., '1K', '100K', '1M') to integer strings"""
        try:
            if isinstance(s_val, str):
                s_val = s_val.strip().upper()
                if s_val.endswith("K"):
                    return str(int(float(s_val[:-1]) * 1000))
                elif s_val.endswith("M"):
                    return str(int(float(s_val[:-1]) * 1000000))
                elif s_val.endswith("B"):
                    return str(int(float(s_val[:-1]) * 1000000000))
                else:
                    return str(int(s_val))  # Fallback to direct conversion
        except Exception as e:
            if self.console_callback:
                self.console_callback(f"Error parsing seed count shorthand '{s_val}': {e}\n")
        return None  # Indicate parsing failure
