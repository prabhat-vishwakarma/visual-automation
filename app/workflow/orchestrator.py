"""Workflow orchestrator.

The orchestrator is the ONLY component allowed to change workflow state. It
owns state transitions and retry policy, and coordinates browser, vision,
OCR, validation, and verification layers.
"""

from __future__ import annotations

import json
from pathlib import Path

from ..browser import BrowserSession
from ..browser.actions import BrowserActions
from ..browser.locators import continue_button, image_region, input_field
from ..browser.navigation import wait_for_selector
from ..browser.screenshots import ScreenshotManager
from ..browser.verification import ResultVerifier
from ..config import AppConfig
from ..exceptions import OCRRecognitionError
from ..ocr.models import OCRResult, WorkflowResult
from ..ocr.paddle_engine import OCREngine
from ..ocr.validator import OCRValidator
from ..telemetry.logger import get_logger, new_run_id, set_run_id
from ..telemetry.metrics import Metrics
from ..vision.preprocess import ImagePreprocessor
from .states import StateMachine, WorkflowState

logger = get_logger(__name__)


class WorkflowOrchestrator:
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.state_machine = StateMachine()
        self.metrics = Metrics()
        self.run_id = new_run_id()
        set_run_id(self.run_id)
        self.browser: BrowserSession | None = None
        self._page_attempts = 0

    async def run(self) -> WorkflowResult:
        self.metrics.increment("workflow_runs_total")
        try:
            self._transition(WorkflowState.OPEN_BROWSER)
            self.browser = BrowserSession(self.config.browser)
            await self.browser.start()

            await self._navigate()

            authenticated_selector = self.config.authentication.authenticated_selector
            if authenticated_selector and self.config.authentication.mode == "manual":
                await self._wait_for_auth(authenticated_selector)

            await self._wait_for_target()

            outcome = False
            for _attempt in range(self.config.workflow.page_retry_limit + 1):
                self._page_attempts += 1
                captured = await self._capture_target_image()
                accepted = await self._ocr_loop(captured)

                await self._locate_and_fill(accepted)

                self._transition(WorkflowState.SUBMIT)
                await self._submit_click()

                outcome = await self._verify()
                if outcome:
                    break

            if not outcome:
                raise OCRRecognitionError("workflow did not verify after submission")

            self._transition(WorkflowState.COMPLETE)
            self.metrics.increment("workflow_success_total")
            self._save_success_artifact(captured)
            return WorkflowResult(True, "COMPLETE", self._page_attempts, None)

        except Exception as exc:
            self.metrics.increment("workflow_failed_total")
            self.metrics.increment(
                f"failure_by_{self._failure_state()}_total"
            )
            reason = str(exc)

            self._transition(WorkflowState.FAILED)

            if self.config.artifacts.save_failures:
                try:
                    await self._save_failure_artifacts(reason)
                except Exception:
                    logger.warning("failure_artifact_write_error")

            logger.error(
                "workflow_failed",
                error_type=type(exc).__name__,
                state=self.state_machine.state.name,
                reason=reason,
            )
            return WorkflowResult(False, "FAILED", self._page_attempts, reason)

        finally:
            self.metrics.flush()
            await self._close_browser()

    # ---- state helpers ------------------------------------------------------

    def _transition(self, state: WorkflowState) -> None:
        self.state_machine.transition(state)
        logger.info("state_transition", state=state.name)

    def _failure_state(self) -> str:
        return self.state_machine.state.name.lower()

    # ---- steps ---------------------------------------------------------------

    async def _navigate(self) -> None:
        self._transition(WorkflowState.NAVIGATE)
        page = await self.browser.get_page()
        for attempt in range(self.config.workflow.navigation_retry_limit + 1):
            try:
                await page.goto(
                    self.config.target.start_url,
                    wait_until="domcontentloaded",
                )
                return
            except Exception:
                if attempt >= self.config.workflow.navigation_retry_limit:
                    raise
                logger.warning("navigation_retry", attempt=attempt + 1)

    async def _wait_for_auth(self, selector: str) -> None:
        self._transition(WorkflowState.WAIT_FOR_AUTH)
        await self.browser.wait_until_authenticated(
            selector,
            self.config.authentication.wait_timeout_seconds,
        )

    async def _wait_for_target(self) -> None:
        self._transition(WorkflowState.WAIT_FOR_TARGET)
        await wait_for_selector(
            await self.browser.get_page(),
            self.config.selectors.challenge_image,
            self.config.workflow.target_wait_timeout_seconds,
            description="challenge image",
        )

    async def _capture_target_image(self) -> bytes:
        state = self.state_machine.state
        if state is WorkflowState.WAIT_FOR_TARGET:
            self._transition(WorkflowState.LOCATE_IMAGE)
            self._transition(WorkflowState.CAPTURE)
        elif state is WorkflowState.LOCATE_IMAGE:
            self._transition(WorkflowState.CAPTURE)
        elif state is not WorkflowState.CAPTURE:
            # Retry path arrives here from VERIFY already in CAPTURE state.
            self._transition(WorkflowState.LOCATE_IMAGE)
            self._transition(WorkflowState.CAPTURE)

        page = await self.browser.get_page()
        locator = image_region(page, self.config.selectors.challenge_image)
        manager = ScreenshotManager()

        last_error: Exception | None = None
        for _attempt in range(self.config.workflow.capture_retry_limit + 1):
            try:
                screenshot = await manager.capture_element(locator)
                return screenshot.data
            except Exception as exc:
                last_error = exc
                logger.warning("capture_retry", attempt=_attempt + 1)
                await page.wait_for_timeout(1000)

        assert last_error is not None
        raise last_error

    async def _ocr_loop(self, captured: bytes) -> str:
        preprocessor = ImagePreprocessor(self.config.preprocessing.variants)
        engine = OCREngine(self.config.ocr)
        validator = OCRValidator(
            self.config.ocr.expected_regex,
            self.config.ocr.min_confidence,
        )

        best_result: OCRResult | None = None

        for variant, image_bytes in preprocessor.generate_variants(captured):
            self._transition(WorkflowState.PREPROCESS)
            self._transition(WorkflowState.RECOGNIZE)

            result = engine.recognize(image_bytes, variant=variant)
            if best_result is None or result.confidence > best_result.confidence:
                best_result = result

            self._transition(WorkflowState.VALIDATE)
            validation = validator.validate(result)
            if validation.accepted:
                logger.info(
                    "ocr_accepted",
                    preprocessing_variant=variant,
                    text=validation.normalized_text,
                    confidence=round(result.confidence, 3),
                )
                return validation.normalized_text

            validator.log_rejection(result, validation)

        raise OCRRecognitionError(self._failure_summary(best_result))

    @staticmethod
    def _failure_summary(best: OCRResult | None) -> str:
        if best is None:
            return "no usable variant produced OCR output"
        return (
            f"all variants rejected: best text={best.text!r} "
            f"confidence={best.confidence:.3f} variant={best.preprocessing_variant}"
        )

    async def _locate_and_fill(self, value: str) -> None:
        self._transition(WorkflowState.LOCATE_INPUT)
        self._transition(WorkflowState.FILL)
        page = await self.browser.get_page()
        await BrowserActions.fill_text(
            input_field(page, self.config.selectors.challenge_input),
            value,
        )

    async def _submit_click(self) -> None:
        page = await self.browser.get_page()
        await BrowserActions.click(
            continue_button(page, self.config.selectors.continue_button)
        )

    async def _verify(self) -> bool:
        self._transition(WorkflowState.VERIFY)
        verifier = ResultVerifier(
            success_selector=self.config.selectors.success_element,
            rejection_selector=self.config.selectors.rejection_element,
            timeout_seconds=self.config.workflow.post_submit_timeout_seconds,
        )
        page = await self.browser.get_page()
        outcome = await verifier.verify(page)
        logger.info("submission_verified", outcome=outcome)

        if outcome == "success":
            self.metrics.increment("submission_success_total")
            return True

        if outcome == "rejected":
            self.metrics.increment("submission_rejected_total")
        else:
            self.metrics.increment("submission_timeout_total")

        self._transition(WorkflowState.CAPTURE)
        return False

    # ---- artifacts -------------------------------------------------------------

    def _artifact_root(self, sub: str) -> Path:
        root = Path(self.config.artifacts.root)
        target = root / sub / self.run_id
        target.mkdir(parents=True, exist_ok=True)
        return target

    def _save_success_artifact(self, captured: bytes) -> None:
        if not self.config.artifacts.save_success_images:
            return
        (self._artifact_root("screenshots") / "challenge.png").write_bytes(captured)

    async def _save_failure_artifacts(self, reason: str) -> None:
        target = self._artifact_root("failures")
        try:
            page = await self.browser.get_page()
            (target / "page.png").write_bytes(await page.screenshot(full_page=False))
        except Exception as exc:
            logger.warning("failure_page_screenshot_error", error=str(exc))

        metadata = {
            "run_id": self.run_id,
            "state": self.state_machine.state.name,
            "attempts": self._page_attempts,
            "failure_reason": reason,
        }
        (target / "metadata.json").write_text(
            json.dumps(metadata, indent=2),
            encoding="utf-8",
        )
        logger.info("failure_artifacts_saved", run_id=self.run_id)

    async def _close_browser(self) -> None:
        if self.browser is not None:
            await self.browser.close()