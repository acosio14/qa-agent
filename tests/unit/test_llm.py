from types import SimpleNamespace

import pytest
import openrouter.errors as errors

from qa_agent_cli import llm
from qa_agent_cli.llm import QAAssistant, QAAssistantError, _classify, _ErrorAction


def make_error(cls, msg="boom"):
    """Build an OpenRouter error instance without its httpx-based __init__.

    The real error classes expect an ``httpx.Response``; for classification and
    control-flow tests we only need an instance of the right type whose
    ``str()`` works, so we allocate with ``__new__`` and set ``message``.
    """
    err = cls.__new__(cls)
    err.message = msg
    return err


def resp(content="ok", refusal=None, finish_reason="stop", message=True, choices=True):
    """Build a fake chat response shaped like the OpenRouter SDK's."""
    if not choices:
        return SimpleNamespace(choices=[])
    msg = SimpleNamespace(content=content, refusal=refusal) if message else None
    choice = SimpleNamespace(finish_reason=finish_reason, message=msg)
    return SimpleNamespace(choices=[choice])


class FakeOpenRouter:
    """Stand-in for the OpenRouter client used as a context manager."""

    def __init__(self, *args, **kwargs):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


def make_assistant(monkeypatch, script, default="m1", fallbacks=None):
    """Return (assistant, tried) with ``_send`` scripted from ``script``.

    Each item in ``script`` is either a response object (returned by ``_send``)
    or an ``Exception`` (raised by ``_send``). ``tried`` records, in order, the
    model each ``_send`` call was made against.
    """
    monkeypatch.setattr(llm, "OpenRouter", FakeOpenRouter)
    monkeypatch.setattr(llm.time, "sleep", lambda *a, **k: None)  # no real backoff

    tried: list[str] = []
    seq = iter(script)

    def fake_send(self, open_router, model):
        tried.append(model)
        item = next(seq)
        if isinstance(item, BaseException):
            raise item
        return item

    monkeypatch.setattr(QAAssistant, "_send", fake_send)
    assistant = QAAssistant("sys prompt", "user prompt", default, fallbacks or [])
    return assistant, tried


class TestClassify:
    @pytest.mark.parametrize("cls", llm._RETRY_ERRORS, ids=lambda c: c.__name__)
    def test_transient_errors_retry(self, cls):
        # Arrange
        error = make_error(cls)

        # Act
        action = _classify(error)

        # Assert
        assert action is _ErrorAction.RETRY

    @pytest.mark.parametrize("cls", llm._REROUTE_ERRORS, ids=lambda c: c.__name__)
    def test_model_provider_errors_reroute(self, cls):
        # Arrange
        error = make_error(cls)

        # Act
        action = _classify(error)

        # Assert
        assert action is _ErrorAction.REROUTE

    @pytest.mark.parametrize("cls", llm._FAIL_ERRORS, ids=lambda c: c.__name__)
    def test_client_errors_fail(self, cls):
        # Arrange
        error = make_error(cls)

        # Act
        action = _classify(error)

        # Assert
        assert action is _ErrorAction.FAIL

    def test_unknown_error_defaults_to_reroute(self):
        # Arrange
        error = make_error(errors.OpenRouterDefaultError)

        # Act
        action = _classify(error)

        # Assert
        assert action is _ErrorAction.REROUTE


class TestValidate:
    def test_returns_content_when_usable(self):
        # Arrange
        response = resp("the answer")

        # Act
        answer = QAAssistant._validate(response, "m1")

        # Assert
        assert answer == "the answer"

    def test_length_finish_reason_is_still_usable(self):
        # Arrange
        # A truncated-but-present answer is acceptable.
        response = resp("partial", finish_reason="length")

        # Act
        answer = QAAssistant._validate(response, "m1")

        # Assert
        assert answer == "partial"

    def test_surrounding_whitespace_is_preserved(self):
        # Arrange
        response = resp("  spaced  ")

        # Act
        answer = QAAssistant._validate(response, "m1")

        # Assert
        assert answer == "  spaced  "

    @pytest.mark.parametrize(
        "bad",
        [
            resp(choices=False),
            resp(finish_reason="content_filter"),
            resp(finish_reason="error"),
            resp(message=False),
            resp(refusal="I won't answer that"),
            resp(content=None),
            resp(content=""),
            resp(content="   "),
        ],
        ids=[
            "no_choices",
            "content_filter",
            "finish_error",
            "no_message",
            "refusal",
            "content_none",
            "content_empty",
            "content_whitespace",
        ],
    )
    def test_unusable_response_raises(self, bad):
        # Act / Assert
        with pytest.raises(QAAssistantError):
            QAAssistant._validate(bad, "m1")


class TestGetAnswerSuccess:
    def test_returns_content_on_first_success(self, monkeypatch):
        # Arrange
        assistant, tried = make_assistant(monkeypatch, [resp("hello")])

        # Act
        answer = assistant.GetAnswer()

        # Assert
        assert answer == "hello"
        assert tried == ["m1"]

    def test_retries_same_model_then_succeeds(self, monkeypatch):
        # Arrange
        script = [make_error(errors.ServiceUnavailableResponseError), resp("ok")]
        assistant, tried = make_assistant(monkeypatch, script)

        # Act
        answer = assistant.GetAnswer()

        # Assert
        assert answer == "ok"
        assert tried == ["m1", "m1"]  # same model retried, not re-routed

    def test_retry_exhausts_three_attempts_then_reroutes(self, monkeypatch):
        # Arrange
        err = errors.ServiceUnavailableResponseError
        script = [make_error(err), make_error(err), make_error(err), resp("ok")]
        assistant, tried = make_assistant(monkeypatch, script, fallbacks=["m2"])

        # Act
        answer = assistant.GetAnswer()

        # Assert
        assert answer == "ok"
        assert tried == ["m1", "m1", "m1", "m2"]  # 3 tries cap, then next model

    def test_reroute_error_switches_model_without_retrying(self, monkeypatch):
        # Arrange
        script = [make_error(errors.TooManyRequestsResponseError), resp("ok")]
        assistant, tried = make_assistant(monkeypatch, script, fallbacks=["m2"])

        # Act
        answer = assistant.GetAnswer()

        # Assert
        assert answer == "ok"
        assert tried == ["m1", "m2"]  # only one attempt on m1


class TestGetAnswerFailure:
    def test_fail_error_stops_immediately(self, monkeypatch):
        # Arrange
        script = [make_error(errors.UnauthorizedResponseError, "bad key")]
        assistant, tried = make_assistant(monkeypatch, script, fallbacks=["m2", "m3"])

        # Act / Assert
        with pytest.raises(QAAssistantError) as exc:
            assistant.GetAnswer()
        assert "Unrecoverable" in str(exc.value)
        assert tried == ["m1"]  # fallbacks never attempted

    def test_all_models_exhausted_raises(self, monkeypatch):
        # Arrange
        script = [
            make_error(errors.TooManyRequestsResponseError),
            make_error(errors.TooManyRequestsResponseError),
        ]
        assistant, tried = make_assistant(monkeypatch, script, fallbacks=["m2"])

        # Act / Assert
        with pytest.raises(QAAssistantError) as exc:
            assistant.GetAnswer()
        assert "All models failed" in str(exc.value)
        assert tried == ["m1", "m2"]

    def test_unusable_response_fails_without_trying_fallbacks(self, monkeypatch):
        # Arrange
        assistant, tried = make_assistant(monkeypatch, [resp(content=None)], fallbacks=["m2"])

        # Act / Assert
        with pytest.raises(QAAssistantError):
            assistant.GetAnswer()
        assert tried == ["m1"]  # validation failure is fatal, not re-routed
