from enum import Enum, auto


class RunStatus(Enum):
    def _generate_next_value_(name, start, count, last_values):
        return name

    applied = auto()
    applying = auto()
    canceled = auto()
    discarded = auto()
    errored = auto()
    pending = auto()
    plan_queued = auto()
    planned = auto()
    planned_and_finished = auto()
    planning = auto()
