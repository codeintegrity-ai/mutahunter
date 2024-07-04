"""
Module for generating prompts based on the programming language.
"""

from mutahunter.core.pilot.prompts.examples import (GO_UDIFF, JAVA_UDIFF,
                                                    JAVASCRIPT_UDIFF,
                                                    PYTHON_UDIFF)
from mutahunter.core.pilot.prompts.system import SYSTEM_PROMPT
from mutahunter.core.pilot.prompts.user import USER_PROMPT


class PromptFactory:
    """Factory class to generate prompts based on the programming language."""

    @staticmethod
    def get_prompt(language: str):
        """Get the appropriate prompt class based on the language.

        Args:
            language (str): The programming language.

        Returns:
            BasePrompt: The corresponding prompt class.
        """
        if language == "python":
            return PythonPrompt()
        if language == "javascript":
            return JavaScriptPrompt()
        if language == "go":
            return GoPrompt()
        if language == "java":
            return JavaPrompt()
        return BasePrompt()


class BasePrompt:
    """Base prompt class with system and user prompts."""

    def __init__(self):
        self.system_prompt = SYSTEM_PROMPT
        self.user_prompt = USER_PROMPT
        self.example_output = ""

    def get_system_prompt(self):
        """Get the system prompt."""
        return self.system_prompt

    def get_user_prompt(self):
        """Get the user prompt."""
        return self.user_prompt

    def get_example_output(self):
        """Get the example output."""
        return self.example_output


class PythonPrompt(BasePrompt):
    """Python-specific prompt class."""

    def __init__(self):
        super().__init__()
        self.example_output = PYTHON_UDIFF


class JavaScriptPrompt(BasePrompt):
    """JavaScript-specific prompt class."""

    def __init__(self):
        super().__init__()
        self.example_output = JAVASCRIPT_UDIFF


class GoPrompt(BasePrompt):
    """Go-specific prompt class."""

    def __init__(self):
        super().__init__()
        self.example_output = GO_UDIFF


class JavaPrompt(BasePrompt):
    """Java-specific prompt class."""

    def __init__(self):
        super().__init__()
        self.example_output = JAVA_UDIFF
