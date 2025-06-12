"""
Database Model - Handles database interactions for Ouija seed finder
"""

import os
import sys
import threading
from pathlib import Path

import duckdb
import pandas as pd


class DatabaseModel:
    """Model for handling database operations with DuckDB"""    
    def __init__(self):
        """Initialize the database model"""
        self.connection = None
        self.db_path = None
        self._schema_established = False
        self.current_db_path = None
        self.current_config_path = None  # Store config path for reconnection
        self.conn = None
        self.header_columns = None
        self.on_results_table_reset = None  # Callback for UI refresh after table reset
        self.db_lock = threading.RLock()

        # Determine the correct database directory based on runtime context
        self.DB_DIR = self._get_database_directory()
        
        # Ensure database directory exists
        os.makedirs(self.DB_DIR, exist_ok=True)

    def _get_database_directory(self):
        """Get the correct database directory based on whether we're running in development or packaged"""
        if getattr(sys, 'frozen', False):
            # Running as packaged executable - use the executable's directory
            exe_dir = os.path.dirname(sys.executable)
            return os.path.join(exe_dir, "ouija_database")
        else:
            # Running in development - check both locations
            # First go up from models to Ouija-ui, then to Ouija
            models_dir = os.path.dirname(os.path.abspath(__file__))
            ui_dir = os.path.dirname(models_dir)
            root_dir = os.path.dirname(ui_dir)
            
            # Check if we're running from distribution directory (has ouija_database folder)
            dist_db_dir = os.path.join(os.getcwd(), "ouija_database")
            # Check root directory (for normal development)
            root_db_dir = os.path.join(root_dir, "ouija_database")
            
            if os.path.exists(dist_db_dir):
                return dist_db_dir
            elif os.path.exists(root_db_dir):
                return root_db_dir
            else:
                # Default to root location (will be created if needed)
                return root_db_dir

    def get_db_path_from_config(self, config_path):
        """Derive database path from configuration path, always in ouija_database directory."""
        if not config_path:
            return None
        base = os.path.basename(config_path)
        name, _ = os.path.splitext(base)
        return os.path.join(self.DB_DIR, f"{name}.duckdb")

    def connect(self, config_path):
        """Connect to the database based on config path

        Args:
            config_path: Path to the config file (used to determine database location)

        Returns:
            bool: True if connection successful, False otherwise
        """
        with self.db_lock:
            try:
                db_path = self.get_db_path_from_config(config_path)

                # Check if already connected to the same database
                if self.current_db_path == db_path and self.connection:
                    return True                # Close existing connection if switching databases
                if self.connection:
                    self.close()

                # Connect to the database
                self.connection = duckdb.connect(db_path)
                self.conn = self.connection  # Set alias
                self.current_db_path = db_path  # Set current path
                self.current_config_path = config_path  # Store config path for reconnection
                self.db_path = db_path

                # Reset schema tracking when connecting to any database
                self._schema_established = False
                self.header_columns = None  # Reset header columns too!

                # Create the results table if it doesn't exist
                self.create_results_table()
                return True
            except Exception as e:
                print(f"Error connecting to database: {e}")
                self.connection = None
                self.conn = None
                self.current_db_path = None
                self.current_config_path = None
                return False

    def close(self):
        """Close the current database connection"""
        with self.db_lock:
            if self.connection:
                self.connection.close()
                self.connection = None
            if self.conn:
                self.conn = None
            self.current_db_path = None
            self.current_config_path = None

    def table_exists(self):
        """Check if the results table exists in the current database"""
        with self.db_lock:
            if not self.conn:
                return False
            try:
                result = self.conn.execute(
                    "SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'results'"
                ).fetchone()
                return result is not None and result[0] > 0
            except Exception:
                return False

    def create_results_table(self):
        """Create the basic results table"""
        with self.db_lock:
            if not self.conn:
                return False
            try:
                table_was_created = False
                if not self.table_exists():
                    try:
                        self.conn.execute(
                            """
                            CREATE TABLE results
                            (
                                Seed  TEXT PRIMARY KEY,
                                Score INTEGER
                            )
                            """
                        )
                        # Create an index on Score column for faster sorting
                        self.conn.execute(
                            'CREATE INDEX IF NOT EXISTS idx_score ON results ("Score");'
                        )
                        self.conn.execute(
                            'CREATE INDEX IF NOT EXISTS idx_seed ON results ("Seed");'
                        )
                        table_was_created = True
                    except Exception as e:
                        # Ignore "column already exists" errors which can happen during race conditions
                        error_msg = str(e).lower()
                        if "already exists" not in error_msg and "duplicate column" not in error_msg:
                            raise  # Re-raise any other error
                if table_was_created and self.on_results_table_reset:
                    self.on_results_table_reset()
                return True
            except Exception as e:
                print(f"Error creating results table: {e}")
                return False

    def delete_all_results(self):
        """Delete all results by completely removing and recreating the database file"""
        with self.db_lock:
            if not self.connection or not self.current_db_path:
                return False

            try:
                # Close the database connection
                self.connection.close()
                self.connection = None
                self.conn = None

                # Remove the database file if it exists
                db_path = Path(self.current_db_path)
                if db_path.exists():
                    os.remove(db_path)

                # Reset schema tracking and connection state
                self._schema_established = False
                self.header_columns = None                # Reconnect to create a fresh database
                if self.current_config_path:
                    self.connect(self.current_config_path)
                    if self.on_results_table_reset:
                        self.on_results_table_reset()
                    return True
                return False

            except Exception as e:
                print(f"Error deleting database file: {e}")
                return False

    def process_csv_line(self, line, header_columns=None):
        """Process a CSV line directly from string"""
        with self.db_lock:
            if not self.conn:
                return None

            try:
                # Remove the leading '|' character if present
                if line.startswith("|"):
                    csv_line = line[1:].strip()
                else:
                    csv_line = line.strip()

                # Split by comma
                parts = csv_line.split(",")

                # Process values: first value (Seed) is STRING, all others are INTEGER
                values = []
                for i, part in enumerate(parts):
                    if i == 0:  # Seed column
                        values.append(part.strip())  # String value
                    else:  # All other columns
                        try:
                            # Force integer conversion - truncate any decimal part
                            part_str = part.strip()
                            if "." in part_str:
                                part_str = part_str.split(".")[0]
                            values.append(int(part_str))
                        except ValueError:
                            values.append(0)  # Default to 0 if conversion fails

                # Use provided header columns or generate default ones
                if header_columns is None:
                    header_columns = ["Seed"]
                    header_columns.extend([f"Col{i}" for i in range(1, len(values))])

                # Ensure values match header length
                if len(values) < len(header_columns):
                    values.extend([0] * (len(header_columns) - len(values)))
                elif len(values) > len(header_columns):
                    values = values[: len(header_columns)]

                return header_columns, values
            except Exception as e:
                print(f"Error processing CSV line: {e}")
                return None

    def insert_result(self, columns, values):
        """Insert a result row into the database"""
        with self.db_lock:
            if not self.conn:
                return False

            try:
                # Ensure the table exists and has the right columns
                if not self.table_exists():
                    self.create_table(columns)

                self.ensure_columns_exist(columns)

                # Use Seed column as the unique key for upsert
                seed_value = values[0] if values else None
                if not seed_value:
                    return False

                # Create column names and placeholder values for the SQL statement
                column_names = ", ".join([f'"{col}"' for col in columns])
                placeholders = ", ".join(["?"] * len(values))

                # Insert or replace the row
                query = f"INSERT OR REPLACE INTO results ({column_names}) VALUES ({placeholders})"
                self.conn.execute(query, values)

                return True
            except Exception as e:
                print(f"Error upserting result: {e}")
                return False

    def create_table(self, columns):
        """Create the results table with the given columns if it doesn't exist."""
        with self.db_lock:
            if not self.conn:
                return False

            try:
                # Check if table exists first
                if self.table_exists():
                    # Table exists, don't drop it - just return
                    return True

                # Create the table with a strict schema:
                # - Seed is VARCHAR PRIMARY KEY
                # - All other columns are INTEGER
                columns_def = []
                for col in columns:
                    if col == "Seed":
                        columns_def.append(f'"{col}" VARCHAR PRIMARY KEY')
                    else:
                        columns_def.append(f'"{col}" INTEGER')

                # Create the table
                self.conn.execute(f"CREATE TABLE results ({', '.join(columns_def)});")

                # Create an index on the Score column for faster sorting
                if "Score" in columns:
                    try:
                        self.conn.execute(
                            'CREATE INDEX IF NOT EXISTS idx_score ON results ("Score");'
                        )
                    except Exception:
                        pass

                return True
            except Exception as e:
                # Only print if it's not an "already exists" error
                if "already exists" not in str(e).lower():
                    print(f"Error creating table: {e}")
                return False

    def ensure_columns_exist(self, columns):
        """Ensure all specified columns exist in the results table."""
        with self.db_lock:
            if not self.conn:
                print("[DB] No connection when ensuring columns exist.")
                return False

            try:
                # Get current table schema
                try:
                    existing_cols = self.conn.execute("PRAGMA table_info(results)").fetchall()
                except Exception as e:
                    print(f"Error fetching table info: {e}")
                    # Attempt to reset connection if possible
                    try:
                        if self.current_db_path:
                            print("[DB] Attempting to reconnect due to failed PRAGMA table_info.")
                            self.connect(self.current_db_path)
                            existing_cols = self.conn.execute("PRAGMA table_info(results)").fetchall()
                        else:
                            return False
                    except Exception as reconnect_error:
                        print(f"[DB] Reconnection failed: {reconnect_error}")
                        return False
                existing_col_names = [col[1] for col in existing_cols]

                # Add any missing columns
                for col in columns:
                    if col not in existing_col_names and col != "Seed":
                        try:
                            # Use IF NOT EXISTS to handle race conditions gracefully
                            self.conn.execute(
                                f'ALTER TABLE results ADD COLUMN IF NOT EXISTS "{col}" INTEGER DEFAULT 0'
                            )
                        except Exception as col_error:
                            error_msg = str(col_error).lower()
                            # Ignore "already exists" errors - they're harmless race conditions
                            if "already exists" not in error_msg and "duplicate column" not in error_msg:
                                print(f"Error adding column {col}: {col_error}")
                                continue
                        # Update tracking if column was added or already existed
                        existing_col_names.append(col)

                self.conn.commit()  # Commit after all column additions
                return True
            except Exception as e:
                print(f"Error ensuring columns exist: {e}")
                # Optionally, try to reset connection here as well
                return False

    def query_results(self, sort_column="Score", descending=True, limit=1000):
        """Query results from the database, optionally sorted and limited

        Args:
            sort_column: Column to sort by (default: "Score")
            descending: Sort in descending order (default: True)
            limit: Maximum number of results to return (default: 1000)
        """
        with self.db_lock:
            if not self.conn or not self.table_exists():
                return None

            try:  # Query with optional sorting, limited to top 1000 results by default
                direction = "DESC" if descending else "ASC"
                # Sort by primary column first, then by Seed to prevent results from getting jumbled up on refresh
                result = self.conn.execute(
                    f'SELECT * FROM results ORDER BY "{sort_column}" {direction}, "Seed" ASC LIMIT {limit}'
                )
                return result.fetch_df() if result else None
            except Exception:
                # Silent failure, just return None
                return None

    def get_dataframe(self):
        """Get results as a pandas DataFrame"""
        with self.db_lock:
            return self.query_results()

    def export_to_csv(self, file_path, limit=None):
        """Export results to CSV file
        
        Args:
            file_path: Path where CSV file will be saved
            limit: Maximum number of rows to export (None for all)
            
        Returns:
            bool: True if successful, False otherwise
        """
        with self.db_lock:
            try:
                df = self.query_results(limit=limit or 10000)  # Default to 10k if no limit
                if df is not None and not df.empty:
                    df.to_csv(file_path, index=False)
                    return True
                return False
            except Exception as e:
                print(f"Error exporting to CSV: {e}")
                return False

    def export_to_excel(self, file_path, limit=None):
        """Export results to Excel file
        
        Args:
            file_path: Path where Excel file will be saved
            limit: Maximum number of rows to export (None for all)
            
        Returns:
            bool: True if successful, False otherwise
        """
        with self.db_lock:
            try:
                df = self.query_results(limit=limit or 10000)  # Default to 10k if no limit
                if df is not None and not df.empty:
                    # Requires openpyxl for Excel export
                    df.to_excel(file_path, index=False, engine='openpyxl')
                    return True
                return False
            except Exception as e:
                print(f"Error exporting to Excel: {e}")
                print("Note: Excel export requires 'pip install openpyxl'")
                return False

    def export_to_json(self, file_path, limit=None):
        """Export results to JSON file
        
        Args:
            file_path: Path where JSON file will be saved
            limit: Maximum number of rows to export (None for all)
            
        Returns:
            bool: True if successful, False otherwise
        """
        with self.db_lock:
            try:
                df = self.query_results(limit=limit or 10000)  # Default to 10k if no limit
                if df is not None and not df.empty:
                    df.to_json(file_path, orient='records', indent=2)
                    return True
                return False
            except Exception as e:
                print(f"Error exporting to JSON: {e}")
                return False

    def get_export_stats(self):
        """Get statistics about exportable data
        
        Returns:
            dict: Statistics including row count, columns, etc.
        """
        with self.db_lock:
            try:
                if not self.conn or not self.table_exists():
                    return {"total_rows": 0, "columns": []}

                # Get row count
                row_count = self.conn.execute("SELECT COUNT(*) FROM results").fetchone()[0]

                # Get column names
                columns = self.conn.execute("PRAGMA table_info(results)").fetchall()
                column_names = [col[1] for col in columns]

                return {
                    "total_rows": row_count,
                    "columns": column_names,
                    "database_path": self.current_db_path
                }
            except Exception as e:
                print(f"Error getting export stats: {e}")
                return {"total_rows": 0, "columns": []}
