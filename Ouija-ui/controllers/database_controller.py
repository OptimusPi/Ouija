"""
Database Controller - Handles database operations and results management
"""

import json
import os

from utils.result import Result


class DatabaseController:
    """Controller for database operations"""

    def __init__(self, database_model):
        self.database_model = database_model
        self.current_view = None

        # Set up callback for database table reset to refresh UI
        self.database_model.on_results_table_reset = self.refresh_results

    def register_view(self, view):
        """Register the main view for callbacks"""
        self.current_view = view

    def ensure_connection(self, config_path):
        """Ensure database connection is established
        
        Args:
            config_path (str): Path to configuration file
            
        Returns:
            Result: Success/failure with error details
        """
        try:
            db_path = self.database_model.get_db_path_from_config(config_path)
            if not os.path.exists(db_path):
                # Create database if it doesn't exist
                self.database_model.connect(config_path)
                self.database_model.close()

            # Always ensure the database is connected
            success = self.database_model.connect(config_path)
            return Result.success(db_path) if success else Result.error("Failed to connect to database")
        except Exception as e:
            return Result.error(f"Database connection error: {str(e)}")

    def refresh_results(self):
        """Refresh results from the database
        
        Returns:
            Result: Success/failure with data or error details
        """
        try:
            df = self.database_model.get_dataframe()
            if df is not None and not df.empty:
                if self.current_view:
                    self.current_view.update_results_table(df)
                return Result.success(df)
            else:
                if self.current_view:
                    self.current_view.write_to_console("⚠️ No results found in the database.\n")
                # If no results, return empty DataFrame
                if self.current_view:
                    self.current_view.update_results_table(None)
                return Result.success(None)
        except Exception as e:
            error_msg = f"Error refreshing results: {str(e)}"
            if self.current_view:
                self.current_view.write_to_console(f"⚠️ {error_msg}\n")
            return Result.error(error_msg)

    def delete_all_results(self):
        """Delete all results from the database
        
        Returns:
            Result: Success/failure with error details
        """
        try:
            # Get the current config path to determine which database to clear
            with open("user.ouija.conf", "r") as f:
                user_conf = json.load(f)
            config_path = user_conf.get("last_config_path")

            if config_path and self.database_model.connect(config_path):
                success = self.database_model.delete_all_results()
                if success:
                    # Refresh the view to show empty table
                    refresh_result = self.refresh_results()
                    return Result.success("All results deleted")
                else:
                    return Result.error("Failed to delete results from database")
            else:
                return Result.error("No config path found or database connection failed")
        except Exception as e:
            return Result.error(f"Error deleting all results: {str(e)}")

    def export_results(self, file_path, export_format="csv", limit=None):
        """Export results to file
        
        Args:
            file_path (str): Path where file will be saved
            export_format (str): Format to export ("csv", "excel", "json")
            limit (int, optional): Maximum number of rows to export (None for all)
            
        Returns:
            Result: Success/failure with error details
        """
        try:
            # Ensure database is connected
            config_path = getattr(self.database_model, "loaded_config_path", None)
            if not config_path:
                return Result.error("No configuration loaded")

            if not self.database_model.connect(config_path):
                return Result.error("Failed to connect to database")

            # Export based on format
            if export_format.lower() == "csv":
                success = self.database_model.export_to_csv(file_path, limit)
            elif export_format.lower() == "excel":
                success = self.database_model.export_to_excel(file_path, limit)
            elif export_format.lower() == "json":
                success = self.database_model.export_to_json(file_path, limit)
            else:
                return Result.error(f"Unsupported export format: {export_format}")

            if success:
                return Result.success(f"Results exported to {file_path}")
            else:
                return Result.error("Export operation failed")

        except Exception as e:
            return Result.error(f"Error exporting results: {str(e)}")

    def get_export_info(self):
        """Get information about exportable data
        
        Returns:
            Result: Export statistics and info
        """
        try:
            config_path = getattr(self.database_model, "loaded_config_path", None)
            if config_path and self.database_model.connect(config_path):
                stats = self.database_model.get_export_stats()
                return Result.success(stats)
            else:
                return Result.success({"total_rows": 0, "columns": []})
        except Exception as e:
            return Result.error(f"Error getting export info: {str(e)}")

    def close(self):
        """Close database connections"""
        try:
            self.database_model.close()
            return Result.success("Database connection closed")
        except Exception as e:
            return Result.error(f"Error closing database: {str(e)}")
