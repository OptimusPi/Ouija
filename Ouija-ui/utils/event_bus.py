"""
Event bus for centralized event management
"""

from collections import defaultdict


class EventBus:
    """Centralized event management system"""

    def __init__(self):
        self._listeners = defaultdict(list)

    def subscribe(self, event_type, callback):
        """Subscribe to an event type
        
        Args:
            event_type (str): Type of event to listen for
            callback (callable): Function to call when event occurs
        """
        self._listeners[event_type].append(callback)

    def unsubscribe(self, event_type, callback):
        """Unsubscribe from an event type
        
        Args:
            event_type (str): Type of event to stop listening for
            callback (callable): Function to remove from listeners
        """
        if callback in self._listeners[event_type]:
            self._listeners[event_type].remove(callback)

    def publish(self, event_type, data=None):
        """Publish an event to all subscribers
        
        Args:
            event_type (str): Type of event to publish
            data: Optional data to pass to listeners
        """
        for callback in self._listeners[event_type]:
            try:
                callback(data)
            except Exception as e:
                print(f"Error in event callback for {event_type}: {e}")

    def clear(self, event_type=None):
        """Clear listeners
        
        Args:
            event_type (str, optional): Clear specific event type, or all if None
        """
        if event_type:
            self._listeners[event_type].clear()
        else:
            self._listeners.clear()
