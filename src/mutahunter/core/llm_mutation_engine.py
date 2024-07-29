import os
from typing import Any, Dict, List, Optional

import yaml
from grep_ast import filename_to_lang
from jinja2 import Template

from mutahunter.core.logger import logger
from mutahunter.core.prompts.factory import PromptFactory
from mutahunter.core.repomap import RepoMap

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


class LLMMutationEngine:
    MAX_RETRIES = 2

    def __init__(
        self,
        model,
        router,
    ):
        self.model = model
        self.router = router
        self.repo_map = RepoMap(model=self.model)
        self.prompt = PromptFactory.get_prompt()
        os.makedirs("logs/_latest/llm", exist_ok=True)

        self.num = 0

    def get_source_code(self, source_file_path: str) -> str:
        with open(source_file_path, "r") as f:
            return f.read()

    def _add_line_numbers(self, src_code: str) -> str:
        return "\n".join(
            [f"{i + 1} {line}" for i, line in enumerate(src_code.splitlines())]
        )

    def generate_mutant(
        self,
        repo_map_result: Dict[str, Any],
        source_file_path: str,
        executed_lines: List[int],
    ) -> str:
        language = filename_to_lang(source_file_path)
        src_code = self.get_source_code(source_file_path)
        src_code_with_line_num = self._add_line_numbers(src_code)

        system_template = Template(self.prompt.system_prompt).render(language=language)
        user_template = Template(self.prompt.user_prompt).render(
            language=language,
            ast=repo_map_result,
            covered_lines=executed_lines,
            src_code_with_line_num=src_code_with_line_num,
            maximum_num_of_mutants_per_function_block=2,
        )
        prompt = {"system": system_template, "user": user_template}
        model_response, _, _ = self.router.generate_response(
            prompt=prompt, streaming=True
        )
        #         model_response = """
        # ```yaml
        # source_file: src/main/java/com/example/Calculator.java
        # mutants:
        #   - function_name: add
        #     type: Modify Core Logic
        #     description: Changed the addition operation to a subtraction operation, introducing incorrect logic.
        #     line_number: 7
        #     original_code: |
        #       return a + b;
        #     mutated_code: |
        #       return a - b; // Mutated to subtract instead of add
        # ```
        #         """
        return model_response

    def generate(
        self, source_file_path: str, executed_lines: List[int], cov_files: List[str]
    ) -> Dict[str, Any]:
        repo_map_result = self._get_repo_map(cov_files=cov_files)
        if not repo_map_result:
            logger.error("No repository map found.")
            return {"mutants": []}

        response = self.generate_mutant(
            repo_map_result, source_file_path, executed_lines
        )
        extracted_response = self.extract_response(response)
        self._save_yaml(extracted_response)
        return extracted_response

    def extract_response(self, response: str) -> Dict[str, Any]:
        for attempt in range(self.MAX_RETRIES):
            try:
                cleaned_response = self._clean_response(response)
                data = yaml.safe_load(cleaned_response)
                return data
            except Exception as e:
                logger.error(f"Error extracting YAML content: {e}")
                if attempt < self.MAX_RETRIES - 1:
                    logger.info(f"Retrying to extract YAML with retry {attempt + 1}...")
                    response = self.fix_format(e, response)
                else:
                    logger.error(
                        f"Error extracting YAML content after {self.MAX_RETRIES} attempts: {e}"
                    )
        return {"mutants": []}

    def fix_format(self, error: Exception, content: str) -> str:
        system_template = Template(SYSTEM_YAML_FIX).render()
        user_template = Template(USER_YAML_FIX).render(
            yaml_content=content, error=error
        )
        prompt = {"system": system_template, "user": user_template}
        model_response, _, _ = self.router.generate_response(
            prompt=prompt, streaming=True
        )
        return model_response

    def _get_repo_map(self, cov_files) -> Optional[Dict[str, Any]]:
        return self.repo_map.get_repo_map(chat_files=[], other_files=cov_files)

    def _add_line_numbers(self, src_code: str) -> str:
        return "\n".join(
            [f"{i + 1} {line}" for i, line in enumerate(src_code.splitlines())]
        )

    def _clean_response(self, response: str) -> str:
        return response.strip().removeprefix("```yaml").rstrip("`")

    def _save_yaml(self, data: Dict[str, Any]) -> None:
        output = f"output_{self.num}.yaml"
        with open(os.path.join("logs/_latest/llm", output), "w") as f:
            yaml.dump(data, f, default_flow_style=False, indent=2)
        self.num += 1
        logger.info(f"YAML output saved to {output}")
