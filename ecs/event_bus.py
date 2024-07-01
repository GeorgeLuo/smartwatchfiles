class EventBus:
    def __init__(self):
        self.events = []

    def push_event(self, event_type, event_data):
        self.events.append((event_type, event_data))

    def get_events(self):
        events = self.events[:]
        self.events.clear()
        return events
