"""Data logger for storing soil measurements."""

import csv
import os
from datetime import datetime
from typing import Dict, Any, Optional


class DataLogger:
    """Logs soil sensor measurements to CSV file."""

    def __init__(self, log_dir: str = "./logs"):
        """
        Initialize the data logger.

        Args:
            log_dir: Directory to store log files
        """
        self.log_dir = log_dir
        self.log_file: Optional[str] = None
        self._ensure_log_dir()
        self._create_log_file()

    def _ensure_log_dir(self):
        """Create log directory if it doesn't exist."""
        os.makedirs(self.log_dir, exist_ok=True)

    def _create_log_file(self):
        """Create or open the log file for today."""
        today = datetime.now().strftime("%Y-%m-%d")
        self.log_file = os.path.join(self.log_dir, f"soil_measurements_{today}.csv")

        # Create file with header if it doesn't exist
        if not os.path.exists(self.log_file):
            with open(self.log_file, 'w', newline='') as f:
                fieldnames = [
                    'timestamp',
                    'temperature',
                    'moisture',
                    'ec',
                    'ph',
                    'nitrogen',
                    'phosphorus',
                    'potassium',
                    'salinity',
                    'battery'
                ]
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()

    def log(self, data: Dict[str, Any]) -> bool:
        """
        Log measurement data to CSV file.

        Args:
            data: Dictionary containing sensor readings

        Returns:
            True if successful, False otherwise
        """
        if not self.log_file:
            print("Log file not initialized")
            return False

        try:
            # Add timestamp if not present
            if 'timestamp' not in data:
                data['timestamp'] = datetime.now().isoformat()

            with open(self.log_file, 'a', newline='') as f:
                fieldnames = [
                    'timestamp',
                    'temperature',
                    'moisture',
                    'ec',
                    'ph',
                    'nitrogen',
                    'phosphorus',
                    'potassium',
                    'salinity',
                    'battery'
                ]
                writer = csv.DictWriter(f, fieldnames=fieldnames)

                # Write only the fields that exist
                row = {key: data.get(key, '') for key in fieldnames}
                writer.writerow(row)

            print(f"Data logged successfully to {self.log_file}")
            return True

        except Exception as e:
            print(f"Error logging data: {e}")
            return False

    def get_latest_measurements(self, count: int = 10) -> list:
        """
        Get the latest N measurements from the log file.

        Args:
            count: Number of recent measurements to retrieve

        Returns:
            List of measurement dictionaries
        """
        if not self.log_file or not os.path.exists(self.log_file):
            return []

        try:
            measurements = []
            with open(self.log_file, 'r', newline='') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                # Get the last 'count' rows
                measurements = rows[-count:] if len(rows) > count else rows
            return measurements

        except Exception as e:
            print(f"Error reading measurements: {e}")
            return []
