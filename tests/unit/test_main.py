import pytest

from qa_agent_cli import main
from qa_agent_cli.llm import QAAssistantError


# --------------------------------------------------------------------------- #
# resolve_models
# --------------------------------------------------------------------------- #
class TestResolveModels:
    def test_none_returns_the_default_model(self):
        # Arrange / Act
        default, fallbacks = main.resolve_models(None)

        # Assert
        assert default == main.FREE_MODELS[main.DEFAULT_MODEL_ALIAS]

    def test_valid_alias_selects_that_model(self):
        # Arrange / Act
        default, fallbacks = main.resolve_models("gpt-oss-120")

        # Assert
        assert default == main.FREE_MODELS["gpt-oss-120"]

    def test_default_is_never_its_own_fallback(self):
        # Arrange / Act
        default, fallbacks = main.resolve_models("gpt-oss-120")

        # Assert
        assert default not in fallbacks
        assert len(fallbacks) == len(main.FREE_MODELS) - 1

    def test_every_alias_excludes_itself_from_fallbacks(self):
        # Arrange / Act / Assert
        for alias in main.FREE_MODELS:
            default, fallbacks = main.resolve_models(alias)
            assert default not in fallbacks
            assert set(fallbacks) == set(main.FREE_MODELS.values()) - {default}

    def test_unknown_alias_raises_value_error(self):
        # Arrange / Act / Assert
        with pytest.raises(ValueError) as exc:
            main.resolve_models("does-not-exist")
        assert "unknown model" in str(exc.value)


# --------------------------------------------------------------------------- #
# run_pipeline
# --------------------------------------------------------------------------- #
class FakeAssistant:
    """Stand-in for QAAssistant that records construction and returns a fixed answer."""

    last_args: tuple[str, str, str, list[str]] | None = None

    def __init__(self, system_prompt, user_prompt, default_model, fallback_models):
        FakeAssistant.last_args = (system_prompt, user_prompt, default_model, fallback_models)
        self.answering_model = None

    def get_answer(self):
        self.answering_model = "answered-by-model"
        return "the answer"


def _stub_pipeline(monkeypatch, assistant_cls=FakeAssistant):
    """Stub parse/retrieve/format and QAAssistant so run_pipeline needs no I/O."""
    calls = {}
    monkeypatch.setattr(
        main.file_parser, "parse", lambda path: calls.setdefault("path", path) or ["pf"]
    )
    monkeypatch.setattr(
        main.retriever,
        "retrieve_top_k_chunks",
        lambda files, question, k: calls.setdefault("k", k) or [["chunk"]],
    )
    monkeypatch.setattr(
        main.formatter, "format_prompts", lambda chunks, question: ("sys", "user")
    )
    monkeypatch.setattr(main.llm, "QAAssistant", assistant_cls)
    return calls


class TestRunPipeline:
    def test_returns_answer_and_answering_model(self, monkeypatch):
        # Arrange
        _stub_pipeline(monkeypatch)

        # Act
        answer, model = main.run_pipeline("some/path", "a question?", "m1", ["m2"])

        # Assert
        assert answer == "the answer"
        assert model == "answered-by-model"

    def test_wires_inputs_through_to_the_assistant(self, monkeypatch):
        # Arrange
        _stub_pipeline(monkeypatch)

        # Act
        main.run_pipeline("some/path", "a question?", "m1", ["m2", "m3"])

        # Assert
        assert FakeAssistant.last_args is not None
        system_prompt, user_prompt, default_model, fallbacks = FakeAssistant.last_args
        assert (system_prompt, user_prompt) == ("sys", "user")
        assert default_model == "m1"
        assert fallbacks == ["m2", "m3"]

    def test_uses_the_configured_retrieval_k(self, monkeypatch):
        # Arrange
        calls = _stub_pipeline(monkeypatch)

        # Act
        main.run_pipeline("some/path", "q", "m1", [])

        # Assert
        assert calls["k"] == main.RETRIEVAL_K

    def test_propagates_assistant_errors(self, monkeypatch):
        # Arrange
        class BoomAssistant(FakeAssistant):
            def get_answer(self):
                raise QAAssistantError("no models worked")

        _stub_pipeline(monkeypatch, assistant_cls=BoomAssistant)

        # Act / Assert
        with pytest.raises(QAAssistantError):
            main.run_pipeline("some/path", "q", "m1", [])


# --------------------------------------------------------------------------- #
# main (CLI shell + exit codes)
# --------------------------------------------------------------------------- #
def _run_main(monkeypatch, argv, key="sk-or-test"):
    """Invoke main() with the given argv and API-key state."""
    monkeypatch.setattr("sys.argv", ["qa-agent", *argv])
    if key is None:
        monkeypatch.delenv(main.API_KEY_ENV, raising=False)
    else:
        monkeypatch.setenv(main.API_KEY_ENV, key)
    return main.main()


class TestMain:
    def test_missing_api_key_returns_2(self, monkeypatch, capsys):
        # Arrange / Act
        rc = _run_main(monkeypatch, ["path", "q"], key=None)

        # Assert
        assert rc == 2
        assert main.API_KEY_ENV in capsys.readouterr().err

    def test_unknown_model_exits_with_code_2(self, monkeypatch):
        # Arrange / Act / Assert
        with pytest.raises(SystemExit) as exc:
            _run_main(monkeypatch, ["path", "q", "--model", "bogus"])
        assert exc.value.code == 2

    def test_success_prints_answer_and_model_and_returns_0(self, monkeypatch, capsys):
        # Arrange
        monkeypatch.setattr(
            main, "run_pipeline", lambda *a, **k: ("42", "google/gemma-4-31b-it:free")
        )

        # Act
        rc = _run_main(monkeypatch, ["path", "what is the answer?"])

        # Assert
        out = capsys.readouterr().out
        assert rc == 0
        assert "42" in out
        assert "Model: google/gemma-4-31b-it:free" in out

    def test_pipeline_failure_returns_1(self, monkeypatch, capsys):
        # Arrange
        def boom(*a, **k):
            raise QAAssistantError("all models failed")

        monkeypatch.setattr(main, "run_pipeline", boom)

        # Act
        rc = _run_main(monkeypatch, ["path", "q"])

        # Assert
        assert rc == 1
        assert "couldn't answer" in capsys.readouterr().err

    def test_unreadable_path_returns_1(self, monkeypatch, capsys):
        # Arrange
        def missing(*a, **k):
            raise FileNotFoundError("No such file or directory: path")

        monkeypatch.setattr(main, "run_pipeline", missing)

        # Act
        rc = _run_main(monkeypatch, ["path", "q"])

        # Assert
        assert rc == 1
        assert "could not read" in capsys.readouterr().err
