"""
Module for generating prompts based on the programming language.
"""

from mutahunter.core.prompts.mutant_generator import SYSTEM_PROMPT, USER_PROMPT


class PromptFactory:
    """Factory class to generate prompts based on the programming language."""

    @staticmethod
    def get_prompt(language: str):
        return BasePrompt()


class BasePrompt:
    """Base prompt class with system and user prompts."""

    def __init__(self):
        self.system_prompt = SYSTEM_PROMPT
        self.user_prompt = USER_PROMPT

    def get_system_prompt(self):
        """Get the system prompt."""
        return self.system_prompt

    def get_user_prompt(self):
        """Get the user prompt."""
        return self.user_prompt
