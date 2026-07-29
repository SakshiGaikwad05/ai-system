from dataclasses import dataclass
from typing import Dict

import tiktoken


@dataclass
class TokenCall:
    agent: str
    input_tokens: int
    output_tokens: int
    estimated: bool = False


class TokenTracker:
    """Records token usage for every LLM call in the pipeline.

    Prefers actual usage returned by the model provider's API response.
    Falls back to local estimation with tiktoken only when needed.
    """

    def __init__(self) -> None:
        self.calls: list[TokenCall] = []

    def log(self, agent: str, input_tokens: int, output_tokens: int, estimated: bool = False) -> None:
        self.calls.append(TokenCall(agent, input_tokens, output_tokens, estimated))

    def total_input(self) -> int:
        return sum(c.input_tokens for c in self.calls)

    def total_output(self) -> int:
        return sum(c.output_tokens for c in self.calls)

    def total(self) -> int:
        return self.total_input() + self.total_output()

    def by_agent(self) -> Dict[str, Dict[str, int]]:
        result: Dict[str, Dict[str, int]] = {}
        for c in self.calls:
            if c.agent not in result:
                result[c.agent] = {"input_tokens": 0, "output_tokens": 0}
            result[c.agent]["input_tokens"] += c.input_tokens
            result[c.agent]["output_tokens"] += c.output_tokens
        return result

    def any_estimated(self) -> bool:
        return any(c.estimated for c in self.calls)

    def reset(self) -> None:
        self.calls.clear()

    @staticmethod
    def estimate_tokens(text: str, model: str = "gpt-4") -> int:
        """Estimate token count locally using tiktoken (cl100k_base).

        Used when real API usage is unavailable (e.g. in unit tests).
        """
        try:
            enc = tiktoken.get_encoding("cl100k_base")
            return len(enc.encode(text))
        except Exception:
            return len(text.split())


tracker = TokenTracker()
