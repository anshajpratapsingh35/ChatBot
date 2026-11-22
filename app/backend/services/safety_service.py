from typing import Tuple, Optional
from app.backend.core.guardrails import SafetyGuardrails
from app.backend.core.security import SecurityValidator
from app.backend.utils.logger import logger

class SafetyService:
    """Consolidated safety, crisis detection, and security screening service."""

    @staticmethod
    def inspect_input(text: str) -> Tuple[bool, Optional[str], bool]:
        """
        Screen user input for crisis triggers and prompt injection.
        Returns: (is_safe, intervention_message, is_crisis)
        """
        # 1. Check for crisis / self-harm triggers
        is_crisis, crisis_msg = SafetyGuardrails.check_crisis(text)
        if is_crisis:
            logger.warning("Crisis intervention triggered by SafetyService.")
            return False, crisis_msg, True

        # 2. Check for malicious prompt injection attempts
        is_injection, injection_msg = SafetyGuardrails.check_prompt_injection(text)
        if is_injection:
            logger.warning(f"Prompt injection detected: {text[:60]}")
            return False, injection_msg, False

        return True, None, False

    @staticmethod
    def sanitize(text: str) -> str:
        return SafetyGuardrails.sanitize_user_input(text)

safety_service = SafetyService()
