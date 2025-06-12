"""
Config Model - Handles configuration data for Ouija seed finder
"""

import json
import os


class ConfigModel:
    """Model for handling configuration data and files"""

    USER_CONF_PATH = "user.ouija.conf"
    CONFIG_DIR = "ouija_configs"
    EXPORT_DIR = "ouija_csv_exports"

    def __init__(self):
        """Initialize config model with default values"""
        self.needs_list = []
        self.wants_list = []
        self.config_name = ""
        self.config_description = ""
        self.config_author = ""
        self.deck = "Red Deck"
        self.stake = "Black Stake"
        self.config_loaded_from_file = False
        self.config_modified = False
        self.loaded_config_path = None
        self.thread_groups = "32"
        self.starting_seed = "random"
        self.number_of_seeds = "All Seeds"
        self.cutoff = "1"
        self.gpu_batch = "16"  # Default GPU batch size
        self.template = "ouija_template"  # Default template filter
        # --- Negative joker scoring flags ---
        self.score_natural_negatives = False
        self.score_desired_negatives = False

        # Create config directory if it doesn't exist
        os.makedirs(self.CONFIG_DIR, exist_ok=True)

        # Load user preferences if they exist
        self.load_user_conf()

    def load_user_conf(self):
        """Load user configuration from file"""
        if os.path.exists(self.USER_CONF_PATH):
            try:
                with open(self.USER_CONF_PATH, "r") as f:
                    conf = json.load(f)

                # Update model properties from loaded config
                if conf.get("gpu_thread_groups"):
                    self.thread_groups = conf["gpu_thread_groups"]
                if conf.get("last_seed"):
                    self.starting_seed = conf["last_seed"]
                if conf.get("last_deck"):
                    self.deck = conf["last_deck"]
                if conf.get("last_stake"):
                    self.stake = conf["last_stake"]
                if conf.get("last_number_of_seeds"):
                    self.number_of_seeds = conf["last_number_of_seeds"]
                if conf.get("cutoff"):  # Load cutoff
                    self.cutoff = conf["cutoff"]
                if conf.get("gpu_batch_size"):  # Load GPU batch size
                    self.gpu_batch = conf["gpu_batch_size"]
                if conf.get("template"):  # Load template
                    self.template = conf["template"]
                if conf.get("last_config_path") and os.path.exists(
                        conf["last_config_path"]):
                    self.load_config_from_path(conf["last_config_path"])
                return True
            except Exception as e:
                print(f"Error loading user configuration: {e}")
                return False

    def save_user_conf(self):
        """Save current user configuration preferences"""
        conf = {
            "last_config_path": self.loaded_config_path,
            "gpu_thread_groups": self.thread_groups,
            "last_seed": self.starting_seed,
            "last_deck": self.deck,
            "last_stake": self.stake,
            "last_number_of_seeds": self.number_of_seeds,
            "cutoff": self.cutoff,  # Save cutoff
            "gpu_batch_size": self.gpu_batch,  # Save GPU batch size
            "template": self.template,  # Save template
        }

        try:
            with open(self.USER_CONF_PATH, "w") as f:
                json.dump(conf, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving user configuration: {e}")
            return False

    def load_config_from_path(self, file_path):
        """Load a configuration file from the given path"""
        if not file_path or not os.path.exists(file_path):
            return False

        try:
            with open(file_path, "r") as file:
                config = json.load(file)

            # Clear current configuration
            self.needs_list.clear()
            self.wants_list.clear(
            )  # Set configuration name, description, and author
            # Always use filename for config name, ignore JSON "name" field
            self.config_name = os.path.basename(file_path).replace(
                ".ouija.json", "")
            self.config_description = config.get("description", "")
            self.config_author = config.get("author", "")

            # Load needs and wants
            filter_config = config.get("filter_config", {})
            self.needs_list = filter_config.get("Needs", [])
            self.wants_list = filter_config.get("Wants", [])

            # Load deck if specified
            if "deck" in filter_config:
                deck_name = filter_config["deck"].replace("_", " ")
                self.deck = deck_name

            # Load stake if specified
            if "stake" in filter_config:
                stake_name = filter_config["stake"].replace("_", " ")
                self.stake = stake_name

            # Load negative joker scoring flags
            self.score_natural_negatives = filter_config.get("scoreNaturalNegatives", True)
            self.score_desired_negatives = filter_config.get("scoreDesiredNegatives", True)

            # Update state tracking
            self.loaded_config_path = file_path
            self.config_loaded_from_file = True
            self.config_modified = False

            # Save user preferences
            self.save_user_conf()
            return True
        except Exception as e:
            print(f"Error loading configuration: {e}")
            return False

    def calculate_max_search_ante(self):
        """Calculate the maximum search ante based on desires."""
        max_ante = 0  # Default value
        for need in self.needs_list:
            if "desireByAnte" in need and isinstance(need["desireByAnte"],
                                                     int):
                max_ante = max(max_ante, need["desireByAnte"])
        return max_ante

    def save_config(self, file_path=None):
        """Save the current configuration to file"""
        if not self.config_name:
            return False, "Configuration name cannot be empty"
        # Create configuration object
        config = {
            "name": self.config_name,
            "description": self.config_description
                           or f"Filter configuration created by Ouija GUI",
            "author": self.config_author or "Ouija GUI User",
            "filter_config": {
                "numNeeds": len(self.needs_list),
                "numWants": len(self.wants_list),
                "Needs": self.needs_list,
                "Wants": self.wants_list,
                "maxSearchAnte": self.calculate_max_search_ante(),
                "deck": self.deck.replace(" ", "_"),
                "stake": self.stake.replace(" ", "_"),
                # --- Negative joker scoring flags ---
                "scoreNaturalNegatives": self.score_natural_negatives,
                "scoreDesiredNegatives": self.score_desired_negatives,
            },
        }

        # If no path provided, use the loaded path or generate a new one
        if not file_path:
            if self.loaded_config_path:
                file_path = self.loaded_config_path
            else:
                file_name = self.config_name.lower().replace(
                    " ", "_") + ".ouija.json"
                file_path = os.path.join(self.CONFIG_DIR, file_name)

        try:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, "w") as file:
                json.dump(config, file, indent=4)

            # Update state
            self.loaded_config_path = file_path
            self.config_loaded_from_file = True
            self.config_modified = False
            self.save_user_conf()

            return True, file_path
        except Exception as e:
            return False, str(e)

    def get_config_files(self):
        """Get a list of available configuration files"""
        config_files = []
        try:
            if os.path.exists(self.CONFIG_DIR):
                for file in os.listdir(self.CONFIG_DIR):
                    if file.endswith(".ouija.json"):
                        config_files.append(os.path.join(
                            self.CONFIG_DIR, file))
        except Exception as e:
            print(f"Error listing config files: {e}")

        return config_files

    def add_need(self, need):
        """Add a need to the configuration"""
        self.needs_list.append(need)
        self.config_modified = True
        return True

    def add_want(self, want):
        """Add a want to the configuration"""
        self.wants_list.append(want)
        self.config_modified = True
        return True

    def remove_need(self, index):
        """Remove a need from the configuration"""
        if 0 <= index < len(self.needs_list):
            del self.needs_list[index]
            self.config_modified = True
            return True
        return False

    def remove_want(self, index):
        """Remove a want from the configuration"""
        if 0 <= index < len(self.wants_list):
            del self.wants_list[index]
            self.config_modified = True
            return True
        return False

    def clear_all_criteria(self):
        """Clear all needs and wants"""
        self.needs_list.clear()
        self.wants_list.clear()
        self.config_modified = True

    def get_command_config_path(self):
        """Get the configuration path to use for the command line"""
        # Use the config name from the input box, or fall back to 'default.ouija.json'
        if self.config_name:
            file_name = self.config_name.lower().replace(" ", "_") + ".ouija.json"
        else:
            file_name = "default.ouija.json"
        file_path = os.path.join(self.CONFIG_DIR, file_name)
        self.save_config(file_path)
        return file_path

    def set_setting(self, key, value):
        """Set a user setting value"""
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
            "score_desired_negatives": "score_desired_negatives",
        }
        if key in settings_map:
            setattr(self, settings_map[key], value)
            self.config_modified = True
            self.save_user_conf()
            return True
        return False

    def get_setting(self, key, default=None):
        """Get a user setting value"""
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
            "score_desired_negatives": "score_desired_negatives",
        }
        if key in settings_map:
            return getattr(self, settings_map[key], default)
        return default

    def get_criteria(self):
        """Return the current criteria as a list."""
        criteria = []
        for need in self.config.get("Needs", []):
            criteria.append(
                f"Need: {need['value']} (Ante: {need['desireByAnte']})")
        for want in self.config.get("Wants", []):
            criteria.append(f"Want: {want['value']}")
        return criteria

    def get_user_conf_path(self):
        return self.USER_CONF_PATH

    def get_absolute_config_path(self):
        """Return the absolute path to the currently loaded config file."""
        if self.loaded_config_path:
            # If it's already absolute, return it
            if os.path.isabs(self.loaded_config_path):
                return self.loaded_config_path
            # If it's relative, resolve it against the current working directory
            # which should be the application root (X:\\Ouija)
            return os.path.abspath(self.loaded_config_path)
        return None

    def get_config_dir(self):
        return self.CONFIG_DIR
