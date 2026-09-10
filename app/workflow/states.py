"""Explicit workflow state machine (see architecture doc section 10)."""

from __future__ import annotations

from enum import Enum, auto


class WorkflowState(Enum):
    INITIALIZE = auto()
    OPEN_BROWSER = auto()
    NAVIGATE = auto()
    WAIT_FOR_AUTH = auto()
    WAIT_FOR_TARGET = auto()
    LOCATE_IMAGE = auto()
    CAPTURE = auto()
    PREPROCESS = auto()
    RECOGNIZE = auto()
    VALIDATE = auto()
    LOCATE_INPUT = auto()
    FILL = auto()
    SUBMIT = auto()
    VERIFY = auto()
    COMPLETE = auto()
    FAILED = auto()


# Allowed transitions: {from_state: {to_state, ...}}
TRANSITIONS: dict[WorkflowState, set[WorkflowState]] = {
    WorkflowState.INITIALIZE: {WorkflowState.OPEN_BROWSER},
    WorkflowState.OPEN_BROWSER: {
        WorkflowState.NAVIGATE,
        WorkflowState.FAILED,
    },
    WorkflowState.NAVIGATE: {
        WorkflowState.WAIT_FOR_AUTH,
        WorkflowState.WAIT_FOR_TARGET,
        WorkflowState.FAILED,
    },
    WorkflowState.WAIT_FOR_AUTH: {
        WorkflowState.WAIT_FOR_TARGET,
        WorkflowState.FAILED,
    },
    WorkflowState.WAIT_FOR_TARGET: {
        WorkflowState.LOCATE_IMAGE,
        WorkflowState.FAILED,
    },
    WorkflowState.LOCATE_IMAGE: {
        WorkflowState.CAPTURE,
        WorkflowState.FAILED,
    },
    WorkflowState.CAPTURE: {
        WorkflowState.PREPROCESS,
        WorkflowState.FAILED,
    },
    WorkflowState.PREPROCESS: {WorkflowState.RECOGNIZE},
    WorkflowState.RECOGNIZE: {
        WorkflowState.VALIDATE,
        WorkflowState.FAILED,
    },
    WorkflowState.VALIDATE: {
        WorkflowState.LOCATE_INPUT,
        WorkflowState.PREPROCESS,
        WorkflowState.FAILED,
    },
    WorkflowState.LOCATE_INPUT: {
        WorkflowState.FILL,
        WorkflowState.FAILED,
    },
    WorkflowState.FILL: {
        WorkflowState.SUBMIT,
        WorkflowState.FAILED,
    },
    WorkflowState.SUBMIT: {
        WorkflowState.VERIFY,
        WorkflowState.FAILED,
    },
    WorkflowState.VERIFY: {
        WorkflowState.COMPLETE,
        WorkflowState.CAPTURE,
        WorkflowState.FAILED,
    },
    WorkflowState.COMPLETE: set(),
    WorkflowState.FAILED: set(),
}


class StateMachine:
    """Tracks the current workflow state and validates transitions."""

    def __init__(self, initial: WorkflowState = WorkflowState.INITIALIZE) -> None:
        self._state = initial

    @property
    def state(self) -> WorkflowState:
        return self._state

    def transition(self, new_state: WorkflowState) -> None:
        allowed = TRANSITIONS.get(self._state, set())
        if new_state not in allowed:
            raise InvalidTransitionError(self._state, new_state)
        self._state = new_state

    def __repr__(self) -> str:
        return f"<StateMachine state={self._state.name}>"


class InvalidTransitionError(Exception):
    def __init__(self, state: WorkflowState, next_state: WorkflowState) -> None:
        super().__init__(f"invalid transition {state.name} -> {next_state.name}")
        self.state = state
        self.next_state = next_state