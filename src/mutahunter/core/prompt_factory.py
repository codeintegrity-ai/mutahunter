"""
Module for generating prompts based on the programming language.
"""

from importlib import resources

from jinja2 import Environment, FileSystemLoader


class MutationTestingPromptFactory:
    """Factory class to generate prompts based on the programming language."""

    @staticmethod
    def get_prompt():
        return MutationTestingPrompt()


class MutationTestingPrompt:
    """Base prompt class with system and user prompts."""

    def __init__(self):
        env = Environment(
            loader=FileSystemLoader(
                resources.files(__package__).joinpath(
                    "templates",
                )
            )
        )
        self.mutator_system_prompt = env.get_template(
            "mutant_generation/mutator_system.txt"
        )
        self.mutator_user_prompt = env.get_template(
            "mutant_generation/mutator_user.txt"
        )


class YAMLFixerPromptFactory:
    @staticmethod
    def get_prompt():
        return YAMLFixerPrompt()


class YAMLFixerPrompt:
    def __init__(self):
        env = Environment(
            loader=FileSystemLoader(
                resources.files(__package__).joinpath(
                    "templates",
                )
            )
        )
        self.yaml_fixer_user_prompt = env.get_template("utils/yaml_fixer_user.txt")
