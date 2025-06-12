"""
Application Controller - Main coordinator for specialized controllers
"""

from controllers.build_controller import BuildController
from controllers.config_controller import ConfigController
from controllers.database_controller import DatabaseController
from controllers.funny_search_controller import FunSearchController
from controllers.search_controller import SearchController
from utils.result import Result


class ApplicationController:
    """Main controller that coordinates specialized controllers"""

    def __init__(self, config_model, search_model, database_model):
        """Initialize controller with models and specialized controllers"""
        # Initialize specialized controllers
        self.config_controller = ConfigController(config_model)
        self.database_controller = DatabaseController(database_model)
        self.search_controller = SearchController(search_model, self.config_controller, self.database_controller)
        self.fun_search_controller = FunSearchController(search_model, self.config_controller, self.database_controller)
        self.build_controller = BuildController()

        # Keep references to models for backward compatibility
        self.config_model = config_model
        self.search_model = search_model
        self.database_model = database_model
        self.current_view = None

        # Enhanced search completion callback to handle fun searches
        search_model.set_callbacks(
            results_callback=self.search_controller._on_search_results,
            console_callback=self.search_controller._on_console_output,
            process_finished_callback=self._on_search_completed,
        )

    def register_view(self, view):
        """Register the main view for all controllers"""
        self.current_view = view
        self.config_controller.register_view(view)
        self.search_controller.register_view(view)
        self.database_controller.register_view(view)
        self.fun_search_controller.register_view(view)
        self.build_controller.register_view(view)

    def _on_search_completed(self):
        """Enhanced search completion handler that supports fun searches"""
        if self.fun_search_controller.is_fun_search_active():
            # Handle fun search completion
            more_searches = self.fun_search_controller.handle_search_completed()
            if not more_searches:
                # Fun search fully complete
                return
        else:
            # Normal search completion
            self.search_controller._on_search_completed()

    # === Configuration Management (delegated to ConfigController) ===
    def load_config(self, file_path=None):
        """Load configuration from file"""
        result = self.config_controller.load_config(file_path)
        if result.success and self.current_view:
            # Connect to the database for this config
            self.database_controller.ensure_connection(file_path)
            self.database_controller.refresh_results()
        return result.success  # Maintain backward compatibility

    def save_config(self, file_path=None):
        """Save current configuration to file"""
        result = self.config_controller.save_config(file_path)
        return result.success  # Maintain backward compatibility

    def get_config_files(self):
        """Get list of available configuration files"""
        return self.config_controller.get_config_files()

    def get_config_name(self):
        """Get current configuration name"""
        return self.config_controller.get_config_name()

    def set_config_name(self, name):
        """Set configuration name"""
        self.config_controller.set_config_name(name)

    def get_config_description(self):
        """Get current configuration description"""
        return self.config_controller.get_config_description()

    def set_config_description(self, description):
        """Set configuration description"""
        self.config_controller.set_config_description(description)

    def get_config_author(self):
        """Get current configuration author"""
        return self.config_controller.get_config_author()

    def set_config_author(self, author):
        """Set configuration author"""
        self.config_controller.set_config_author(author)

    # === Criteria Management (delegated to ConfigController) ===
    def add_need(self, need_data):
        """Add a need to the configuration"""
        result = self.config_controller.add_need(need_data)
        return result.success

    def add_want(self, want_data):
        """Add a want to the configuration"""
        result = self.config_controller.add_want(want_data)
        return result.success

    def remove_criterion(self, index):
        """Remove a criterion (need or want) by index"""
        result = self.config_controller.remove_criterion(index)
        return result.success

    def clear_all_criteria(self):
        """Clear all needs and wants"""
        result = self.config_controller.clear_all_criteria()
        return result.success

    def get_criteria(self):
        """Retrieve the current criteria from the model"""
        return self.config_controller.get_criteria()

    # === Search Management (delegated to SearchController and FunSearchController) ===
    def run_search(self):
        """Start the search process"""
        if self.search_model.has_active_searches() or self.fun_search_controller.is_fun_search_active():
            # If a search is running, act as stop button
            return self.stop_search()

        result = self.search_controller.run_search()
        return result.success

    def stop_search(self):
        """Stop all active search processes"""
        # Stop both regular and fun searches
        search_result = self.search_controller.stop_search()
        fun_result = self.fun_search_controller.stop_fun_search()
        return search_result.success or fun_result.success

    def run_prank_seed_search(self):
        """Run a prank seed search (NSFW category)"""
        result = self.fun_search_controller.run_prank_seed_search()
        return result.success

    def run_fun_seed_search(self, category):
        """Run a fun seed search for a specific category"""
        result = self.fun_search_controller.run_fun_seed_search(category)
        return result.success

    # === Database Management (delegated to DatabaseController) ===
    def refresh_results(self):
        """Refresh results from the database"""
        result = self.database_controller.refresh_results()
        return result.success

    def delete_all_results(self):
        """Delete all results from the database"""
        result = self.database_controller.delete_all_results()
        return result.success

    def export_results(self, file_path, export_format="csv", limit=None):
        """Export results to file"""
        result = self.database_controller.export_results(file_path, export_format, limit)
        return result.success

    def get_export_info(self):
        """Get information about exportable data"""
        result = self.database_controller.get_export_info()
        return result.data if result.success else {"total_rows": 0, "columns": []}

    # === Build Management (delegated to BuildController) ===
    def is_kernel_build_needed(self):
        """Check if kernel binaries are missing or installation is incomplete"""
        return self.build_controller.is_kernel_build_needed()

    def run_kernel_build(self, on_complete=None):
        """Run kernel build operation"""
        result = self.build_controller.run_kernel_build(on_complete)
        return result.success

    # === Settings Management (delegated to ConfigController) ===
    def get_setting(self, key, default=None):
        """Get a user setting value"""
        return self.config_controller.get_setting(key, default)

    def set_setting(self, key, value):
        """Set a user setting value"""
        result = self.config_controller.set_setting(key, value)
        return result.success

    def get_current_config_path(self):
        """Return the currently loaded config path, or None if not set"""
        return self.config_controller.get_current_config_path()

    # === Negative Joker Scoring Flags (delegated to ConfigController) ===
    def get_score_natural_negatives(self):
        """Get score natural negatives setting"""
        return self.config_controller.get_score_natural_negatives()

    def set_score_natural_negatives(self, value):
        """Set score natural negatives setting"""
        result = self.config_controller.set_score_natural_negatives(value)
        return result.success

    def get_score_desired_negatives(self):
        """Get score desired negatives setting"""
        return self.config_controller.get_score_desired_negatives()

    def set_score_desired_negatives(self, value):
        """Set score desired negatives setting"""
        result = self.config_controller.set_score_desired_negatives(value)
        return result.success

    # === Cleanup ===
    def cleanup(self):
        """Clean up resources before application exit"""
        self.search_controller.cleanup()
        self.fun_search_controller.cleanup()
        self.database_controller.close()
        self.config_controller.config_model.save_user_conf()
        return True

    # === Backward Compatibility Methods ===
    def refresh_results_table(self, df):
        """Backward compatibility method for updating results table"""
        if df is None or df.empty:
            if self.current_view:
                self.current_view.write_to_console("⚠️ No data to display in the results table.\n", color="white")
            return
        if hasattr(self.current_view, 'results_table'):
            self.current_view.results_table.updateModel(df)
            self.current_view.results_table.redraw()
