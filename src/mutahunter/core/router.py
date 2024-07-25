import time

from litellm import completion, litellm


class LLMRouter:
    def __init__(self, model: str, api_base: str = ""):
        """
        Initialize the LLMRouter with a model and optional API base URL.
        """
        self.model = model
        self.api_base = api_base
        self.total_cost = 0
        litellm.success_callback = [self.track_cost_callback]

    def track_cost_callback(
        self,
        kwargs,  # kwargs to completion
        completion_response,  # response from completion
        start_time,
        end_time,  # start/end time
    ):
        try:
            response_cost = kwargs.get("response_cost", 0)
            self.total_cost += response_cost
        except:
            pass

    def generate_response(
        self, prompt: dict, max_tokens: int = 4096, streaming: bool = False
    ) -> tuple:
        """
        Call the LLM model with the provided prompt and return the generated response.

        Args:
            prompt (dict): A dictionary containing 'system' and 'user' keys.
            max_tokens (int): Maximum number of tokens for the response.
            streaming (bool): Flag to enable or disable streaming response.

        Returns:
            tuple: Generated response, prompt tokens used, and completion tokens used.
        """
        self._validate_prompt(prompt)
        messages = self._build_messages(prompt)
        completion_params = self._build_completion_params(
            messages, max_tokens, streaming
        )

        try:
            if streaming:
                response_chunks = self._stream_response(completion_params)
                return self._process_response(response_chunks, messages)
            else:
                return self._non_stream_response(completion_params)
        except Exception as e:
            print(f"Error during response generation: {e}")
            return "", 0, 0

    def _validate_prompt(self, prompt: dict):
        """
        Validate that the prompt contains the required keys.
        """
        if "system" not in prompt or "user" not in prompt:
            raise Exception(
                "The prompt dictionary must contain 'system' and 'user' keys."
            )

    def _build_messages(self, prompt: dict) -> list:
        """
        Build the messages list from the prompt.
        """
        return [
            {"role": "system", "content": prompt["system"]},
            {"role": "user", "content": prompt["user"]},
        ]

    def _build_completion_params(
        self, messages: list, max_tokens: int, streaming: bool
    ) -> dict:
        """
        Build the parameters for the LLM completion call.
        """
        completion_params = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens,
            "stream": streaming,
            "temperature": 0.0,
        }
        if (
            "ollama" in self.model
            or "huggingface" in self.model
            or self.model.startswith("openai/")
        ):
            completion_params["api_base"] = self.api_base
        return completion_params

    def _stream_response(self, completion_params: dict) -> list:
        """
        Stream the response from the LLM model.
        """
        response_chunks = []
        print("\nStreaming results from LLM model...")
        response = completion(**completion_params)
        for chunk in response:
            print(chunk.choices[0].delta.content or "", end="", flush=True)
            response_chunks.append(chunk)
            time.sleep(
                0.01
            )  # Optional: Delay to simulate more 'natural' response pacing
        print("\n")
        return response_chunks

    def _non_stream_response(self, completion_params: dict) -> tuple:
        """
        Get the non-streamed response from the LLM model.
        """
        response = completion(**completion_params)
        content = response["choices"][0]["message"]["content"]
        prompt_tokens = int(response["usage"]["prompt_tokens"])
        completion_tokens = int(response["usage"]["completion_tokens"])
        return content, prompt_tokens, completion_tokens

    def _process_response(self, response_chunks: list, messages: list) -> tuple:
        """
        Process the streamed response chunks into a final response.
        """
        model_response = litellm.stream_chunk_builder(
            response_chunks, messages=messages
        )
        content = model_response["choices"][0]["message"]["content"]
        prompt_tokens = int(model_response["usage"]["prompt_tokens"])
        completion_tokens = int(model_response["usage"]["completion_tokens"])
        return content, prompt_tokens, completion_tokens
