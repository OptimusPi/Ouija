"""
Result wrapper class for standardized operation returns
"""


class Result:
    """Standard result wrapper for operations"""

    def __init__(self, success, data=None, error=None):
        self.success = success
        self.data = data
        self.error = error

    @classmethod
    def success(cls, data=None):
        """Create a successful result"""
        return cls(True, data=data)

    @classmethod
    def error(cls, message):
        """Create an error result"""
        return cls(False, error=message)

    def __bool__(self):
        """Allow result to be used in boolean context"""
        return self.success

    def __str__(self):
        if self.success:
            return f"Success: {self.data}"
        else:
            return f"Error: {self.error}"
