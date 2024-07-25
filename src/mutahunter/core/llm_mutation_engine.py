import yaml
from grep_ast import filename_to_lang
from jinja2 import Template

from mutahunter.core.logger import logger
from mutahunter.core.prompts.factory import PromptFactory
from mutahunter.core.repomap import RepoMap


class LLMMutationEngine:
    def __init__(
        self,
        model,
        executed_lines,
        cov_files,
        source_file_path,  # file_path for the source code
        router,
    ):
        self.model = model
        self.executed_lines = executed_lines
        self.cov_files = cov_files
        self.source_file_path = source_file_path
        self.router = router
        self.repo_map = RepoMap(model=self.model)
        self.language = filename_to_lang(self.source_file_path)
        self.prompt = PromptFactory.get_prompt(language=self.language)

        self.function_block_source_code = self.get_function_block_source_code()

    def get_function_block_source_code(self):
        with open(self.source_file_path, "r") as f:
            src_code = f.read()
        return src_code

    def generate_mutant(self, repo_map_result):
        # add line number for each line of code
        function_block_with_line_num = "\n".join(
            [
                f"{i + 1} {line}"
                for i, line in enumerate(self.function_block_source_code.splitlines())
            ]
        )
        system_template = Template(self.prompt.system_prompt).render(
            language=self.language
        )
        user_template = Template(self.prompt.user_prompt).render(
            language=self.language,
            ast=repo_map_result,
            covered_lines=self.executed_lines,
            function_block=function_block_with_line_num,
            maximum_num_of_mutants_per_function_block=2,
        )
        prompt = {
            "system": system_template,
            "user": user_template,
        }

        with open("system_template.txt", "w") as f:
            f.write(system_template)
        with open("user_template.txt", "w") as f:
            f.write(user_template)
        # print("system_template:", system_template)
        # print("user_template:", user_template)

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

        response = self.generate_mutant(repo_map_result)
        response = self.extract_response(response)
        return response

    def extract_response(self, response: str) -> dict:
        retries = 2
        for attempt in range(retries):
            try:
                response = response.strip().removeprefix("```yaml").rstrip("`")
                data = yaml.safe_load(response)
                return data
            except Exception as e:
                logger.error(f"Error extracting YAML content: {e}")
                if attempt < retries - 1:
                    logger.info(f"Retrying to extract YAML with retry {attempt + 1}...")
                    response = self.fix_format(e, response)
                else:
                    logger.error(
                        f"Error extracting YAML content after {retries} attempts: {e}"
                    )
                    return {"changes": []}

    def fix_format(self, error, content):
        system_template = Template(SYSTEM_YAML_FIX).render()
        user_template = Template(USER_YAML_FIX).render(
            yaml_content=content,
            error=error,
        )
        prompt = {
            "system": system_template,
            "user": user_template,
        }
        model_response, _, _ = self.router.generate_response(
            prompt=prompt, streaming=True
        )
        return model_response


SYSTEM_YAML_FIX = """
Based on the error message, the YAML content provided is not in the correct format. Please ensure the YAML content is in the correct format and try again.
"""

USER_YAML_FIX = """
YAML content:
```yaml
{{yaml_content}}
```

Error:
{{error}}

Output must be wrapped in triple backticks and in YAML format:
```yaml
...fix the yaml content here...
```
"""
