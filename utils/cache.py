from datetime import timedelta, datetime


class Cache:
    def __init__(self):
        self.memory = {}  # {url: timestamp}
        self.expiration_time = timedelta(days=1)  # 하루(24시간)

    def filter_new(self, values):
        new_values = [value for value in values if value not in self.memory]
        return new_values

    def add_values(self, values):
        now = datetime.now()
        for value in values:
            self.memory[value] = now

    def clean_old_values(self):
        now = datetime.now()
        self.memory = {
            value: timestamp for value, timestamp in self.memory.items()
            if now < timestamp + self.expiration_time
        }

