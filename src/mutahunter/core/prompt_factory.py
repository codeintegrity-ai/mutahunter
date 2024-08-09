"""
Module for generating prompts based on the programming language.
"""

from jinja2 import Environment, FileSystemLoader
from importlib import resources


class TestGenerationPromptFactory:
    @staticmethod
    def get_prompt():
        return TestGenerationPrompt()


class TestGenerationPrompt:
    def __init__(self):
        env = Environment(
            loader=FileSystemLoader(
                resources.files(__package__).joinpath(
                    "templates",
                )
            )
        )
        self.analyzer_system_prompt = env.get_template(
            "test_generation/analyzer_system.txt"
        )
        self.analyzer_user_prompt = env.get_template(
            "test_generation/analyzer_user.txt"
        )
        self.test_generator_system_prompt = env.get_template(
            "test_generation/test_generator_system.txt"
        )
        self.test_generator_user_prompt = env.get_template(
            "test_generation/test_generator_user.txt"
        )
        self.yaml_fixer_user_prompt = env.get_template(
            "test_generation/yaml_fixer_user.txt"
        )


class TestGenerationWithMutationPromptFactory:
    @staticmethod
    def get_prompt():
        return TestGenerationWithMutationPrompt()


class TestGenerationWithMutationPrompt:
    def __init__(self):
        env = Environment(
            loader=FileSystemLoader(
                resources.files(__package__).joinpath(
                    "templates",
                )
            )
        )
        self.analyzer_system_prompt = env.get_template(
            "test_generation/analyzer_system.txt"
        )
        self.analyzer_user_prompt = env.get_template(
            "test_generation/analyzer_user.txt"
        )
        self.test_generator_system_prompt = env.get_template(
            "test_generation_with_mutation_system.txt"
        )
        self.test_generator_user_prompt = env.get_template(
            "test_generation_with_mutation_user.txt"
        )


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
        self.analyzer_system_prompt = env.get_template(
            "mutant_generation/analyzer_system.txt"
        )
        self.analyzer_user_prompt = env.get_template(
            "mutant_generation/analyzer_user.txt"
        )
        self.mutator_system_prompt = env.get_template(
            "mutant_generation/mutator_system.txt"
        )
        self.mutator_user_prompt = env.get_template(
            "mutant_generation/mutator_user.txt"
        )