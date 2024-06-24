import re

from jinja2 import Template

from mutahunter.core.pilot.aider.repomap import RepoMap
from mutahunter.core.pilot.prompts.factory import PromptFactory
from mutahunter.core.router import LLMRouter


class MutantGenerator:
    def __init__(
        self,
        config,
        cov_files,
        test_file_path,
        filename,
        function_block_source_code,
        language,
    ):
        self.cov_files = cov_files
        self.test_file_path = test_file_path

        self.filename = filename
        self.function_block_source_code = function_block_source_code

        self.router = LLMRouter(model=config["model"], api_base=config["api_base"])
        self.language = language

        self.repo_map = RepoMap(model=config["model"])
        self.prompt = PromptFactory.get_prompt(language=language)

    def generate_mutant(self, repo_map_result):
        system_template = Template(self.prompt.system_prompt).render()
        user_template = Template(self.prompt.user_prompt).render(
            ast=repo_map_result,
            filename=self.filename,
            function_block=self.function_block_source_code,
        )
        prompt = {
            "system": system_template,
            "user": user_template,
        }
        model_response, _, _ = self.router.generate_response(prompt)
        return model_response

    def generate(self):
        repo_map_result = self.repo_map.get_repo_map(
            chat_files=[],
            other_files=self.cov_files + [self.test_file_path],
        )
        ai_reply = self.generate_mutant(
            repo_map_result=repo_map_result,
        )
        details = extract_mutation_details(ai_reply)
        return details


def extract_mutation_details(text):
    # Define regex patterns for each section
    patterns = {
        "code_snippet": r"```.*?\n(.*?)\n```",
    }

    # Extract each section using regex
    details = {}
    for key, pattern in patterns.items():
        match = re.search(pattern, text, re.DOTALL)
        if match:
            details[key] = match.group(1).strip()
        else:
            details[key] = ""

    return details
