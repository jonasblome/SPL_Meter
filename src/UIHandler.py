class UIHandler:
    def __init__(self):
        print("UIHandler: Initializing")

        # Available Leq measurement durations in seconds.
        # The UI can select one of these values by changing leq_duration_index.
        self.leq_durations_seconds = [5, 10, 15, 30, 60, 300]
        self.leq_duration_index = 0

    def get_leq_duration_seconds(self):
        """Return the currently selected Leq measurement duration in seconds."""
        return self.leq_durations_seconds[self.leq_duration_index]

    def cycle_leq_duration(self):

        """
        Select the next Leq duration.

        This can later be connected to a UI button.
        Example: 5 s -> 10 s -> 15 s -> ... -> 5 s
        """
        self.leq_duration_index += 1
        self.leq_duration_index %= len(self.leq_durations_seconds)

        return self.get_leq_duration_seconds()
    
    def set_leq_duration_index(self, index):
        """
        Select a Leq duration by index.

        This is mainly useful for tests or direct UI selection.
        """
        if index < 0 or index >= len(self.leq_durations_seconds):
            raise ValueError("Invalid Leq duration index")

        self.leq_duration_index = index

        return self.get_leq_duration_seconds()