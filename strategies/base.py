from typing import Dict, Any, Optional
import json
import os

class CollaborationStrategy:
    """Base class for collaboration strategies"""
    
    def __init__(self, name: str, config_path: Optional[str] = None):
        """
        Initialize a collaboration strategy
        
        Args:
            name: Name of the strategy
            config_path: Path to configuration file (optional)
        """
        self.name = name
        self.benchmark_name = None

        self.simple_bench_instructions = (
            "\n\nIMPORTANT: This is a multiple-choice question from the SimpleBench dataset. "
            "In EVERY response except the final turn, you must include a line with your current best answer using the format 'Answer: X' "
            "where X is a specific choice (A, B, C, D, E or F) DO NOT use placeholders "
            "like 'still thinking' or 'unclear' - make your best guess if uncertain. This intermediate "
            "answer must be included even when you're not fully confident. This helps track your reasoning progress. "
            "Your final answer MUST be in the format 'Final Answer: X' where X is exactly "
            "one of the provided options (A, B, C, D, E, or F)."
        )
        self.gpqa_instructions = (
            "\n\nIMPORTANT: This is a multiple-choice question from the Graduate-level Professional QA (GPQA) dataset. "
            "In EVERY response except the final turn, you must include a line with your current best answer using the format 'Answer: X' "
            "where X is a specific choice (A, B, C, D) DO NOT use placeholders "
            "like 'still thinking' or 'unclear' - make your best guess if uncertain. This intermediate "
            "answer must be included even when you're not fully confident. This helps track your reasoning progress. "
            "The question requires expertise in a specialized domain. "
            "Your final answer MUST be in the format 'Final Answer: X' where X is exactly "
            "one of the provided options (A, B, C, D). "
        )
        self.aime_instructions = (
            "\n\nIMPORTANT: This is a mathematics problem from the American Invitational Mathematics Examination (AIME). "
            "In EVERY response except the final turn, you must include a line with your current best answer using the format 'Answer: N' "
            "where N is a specific integer (0-999). DO NOT use placeholders "
            "like 'still thinking' or 'unclear' - make your best guess if uncertain. This intermediate "
            "answer must be included even when you're not fully confident. This helps track your reasoning progress. "
            "AIME problems always have integer answers between 0 and 999 inclusive. "
            "Your final answer MUST be in the format 'Final Answer: N' where N is your integer answer. "
        )
        
        # Load configuration from file if provided
        if config_path and os.path.exists(config_path):
            with open(config_path, 'r') as f:
                self.config = json.load(f)
        else:
            # Default configuration
            self.config = {
                "temperature": 0.7,
                "max_tokens": 1000,
                "num_turns": 5
            }
    
    def get_system_prompt_a(self):
        """Get system prompt for Agent A"""
        base_prompt = self._get_base_system_prompt_a()
        
        # Add benchmark-specific instructions if needed
        if self.benchmark_name == "SimpleBench":
            return {
                "role": "system",
                "content": base_prompt["content"] + self.simple_bench_instructions 
            }
        elif self.benchmark_name == "GPQA":
            return {
                "role": "system",
                "content": base_prompt["content"] + self.gpqa_instructions
            }
        elif self.benchmark_name == "AIME":
            return {
                "role": "system",
                "content": base_prompt["content"] + self.aime_instructions
            }
        
        return base_prompt
    
    def get_system_prompt_b(self) -> Dict[str, str]:
        """Get system prompt for Agent B"""
        base_prompt = self._get_base_system_prompt_b()
        
        # Add benchmark-specific instructions if needed
        if self.benchmark_name == "SimpleBench":
            return {
                "role": "system",
                "content": base_prompt["content"] + self.simple_bench_instructions
            }
        elif self.benchmark_name == "GPQA":
            return {
                "role": "system",
                "content": base_prompt["content"] + self.gpqa_instructions
            }
        elif self.benchmark_name == "AIME":
            return {
                "role": "system",
                "content": base_prompt["content"] + self.aime_instructions
            }
        
        return base_prompt
    
    def _get_base_system_prompt_a(self):
        """Get base system prompt for Agent A without benchmark-specific instructions"""
        # This will be overridden in subclasses
        raise NotImplementedError("Subclasses must implement _get_base_system_prompt_a")
    
    def _get_base_system_prompt_b(self):
        """Get base system prompt for Agent B without benchmark-specific instructions"""
        # This will be overridden in subclasses
        raise NotImplementedError("Subclasses must implement _get_base_system_prompt_b")
    
    def get_temperature(self) -> float:
        """Get temperature setting"""
        return self.config.get("temperature", 0.7)
    
    def get_max_tokens(self) -> int:
        """Get max tokens setting"""
        return self.config.get("max_tokens", 1000)
    
    def get_num_turns(self) -> int:
        """Get number of turns"""
        return self.config.get("num_turns", 5)