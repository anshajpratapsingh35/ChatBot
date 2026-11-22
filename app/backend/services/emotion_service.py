import re
from typing import Dict, Any, Tuple

# Linguistic cues for real-time emotional state classification
EMOTION_PATTERNS = {
    "sadness": [
        r"\b(sad|depressed|heartbroken|crying|unhappy|down|miserable|grief|hurting|hopeless)\b"
    ],
    "anxiety": [
        r"\b(anxious|nervous|worried|panicking|stress|stressed|overwhelmed|scared|dread)\b"
    ],
    "anger": [
        r"\b(angry|furious|mad|irritated|annoyed|frustrated|pissed|betrayed|unfair)\b"
    ],
    "loneliness": [
        r"\b(lonely|alone|isolated|nobody cares|no friends|abandoned|left out)\b"
    ],
    "joy": [
        r"\b(happy|glad|excited|proud|thrilled|grateful|awesome|celebrate|blessed|joyful)\b"
    ],
}

EMPATHY_PROMPTS = {
    "sadness": "Acknowledge the user's sorrow with deep warmth. Avoid toxic positivity or rushing them to 'cheer up'. Offer a listening ear and gentle validation.",
    "anxiety": "Offer a calming, grounding presence. Validate that feelings of overwhelm are natural, and encourage taking things one step at a time.",
    "anger": "Validate that their frustration makes sense without judging them. Offer an objective, non-reactive space to vent.",
    "loneliness": "Express unconditional presence. Remind them gently that they matter and that you are here right now to keep them company and listen.",
    "joy": "Celebrate their success with genuine enthusiasm and positive reinforcement. Share in their happiness!",
    "neutral": "Maintain a warm, polite, and attentive conversational tone."
}

class EmotionService:
    """Analyzes user message sentiment and produces empathetic response adaptations."""

    @staticmethod
    def detect_emotion(text: str) -> str:
        """Classifies the primary emotional tone from user text."""
        if not text:
            return "neutral"
            
        lower_text = text.lower()
        for emotion, patterns in EMOTION_PATTERNS.items():
            for pat in patterns:
                if re.search(pat, lower_text):
                    return emotion
        return "neutral"

    @staticmethod
    def get_empathy_guidance(emotion: str) -> str:
        """Returns targeted conversational instructions for the LLM based on detected emotion."""
        return EMPATHY_PROMPTS.get(emotion, EMPATHY_PROMPTS["neutral"])

emotion_service = EmotionService()
