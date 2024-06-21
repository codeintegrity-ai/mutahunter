from mutahunter.core.pilot.prompts.go import SYSTEM_PROMPT as GO_SYSTEM_PROMPT
from mutahunter.core.pilot.prompts.go import USER_PROMPT as GO_USER_PROMPT
from mutahunter.core.pilot.prompts.javascript import \
    SYSTEM_PROMPT as JAVASCRIPT_SYSTEM_PROMPT
from mutahunter.core.pilot.prompts.javascript import \
    USER_PROMPT as JAVASCRIPT_USER_PROMPT
from mutahunter.core.pilot.prompts.python import \
    SYSTEM_PROMPT as PYTHON_SYSTEM_PROMPT
from mutahunter.core.pilot.prompts.python import \
    USER_PROMPT as PYTHON_USER_PROMPT


class PromptFactory:
    @staticmethod
    def get_prompt(language: str):
        if language == "python":
            return PythonPrompt()
        elif language == "javascript":
            return JavaScriptPrompt()
        elif language == "go":
            return GoPrompt()
        else:
            raise NotImplementedError(f"Prompt for {language} is not implemented yet.")


class PythonPrompt:
    def __init__(self):
        self.system_prompt = PYTHON_SYSTEM_PROMPT
        self.user_prompt = PYTHON_USER_PROMPT


class JavaScriptPrompt:
    def __init__(self):
        self.system_prompt = JAVASCRIPT_SYSTEM_PROMPT
        self.user_prompt = JAVASCRIPT_USER_PROMPT


class GoPrompt:
    def __init__(self):
        self.system_prompt = GO_SYSTEM_PROMPT
        self.user_prompt = GO_USER_PROMPT
