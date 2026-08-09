import logging
import os
import time
from enum import Enum, auto

from openrouter import OpenRouter
import openrouter.errors as errors
from dotenv import load_dotenv

load_dotenv()  # does this need to cached?

logger = logging.getLogger(__name__)

MAX_RETRIES = 3  # per-model attempts for transient errors


class QAAssistantError(Exception):
    """Raised when no usable answer could be obtained from any model."""


class _ErrorAction(Enum):
    RETRY = auto()    # transient/server-side: retry the SAME model
    REROUTE = auto()  # model- or provider-specific: try the NEXT model
    FAIL = auto()     # unrecoverable (client/auth/quota): stop immediately


# Transient failures. The same model is likely to succeed on another attempt.
_RETRY_ERRORS = (
    errors.NoResponseError,
    errors.RequestTimeoutResponseError,
    errors.EdgeNetworkTimeoutResponseError,
    errors.InternalServerResponseError,
    errors.ServiceUnavailableResponseError,
    errors.BadGatewayResponseError,
)

# The model or its upstream provider is the problem. A different model may work.
_REROUTE_ERRORS = (
    errors.TooManyRequestsResponseError,      # 429 rate limit on this model
    errors.ProviderOverloadedResponseError,   # upstream provider is saturated
    errors.NotFoundResponseError,             # 404 model id unavailable
    errors.ResponseValidationError,           # model returned a malformed body
)

# Our request or account is the problem. Retrying or re-routing cannot help.
_FAIL_ERRORS = (
    errors.BadRequestResponseError,           # 400 malformed request
    errors.UnauthorizedResponseError,         # 401 bad/missing API key
    errors.PaymentRequiredResponseError,      # 402 out of credits
    errors.ForbiddenResponseError,            # 403 not permitted
    errors.ConflictResponseError,             # 409 conflicting request
    errors.PayloadTooLargeResponseError,      # 413 prompt too large
    errors.UnprocessableEntityResponseError,  # 422 invalid parameters
)


def _classify(error: Exception) -> _ErrorAction:
    """Map an OpenRouter error to a handling strategy based on its severity."""
    if isinstance(error, _FAIL_ERRORS):
        return _ErrorAction.FAIL
    if isinstance(error, _RETRY_ERRORS):
        return _ErrorAction.RETRY
    if isinstance(error, _REROUTE_ERRORS):
        return _ErrorAction.REROUTE
    # Unknown OpenRouter error: give the other models a chance before giving up.
    return _ErrorAction.REROUTE


class QAAssistant:
    def __init__(
        self,
        system_prompt: str,
        user_prompt: str,
        default_model: str,
        fallback_models: list[str],
    ) -> None:

        self.system_prompt = system_prompt
        self.user_prompt = user_prompt
        self.model = default_model
        self.fallback_models = fallback_models
        # The model that actually produced the answer (set by get_answer);
        # may be a fallback rather than the default if the default failed.
        self.answering_model: str | None = None

    def get_answer(self) -> str:
        """Return a validated answer, trying the default model then fallbacks.

        For each model we retry up to ``MAX_RETRIES`` times on transient
        errors, re-route to the next model on model/provider errors, and fail
        immediately on unrecoverable client errors or an unusable response.
        """
        models = [self.model] + list(self.fallback_models)
        last_error: Exception | None = None

        with OpenRouter(api_key=os.getenv("OPENROUTER_API_KEY")) as open_router:
            for model in models:
                for attempt in range(1, MAX_RETRIES + 1):
                    try:
                        logger.info("Requesting answer from '%s' (attempt %d/%d)",
                                    model, attempt, MAX_RETRIES)
                        response = self._send(open_router, model)
                        answer = self._validate(response, model)
                        logger.info("Usable answer received from '%s'", model)
                        self.answering_model = model
                        return answer
                    except QAAssistantError:
                        # Unusable response -> fail immediately (no retry/reroute).
                        raise
                    except (errors.OpenRouterError, errors.NoResponseError) as e:
                        last_error = e
                        action = _classify(e)
                        logger.warning(
                            "model=%s attempt=%d/%d error=%s -> %s",
                            model, attempt, MAX_RETRIES, type(e).__name__, action.name,
                        )

                        if action is _ErrorAction.FAIL:
                            raise QAAssistantError(
                                f"Unrecoverable error from '{model}': "
                                f"{type(e).__name__}: {e}"
                            ) from e

                        if action is _ErrorAction.RETRY and attempt < MAX_RETRIES:
                            time.sleep(min(2 ** (attempt - 1), 8))  # backoff
                            continue

                        # Retries exhausted, or a reroute error: try next model.
                        break

        raise QAAssistantError(
            "All models failed to produce a usable answer. Last error: "
            f"{type(last_error).__name__}: {last_error}"
        )

    def _send(self, open_router: OpenRouter, model: str):
        return open_router.chat.send(
            model=model,
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": self.user_prompt},
            ],
        )

    @staticmethod
    def _validate(response, model: str) -> str:
        """Return the answer text, or raise QAAssistantError if unusable."""
        choices = getattr(response, "choices", None)
        if not choices:
            raise QAAssistantError(f"'{model}' returned no choices.")

        choice = choices[0]

        # The model stopped for a reason that yields no trustworthy content.
        finish_reason = getattr(choice, "finish_reason", None)
        if finish_reason in ("content_filter", "error"):
            raise QAAssistantError(
                f"'{model}' returned an unusable response "
                f"(finish_reason={finish_reason})."
            )

        message = getattr(choice, "message", None)
        if message is None:
            raise QAAssistantError(f"'{model}' returned a choice with no message.")

        refusal = getattr(message, "refusal", None)
        if refusal:
            raise QAAssistantError(f"'{model}' refused to answer: {refusal}")

        content = getattr(message, "content", None)
        if content is None or (isinstance(content, str) and not content.strip()):
            raise QAAssistantError(f"'{model}' returned empty content.")

        return content
