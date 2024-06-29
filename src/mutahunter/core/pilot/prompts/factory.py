from mutahunter.core.pilot.prompts.examples import (
    GO_UDIFF,
    JAVASCRIPT_UDIFF,
    PYTHON_UDIFF,
    JAVA_UDIFF,
)
from mutahunter.core.pilot.prompts.system import SYSTEM_PROMPT
from mutahunter.core.pilot.prompts.user import USER_PROMPT


class PromptFactory:
    @staticmethod
    def get_prompt(language: str):
        if language == "python":
            return PythonPrompt()
        elif language == "javascript":
            return JavaScriptPrompt()
        elif language == "go":
            return GoPrompt()
        elif language == "java":
            return JavaPrompt()
        else:
            return BasePrompt()


class BasePrompt:
    def __init__(self):
        self.system_prompt = SYSTEM_PROMPT
        self.user_prompt = USER_PROMPT
        self.example_output = ""


class PythonPrompt:
    def __init__(self):
        self.system_prompt = SYSTEM_PROMPT
        self.user_prompt = USER_PROMPT
        self.example_output = PYTHON_UDIFF


class JavaScriptPrompt:
    def __init__(self):
        self.system_prompt = SYSTEM_PROMPT
        self.user_prompt = USER_PROMPT
        self.example_output = JAVASCRIPT_UDIFF


class GoPrompt:
    def __init__(self):
        self.system_prompt = SYSTEM_PROMPT
        self.user_prompt = USER_PROMPT
        self.example_output = GO_UDIFF


class JavaPrompt:
    def __init__(self):
        self.system_prompt = SYSTEM_PROMPT
        self.user_prompt = USER_PROMPT
        self.example_output = JAVA_UDIFF
