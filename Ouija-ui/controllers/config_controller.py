"""
Configuration Controller - Handles configuration management operations
"""

from utils.result import Result


class ConfigController:
    """Controller for configuration management"""

    def __init__(self, config_model):
        self.config_model = config_model
        self.current_view = None

    def register_view(self, view):
        """Register the main view for callbacks"""
        self.current_view = view

    def load_config(self, file_path=None):
        """Load configuration from file
        
        Args:
            file_path (str): Path to configuration file
            
        Returns:
            Result: Success/failure with error details
        """
        if file_path is None:
            return Result.error("No file path provided")

        success = self.config_model.load_config_from_path(file_path)
        if success:
            if self.current_view:
                self.current_view.update_config_display()
            return Result.success(file_path)
        else:
            return Result.error("Failed to load configuration")

    def save_config(self, file_path=None):
        """Save current configuration to file
        
        Args:
            file_path (str, optional): Path to save configuration
            
        Returns:
            Result: Success/failure with error details
        """
        if not self.config_model.config_name:
            return Result.error("Please enter a configuration name before saving")

        success, result = self.config_model.save_config(file_path)
        if success:
            if self.current_view:
                self.current_view.set_status(f"Configuration saved: {result}")
            return Result.success(result)
        else:
            return Result.error(f"Failed to save configuration: {result}")

    def get_config_files(self):
        """Get list of available configuration files
        
        Returns:
            list: Available configuration files
        """
        return self.config_model.get_config_files()

    def get_config_name(self):
        """Get current configuration name"""
        return self.config_model.config_name

    def set_config_name(self, name):
        """Set configuration name"""
        self.config_model.config_name = name
        self.config_model.config_modified = True
        return Result.success(name)

    def get_config_description(self):
        """Get current configuration description"""
        return self.config_model.config_description

    def set_config_description(self, description):
        """Set configuration description"""
        self.config_model.config_description = description
        self.config_model.config_modified = True
        return Result.success(description)

    def get_config_author(self):
        """Get current configuration author"""
        return self.config_model.config_author

    def set_config_author(self, author):
        """Set configuration author"""
        self.config_model.config_author = author
        self.config_model.config_modified = True
        return Result.success(author)

    # Criteria management
    def add_need(self, need_data):
        """Add a need to the configuration
        
        Args:
            need_data: Need configuration data
            
        Returns:
            Result: Success/failure with error details
        """
        success = self.config_model.add_need(need_data)
        if success:
            if self.current_view:
                self.current_view.update_criteria_display()
            return Result.success(need_data)
        else:
            return Result.error("Failed to add need")

    def add_want(self, want_data):
        """Add a want to the configuration
        
        Args:
            want_data: Want configuration data
            
        Returns:
            Result: Success/failure with error details
        """
        success = self.config_model.add_want(want_data)
        if success:
            if self.current_view:
                self.current_view.update_criteria_display()
            return Result.success(want_data)
        else:
            return Result.error("Failed to add want")

    def remove_criterion(self, index):
        """Remove a criterion (need or want) by index
        
        Args:
            index (int): Index of criterion to remove
            
        Returns:
            Result: Success/failure with error details
        """
        needs_count = len(self.config_model.needs_list)
        if index < needs_count:
            success = self.config_model.remove_need(index)
        else:
            success = self.config_model.remove_want(index - needs_count)

        if success:
            if self.current_view:
                self.current_view.update_criteria_display()
            return Result.success(index)
        else:
            return Result.error(f"Failed to remove criterion at index {index}")

    def clear_all_criteria(self):
        """Clear all needs and wants
        
        Returns:
            Result: Success result
        """
        self.config_model.clear_all_criteria()
        if self.current_view:
            self.current_view.update_criteria_display()
        return Result.success("All criteria cleared")

    def get_criteria(self):
        """Retrieve the current criteria from the model
        
        Returns:
            dict: Current criteria configuration
        """
        return self.config_model.get_criteria()

    # Settings management
    def get_setting(self, key, default=None):
        """Get a configuration setting value
        
        Args:
            key (str): Setting key
            default: Default value if setting not found
            
        Returns:
            Any: Setting value or default
        """
        settings_map = {
            "thread_groups": "thread_groups",
            "starting_seed": "starting_seed",
            "number_of_seeds": "number_of_seeds",
            "deck": "deck",
            "stake": "stake",
            "cutoff": "cutoff",
            "gpu_batch": "gpu_batch",
            "template": "template",
            "score_natural_negatives": "score_natural_negatives",
            "score_desired_negatives": "score_desired_negatives"
        }

        if key in settings_map:
            return getattr(self.config_model, settings_map[key], default)
        return default

    def set_setting(self, key, value):
        """Set a configuration setting value
        
        Args:
            key (str): Setting key
            value: Setting value
            
        Returns:
            Result: Success/failure with error details
        """
        settings_map = {
            "thread_groups": "thread_groups",
            "starting_seed": "starting_seed",
            "number_of_seeds": "number_of_seeds",
            "deck": "deck",
            "stake": "stake",
            "cutoff": "cutoff",
            "gpu_batch": "gpu_batch",
            "template": "template",
            "score_natural_negatives": "score_natural_negatives",
            "score_desired_negatives": "score_desired_negatives"
        }

        if key in settings_map:
            setattr(self.config_model, settings_map[key], value)
            self.config_model.config_modified = True
            self.config_model.save_user_conf()
            return Result.success(value)
        return Result.error(f"Unknown setting key: {key}")

    def get_current_config_path(self):
        """Return the currently loaded config path, or None if not set"""
        return getattr(self.config_model, "loaded_config_path", None)

    # Negative joker scoring flags
    def get_score_natural_negatives(self):
        """Get score natural negatives setting"""
        return self.config_model.score_natural_negatives

    def set_score_natural_negatives(self, value):
        """Set score natural negatives setting"""
        self.config_model.score_natural_negatives = value
        self.config_model.config_modified = True
        return Result.success(value)

    def get_score_desired_negatives(self):
        """Get score desired negatives setting"""
        return self.config_model.score_desired_negatives

    def set_score_desired_negatives(self, value):
        """Set score desired negatives setting"""
        self.config_model.score_desired_negatives = value
        self.config_model.config_modified = True
        return Result.success(value)
