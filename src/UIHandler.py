class UIHandler:
    def __init__(self):
        print("UIHandler: Initializing")
        self.leq_durations_seconds = [5, 10, 15, 30, 60, 300]
        self.leq_duration_index = 0

    def get_leq_duration_seconds(self):
        return self.leq_durations_seconds[self.leq_duration_index]

    def cycle_leq_duration(self):
        self.leq_duration_index += 1
        self.leq_duration_index %= len(self.leq_durations_seconds)

        return self.get_leq_duration_seconds()
    
    def set_leq_duration_index(self, index):
        if index < 0 or index >= len(self.leq_durations_seconds):
            raise ValueError("Invalid Leq duration index")

        self.leq_duration_index = index

        return self.get_leq_duration_seconds()