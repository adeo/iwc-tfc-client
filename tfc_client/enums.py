from enum import Enum, auto


class RunStatus(Enum):
    def _generate_next_value_(name, start, count, last_values):
        return name

    pending = auto()
    applied = auto()
    applying = auto()
    discarded = auto()
    errored = auto()
    canceled = auto()
    planned = auto()
    planned_and_finished = auto()
    planning = auto()
