from enum import Enum, auto


class RunStatus(str, Enum):
    def _generate_next_value_(name, start, count, last_values):
        return name

    pending = auto()
    plan_queued = auto()
    planning = auto()
    planned = auto()
    cost_estimating = auto()
    cost_estimated = auto()
    policy_checking = auto()
    policy_override = auto()
    policy_soft_failed = auto()
    policy_checked = auto()
    confirmed = auto()
    planned_and_finished = auto()
    apply_queued = auto()
    applying = auto()
    applied = auto()
    discarded = auto()
    errored = auto()
    canceled = auto()
    force_canceled = auto()

class WorkspaceSort(str, Enum):
    name = "name"
    name_reverse = "-name"
    current_run = "current-run.created-at"
    current_run_reverse = "-current-run.created-at"

    def __str__(self):
        return self.value


class VarCat(str, Enum):
    def _generate_next_value_(name, start, count, last_values):
        return name

    terraform = auto()
    env = auto()

    def __str__(self):
        return self.value


class NotificationTrigger(str, Enum):
    def _generate_next_value_(name, start, count, last_values):
        return f"run:{name}"

    applying = auto()
    completed = auto()
    created = auto()
    errored = auto()
    needs_attention = auto()
    planning = auto()

    def __str__(self):
        return self.value


class NotificationsDestinationType(str, Enum):
    def _generate_next_value_(name, start, count, last_values):
        return name

    generic = auto()
    slack = auto()
