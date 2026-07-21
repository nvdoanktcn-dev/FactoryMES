import math


class CapacityEngine:
    @staticmethod
    def calculate_required_machines(base_cycle_time, target_cycle_time):
        if not base_cycle_time or not target_cycle_time:
            return 0

        if base_cycle_time <= 0 or target_cycle_time <= 0:
            return 0

        return math.ceil(target_cycle_time / base_cycle_time)