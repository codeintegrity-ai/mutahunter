import os
from typing import Any, Dict, List, Optional

import yaml
from mutahunter.core.parsers import filename_to_lang
from jinja2 import Template

from mutahunter.core.logger import logger
from mutahunter.core.prompt_factory import MutationTestingPrompt
from mutahunter.core.router import LLMRouter

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
        model: str,
        router: LLMRouter,
        prompt: MutationTestingPrompt,
    ) -> None:
        self.model = model
        self.router = router
        self.prompt = prompt
        self.num = 0

    def get_source_code(self, source_file_path: str) -> str:
        with open(source_file_path, "r") as f:
            return f.read()

    def add_line_numbers(self, src_code: str) -> str:
        lines = src_code.split("\n")
        numbered_lines = [f"{i+1}: {line}" for i, line in enumerate(lines)]
        return "\n".join(numbered_lines)

    def generate_mutant(
        self,
        source_file_path: str,
    ) -> str:
        language = filename_to_lang(source_file_path)
        src_code = self.get_source_code(source_file_path)

        numbered_src_code = self.add_line_numbers(src_code)

        system_template = self.prompt.mutator_system_prompt.render(
            {
                "language": language,
            }
        )
        user_template = self.prompt.mutator_user_prompt.render(
            {
                "language": language,
                "numbered_src_code": numbered_src_code,
                "maximum_num_of_mutants_per_function_block": 2,
            }
        )
        prompt = {"system": system_template, "user": user_template}
        model_response, _, _ = self.router.generate_response(
            prompt=prompt, streaming=True
        )
        return model_response

    def generate(self, source_file_path: str) -> Dict[str, Any]:
        response = self.generate_mutant(source_file_path)
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


    def _clean_response(self, response: str) -> str:
        return response.strip().removeprefix("```yaml").rstrip("`")

    def _save_yaml(self, data: Dict[str, Any]) -> None:
        output = f"output_{self.num}.yaml"
        with open(os.path.join("logs/_latest/llm", output), "w") as f:
            yaml.dump(data, f, default_flow_style=False, indent=2)
        self.num += 1
        logger.info(f"YAML output saved to {output}")
