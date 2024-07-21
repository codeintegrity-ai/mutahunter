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
        start_byte,
        end_byte,
        router,
    ):
        self.model = model
        self.executed_lines = executed_lines
        self.cov_files = cov_files
        self.source_file_path = source_file_path
        self.start_byte = start_byte
        self.end_byte = end_byte
        self.router = router
        self.repo_map = RepoMap(model=self.model)
        self.language = filename_to_lang(self.source_file_path)
        self.prompt = PromptFactory.get_prompt(language=self.language)

        self.function_block_source_code = self.get_function_block_source_code()

    def get_function_block_source_code(self):
        with open(self.source_file_path, "rb") as f:
            src_code = f.read()
        return src_code[self.start_byte : self.end_byte].decode("utf-8")

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
        mutation_info = self.extract_response(response)
        changes = mutation_info["changes"]
        original_lines = self.function_block_source_code.splitlines(keepends=True)
        for change in changes:
            original_line = change["original_line"]
            mutated_line = change["mutated_line"]

            for i, line in enumerate(original_lines):
                # print("line: ---->", line.lstrip().rstrip())
                # print("original_line: ---->", original_line.lstrip().rstrip())
                # print(
                #     "check: ---->",
                #     line.lstrip().rstrip() == original_line.lstrip().rstrip(),
                # )
                # print("\n")
                if line.lstrip().rstrip() == original_line.lstrip().rstrip():
                    # print("FOUND SAME LINE")
                    # print("original_lines[i]: ---->", original_lines[i])
                    # print("line: ---->", line)
                    # print("mutated_line: ---->", mutated_line)
                    # original_lines[i] = mutated_line + "\n"
                    # dont modify the original lines
                    temp_lines = original_lines.copy()
                    # check if the temp_lines[i] ends with a newline character
                    # get indentation of the original line
                    indentation_space = len(temp_lines[i]) - len(temp_lines[i].lstrip())
                    # add the indentation to the mutated line after lstripping
                    mutated_line = " " * indentation_space + mutated_line.lstrip()
                    temp_lines[i] = mutated_line + "\n"
                    # updated change dict
                    change["mutant_code"] = "".join(temp_lines)
                    break
            else:
                logger.error(f"Could not apply mutation. Skipping mutation.")
                continue
        return changes

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
