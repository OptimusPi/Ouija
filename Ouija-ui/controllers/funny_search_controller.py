"""
Fun Search Controller - Handles specialized fun/prank seed searches
"""

from utils.result import Result


class FunSearchController:
    """Controller for fun and prank seed searches"""

    def __init__(self, search_model, config_controller, database_controller):
        self.search_model = search_model
        self.config_controller = config_controller
        self.database_controller = database_controller
        self.current_view = None        # Fun search state
        self.fun_search_active = False
        self.fun_search_category = None
        self.fun_search_words = []
        self.fun_search_current_word_index = 0
        self.auto_refresh_timer_id = None
        self.auto_refresh_interval_ms = 2000
        self.completion_message_shown = False  # Flag to prevent duplicate "Search Complete" messages

    def register_view(self, view):
        """Register the main view for callbacks"""
        self.current_view = view

    def run_fun_seed_search(self, category):
        """Run a fun seed search for a specific category
        
        Args:
            category (str): Category of fun seeds to search for ("LOL", "GROSS", "NSFW", "COOL")
            
        Returns:
            Result: Success/failure with error details
        """
        try:
            fun_words = {
                "LOL": ["LMAO", "ROFL", "HAHA", "JOKE", "MEME", "EPIC", "FAIL", "DERP", "NOOB", "YOLO", "SWAG", "REKT",
                        "TROLL", "PLEB", "KEKS", "LULZ"],
                "GROSS": ["FART", "BUTT", "BURP", "SNOT", "POOP", "SLIME", "YUCK", "EWWW", "SICK", "VOMIT", "GUNK",
                          "CRUD", "MOLD", "GRIME", "BILE", "DROOL", "SCUM"],
                "NSFW": ["SEXY", "BOOB", "ASSS", "PENIS", "PUSSY", "COCK", "PUSSY", "SQUIRT", "WET", "THROB", "CUMMY",
                         "CUM", "CUM", "CLIT", "SHIT", "HELL", "SUCK", "BEER", "WINE", "FUCK", "BLOW", "DRUG", "WEED",
                         "HIGH", "DOPE", "ACID", "CUNT"],
                "COOL": ["PILUV", "FIRE", "DOPE", "SICK", "EPIC", "RAGE", "WILD", "YEAH", "BOSS", "HERO", "STAR",
                         "GOLD", "RICH", "DAMN", "MEGA", "HUGE", "ROCK", "KING"]
            }

            if category not in fun_words:
                return Result.error(f"Unknown fun search category: {category}")

            if self.search_model.has_active_searches() or self.fun_search_active:
                return Result.error("A search is already running. Please stop it first.")
            
            # Generate all valid seeds for each word with padding
            fun_seeds = self._generate_fun_seeds(fun_words[category])

            # Reset completion state for new search
            self.fun_search_category = category
            self.fun_search_words = fun_seeds
            self.fun_search_current_word_index = 0
            self.fun_search_active = True
            self.completion_message_shown = False

            if self.current_view:
                self.current_view.write_to_console(f"🎭 Starting {category} fun seed search!\n", color="white")
                self.current_view.set_search_running(True)

            result = self._run_next_fun_seed_search()
            return Result.success(f"{category} fun search started") if result else Result.error(
                "Failed to start fun search")

        except Exception as e:
            return Result.error(f"Failed to start fun search: {str(e)}")

    def _generate_fun_seeds(self, words):
        """Generate fun seeds with padding
        
        Args:
            words (list): List of base words
            
        Returns:
            list: List of (seed, right_pad_count) tuples
        """
        fun_seeds = []
        for word in words:
            max_pad = 8 - len(word)
            if max_pad < 1:
                continue  # skip words too long

            # For each possible total padding (from 1 to max_pad), always require at least 1 right pad
            for total_pad in range(1, max_pad + 1):
                for left in range(0, total_pad):
                    right = total_pad - left
                    if right < 1:
                        continue  # must have at least one right pad
                    seed = ("1" * left) + word + ("1" * right)
                    if len(seed) <= 8:
                        fun_seeds.append((seed, right))

        # Remove duplicates
        return list(dict.fromkeys(fun_seeds))

    def _run_next_fun_seed_search(self):
        """Run the next fun seed search in the sequence
        
        Returns:
            bool: True if search started successfully
        """
        try:
            if self.fun_search_current_word_index >= len(self.fun_search_words):
                return False

            search_term, right_pad_count = self.fun_search_words[self.fun_search_current_word_index]

            # Set n_value based on right_pad_count
            n_value = 35 ** right_pad_count if right_pad_count > 0 else 35

            if self.current_view:
                self.current_view.write_to_console(f"    🔍 Searching: {search_term} (n={n_value})\n", color="blue")            
                # Get config name instead of path (CLI now uses config name only)
            config_name = self.config_controller.config_model.config_name
            if not config_name:
                # Try to get it from the loaded path if config_name is empty
                loaded_path = self.config_controller.config_model.loaded_config_path
                if loaded_path:
                    import os
                    config_name = os.path.basename(loaded_path).replace(".ouija.json", "")
            
            if not config_name:
                return False

            # Connect to database using full path (for database file naming)
            db_config_path = self.config_controller.config_model.get_absolute_config_path()
            if not db_config_path:
                import os
                db_config_path = os.path.join(self.config_controller.config_model.CONFIG_DIR, f"{config_name}.ouija.json")
                self.database_controller.database_model.connect(db_config_path)
            success = self.search_model.start_search(
                config_name_for_cli=config_name,
                starting_seed=search_term,
                thread_groups=self.config_controller.get_setting("thread_groups"),
                number_of_seeds=str(n_value),  # Convert integer to string
                db_model=self.database_controller.database_model,
                cutoff=self.config_controller.get_setting("cutoff"),
                gpu_batch=self.config_controller.get_setting("gpu_batch"),
                template=self.config_controller.get_setting("template"),
            )
            return success
        except Exception as e:
            if self.current_view:
                self.current_view.write_to_console(f"❌ Error in fun search: {e}\n", color="red")
            return False

    def handle_search_completed(self):
        """Handle completion of a fun search iteration
        
        Returns:
            bool: True if more searches to run, False if complete
        """
        try:
            if not self.fun_search_active:
                return False

            # Log completion of current word
            if hasattr(self, 'fun_search_category') and self.fun_search_category:
                if self.fun_search_current_word_index < len(self.fun_search_words):
                    word = self.fun_search_words[self.fun_search_current_word_index][0]  # Get seed from tuple
                    if self.current_view and word:
                        self.current_view.write_to_console(f"✅ Completed: {word}\n", color="green")
                        # Refresh results table through database controller
                        self.database_controller.refresh_results()

            # Advance to next search
            self.fun_search_current_word_index += 1

            # Check if we're done with all combinations
            if self.fun_search_current_word_index >= len(self.fun_search_words):
                # Fun search fully complete
                self.fun_search_active = False
                category = self.fun_search_category
                self.fun_search_category = None
                self._stop_auto_refresh()

                if self.current_view:
                    try:
                        self.current_view.write_to_console(f"🎉 All {category} searches complete! Check your results! 🎉\n", color="green")
                        self.current_view.set_search_running(False)
                    except Exception:
                        # UI might be destroyed during cleanup, ignore errors
                        pass

                self.database_controller.refresh_results()
                return False
            else:
                # More combinations to search - continue
                return self._run_next_fun_seed_search()

        except Exception as e:
            if self.current_view:
                try:
                    self.current_view.write_to_console(f"⚠️ Error in fun search completion: {e}\n", color="red")
                except Exception:
                    # UI might be destroyed, ignore errors
                    pass
            print(f"Error in handle_search_completed: {e}")

            # Reset fun search state to prevent further issues
            self.fun_search_active = False
            self.fun_search_category = None
            if self.current_view:
                try:
                    self.current_view.set_search_running(False)
                except Exception:
                    # UI might be destroyed during cleanup, ignore errors
                    pass
            return False

    def stop_fun_search(self):
        """Stop any active fun search
        
        Returns:
            Result: Success result
        """
        # Just brutally kill the CLI processes - screw the fancy UI updates during cleanup!
        self.search_model.stop_all_searches()
        
        # Reset fun search state
        self.fun_search_active = False
        self.fun_search_category = None
        self.fun_search_words = []
        self.fun_search_current_word_index = 0
        self._stop_auto_refresh()

        return Result.success("Fun search stopped")

    def is_fun_search_active(self):
        """Check if a fun search is currently active
        
        Returns:
            bool: True if fun search is active
        """
        return self.fun_search_active

    def _stop_auto_refresh(self):
        """Stop the auto-refresh timer"""
        if self.auto_refresh_timer_id and self.current_view:
            try:
                self.current_view.root.after_cancel(self.auto_refresh_timer_id)
            except:
                pass  # Don't care if UI is dead
            self.auto_refresh_timer_id = None

    def cleanup(self):
        """Clean up fun search resources - just kill everything!"""
        # Brutally stop all searches without UI updates
        try:
            self.search_model.stop_all_searches()
        except:
            pass  # Don't care about errors during shutdown
            
        # Reset state
        self.fun_search_active = False
        self.fun_search_category = None
        self.fun_search_words = []
        self.fun_search_current_word_index = 0
        
        # Kill timers
        if self.auto_refresh_timer_id:
            try:
                if self.current_view and hasattr(self.current_view, 'root'):
                    self.current_view.root.after_cancel(self.auto_refresh_timer_id)
            except:
                pass  # UI is probably dead anyway
            self.auto_refresh_timer_id = None
