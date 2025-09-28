import asyncio

class Dispatcher:
    def __init__(self):
        self.listeners: dict[str, list] = {}

    def subscribe(self, event_name: str, handler):
        """Register a handler for an event name."""
        self.listeners.setdefault(event_name, []).append(handler)

    async def publish(self, event_name: str, payload: dict):
        """Publish an event to all subscribers."""
        for handler in self.listeners.get(event_name, []):
            asyncio.create_task(handler(payload))