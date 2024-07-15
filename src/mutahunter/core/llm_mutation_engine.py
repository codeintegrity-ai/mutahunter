import json

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
            example_output=self.prompt.example_output,
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
        # print("model_response", model_response)
        return model_response

    def generate(self):
        repo_map_result = self.repo_map.get_repo_map(
            chat_files=[],
            other_files=self.cov_files,
        )
        if not repo_map_result:
            logger.error("No repository map found.")

        ai_reply = self.generate_mutant(repo_map_result)
        mutation_info = self.extract_json_from_reply(ai_reply)
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

    def extract_json_from_reply(self, ai_reply: str) -> dict:
        retries = 2
        for attempt in range(retries):
            try:
                if "```json" in ai_reply:
                    json_content = ai_reply.split("```json")[1].split("```")[0]
                else:
                    json_content = ai_reply.strip()

                mutation_info = json.loads(json_content)
                return mutation_info
            except (IndexError, json.JSONDecodeError) as e:
                logger.error(f"Error extracting JSON content: {e}")
                if attempt < retries - 1:
                    logger.info(f"Retrying to extract JSON with retry {attempt + 1}...")
                    json_content = self.fix_json_format(e, ai_reply)
                    ai_reply = json_content
                else:
                    logger.error(
                        f"Error extracting JSON content after {retries} attempts: {e}"
                    )
                    return {"changes": []}

    def fix_json_format(self, error, json_content):
        system_template = Template(SYSTEM_JSON_FIX).render()
        user_template = Template(USER_JSON_FIX).render(
            json_content=json_content,
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


SYSTEM_JSON_FIX = """
Based on the error message, the JSON content provided is not in the correct format. Please ensure the JSON content is in the correct format and try again.
"""
USER_JSON_FIX = """
JSON content:
{{json_content}}

Error:
{{error}}

Output must be wrapped in triple backticks and in JSON format:
```json
...fix the json content here...
"""
