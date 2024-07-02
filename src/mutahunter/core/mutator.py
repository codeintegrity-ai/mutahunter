from jinja2 import Template

from mutahunter.core.pilot.aider.repomap import RepoMap
from mutahunter.core.pilot.aider.udiff_coder import UnifiedDiffCoder
from mutahunter.core.pilot.prompts.factory import PromptFactory
from mutahunter.core.router import LLMRouter


class MutantGenerator:
    def __init__(
        self,
        config,
        executed_lines,
        cov_files,
        test_file_path,
        filename,
        function_block_source_code,
        language,
    ):

        self.cov_files = cov_files
        self.executed_lines = executed_lines
        self.test_file_path = test_file_path

        self.filename = filename
        self.function_block_source_code = function_block_source_code

        self.router = LLMRouter(model=config["model"], api_base=config["api_base"])
        self.language = language

        self.repo_map = RepoMap(model=config["model"])
        self.udiff_coder = UnifiedDiffCoder()
        self.prompt = PromptFactory.get_prompt(language=language)

    def generate_mutant(self, repo_map_result):
        with open(self.test_file_path, "r") as f:
            test_file_content = f.read()
        system_template = Template(self.prompt.system_prompt).render()
        user_template = Template(self.prompt.user_prompt).render(
            language=self.language,
            covered_lines=self.executed_lines,
            test_file_path=self.test_file_path,
            test_file_content=test_file_content,
            ast=repo_map_result,
            filename=self.filename,
            example_output=self.prompt.example_output,
            function_block=self.function_block_source_code,
        )
        prompt = {
            "system": system_template,
            "user": user_template,
        }
        model_response, _, _ = self.router.generate_response(
            prompt=prompt, streaming=True
        )
        return model_response

    def generate(self):
        repo_map_result = self.repo_map.get_repo_map(
            chat_files=[],
            other_files=self.cov_files,
        )
        ai_reply = self.generate_mutant(
            repo_map_result=repo_map_result,
        )
        edits = self.udiff_coder.get_edits(ai_reply)

        success_edits, failed_edits = self.udiff_coder.apply_edits(
            edits=edits, original_code=self.function_block_source_code
        )
        # path, hunk, content)
        return success_edits
