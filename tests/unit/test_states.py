"""Unit tests for the workflow state machine."""

import pytest

from app.workflow.states import InvalidTransitionError, StateMachine, WorkflowState


def test_initial_state():
    machine = StateMachine()
    assert machine.state is WorkflowState.INITIALIZE


def test_valid_transition():
    machine = StateMachine()
    machine.transition(WorkflowState.OPEN_BROWSER)
    machine.transition(WorkflowState.NAVIGATE)
    assert machine.state is WorkflowState.NAVIGATE


def test_invalid_transition_raises():
    machine = StateMachine()
    machine.transition(WorkflowState.OPEN_BROWSER)
    machine.transition(WorkflowState.NAVIGATE)
    with pytest.raises(InvalidTransitionError):
        machine.transition(WorkflowState.CAPTURE)


def test_complete_is_terminal():
    machine = StateMachine()
    machine.transition(WorkflowState.OPEN_BROWSER)
    machine.transition(WorkflowState.NAVIGATE)
    machine.transition(WorkflowState.WAIT_FOR_TARGET)
    machine.transition(WorkflowState.LOCATE_IMAGE)
    machine.transition(WorkflowState.CAPTURE)
    machine.transition(WorkflowState.PREPROCESS)
    machine.transition(WorkflowState.RECOGNIZE)
    machine.transition(WorkflowState.VALIDATE)
    machine.transition(WorkflowState.LOCATE_INPUT)
    machine.transition(WorkflowState.FILL)
    machine.transition(WorkflowState.SUBMIT)
    machine.transition(WorkflowState.VERIFY)
    machine.transition(WorkflowState.COMPLETE)
    assert machine.state is WorkflowState.COMPLETE
    with pytest.raises(InvalidTransitionError):
        machine.transition(WorkflowState.CAPTURE)