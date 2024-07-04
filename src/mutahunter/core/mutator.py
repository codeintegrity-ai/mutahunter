from grep_ast import filename_to_lang
from jinja2 import Template

from mutahunter.core.logger import logger
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
        source_file_path,  # file_path for the source code
        start_byte,
        end_byte,
    ):
        self.config = config
        self.executed_lines = executed_lines
        self.cov_files = cov_files
        self.source_file_path = source_file_path
        self.start_byte = start_byte
        self.end_byte = end_byte

        self.router = LLMRouter(
            model=self.config["model"], api_base=self.config["api_base"]
        )
        self.repo_map = RepoMap(model=self.config["model"])
        self.udiff_coder = UnifiedDiffCoder()
        self.language = filename_to_lang(self.source_file_path)
        self.prompt = PromptFactory.get_prompt(language=self.language)

        self.function_block_source_code = self.get_function_block_source_code()

    def get_function_block_source_code(self):
        with open(self.source_file_path, "rb") as f:
            src_code = f.read()
        return src_code[self.start_byte : self.end_byte].decode("utf-8")

    def generate_mutant(self, repo_map_result):
        system_template = Template(self.prompt.system_prompt).render()
        user_template = Template(self.prompt.user_prompt).render(
            language=self.language,
            covered_lines=self.executed_lines,
            ast=repo_map_result,
            filename=self.source_file_path,
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
        if not repo_map_result:
            logger.error("No repository map found.")
        ai_reply = self.generate_mutant(
            repo_map_result=repo_map_result,
        )
        edits = self.udiff_coder.get_edits(ai_reply)

        success_edits, failed_edits = self.udiff_coder.apply_edits(
            edits=edits, original_code=self.function_block_source_code
        )
        if not success_edits:
            logger.error(
                f"Failed to apply unified diff for generated mutant {self.source_file_path}"
            )
        return success_edits
