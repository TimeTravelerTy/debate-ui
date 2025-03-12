from typing import Dict, List, Any, Optional, Tuple
import json
import time
import re

from .client import APIClient
from .utils import extract_final_answer, format_message

class AgentFramework:
    """Core framework for managing agent interactions"""
    
    def __init__(self, api_config: Dict[str, Any], strategy):
        """
        Initialize the agent framework
        
        Args:
            api_config: Configuration for the API client
            strategy: Strategy object to use for the debate
        """
        self.client = APIClient(api_config)
        self.strategy = strategy
        
    def run_simulation(self, user_prompt: str) -> List[Dict[str, str]]:
        """
        Run a simulated dialogue with a single model alternating between two agents
        
        Args:
            user_prompt: The problem to solve
            
        Returns:
            List of message dictionaries
        """
        # Create system prompt that incorporates the strategy's system prompts
        system_prompt = {
            "role": "system",
            "content": (
                "You are a helpful assistant who will simulate a debate between two agents—Agent A and Agent B—who are "
                "discussing and challenging each other's reasoning about the problem. For each turn, you will "
                "generate only the argument or counterargument content, without including any role labels "
                "(those will be provided externally). Your responses should be concise and focus on "
                "logical reasoning. In your debate, Agent A should take the position described as: "
                f"\"{self.strategy.get_system_prompt_a()['content']}\", while Agent B should act as: "
                f"\"{self.strategy.get_system_prompt_b()['content']}\". "
                "At the end of the debate, conclude with a final statement that starts with "
                "'Final Answer:' summarizing the agreed solution."
            )
        }
        
        # Initialize message history
        messages = [system_prompt, {"role": "user", "content": user_prompt}]
        
        # Create result messages (excluding system prompt)
        result_messages = [{"role": "user", "content": user_prompt}]
        
        # Get number of turns from strategy
        num_turns = self.strategy.get_num_turns()
        
        # Run the debate for the specified number of turns
        for turn in range(num_turns):
            role = "Agent A" if turn % 2 == 0 else "Agent B"
            
            # Prompt the model with the current role
            prompt = messages + [{"role": "user", "content": f"{role}: "}]
            
            # Call the API for the current turn
            response = self.client.call_api(
                prompt,
                temperature=self.strategy.get_temperature(),
                max_tokens=self.strategy.get_max_tokens()
            )
            
            # Add the response to the message history (without the role)
            messages.append({"role": "assistant", "content": response})
            
            # Add the response to the result messages (with the role)
            result_messages.append({"role": "assistant", "content": f"{role}: {response}"})
            
            print(f"[Simulated Turn {turn+1}] {role}: {response}")
            
            # Add a delay to avoid rate limiting
            time.sleep(1)
        
        return result_messages
    
    def run_dual_agent(self, user_prompt: str) -> List[Dict[str, str]]:
        """
        Run a dialogue between two separate agent instances
        
        Args:
            user_prompt: The problem to solve
            
        Returns:
            List of message dictionaries
        """
        # Initialize message histories for both agents
        messages_a = [self.strategy.get_system_prompt_a(), {"role": "user", "content": user_prompt}]
        messages_b = [self.strategy.get_system_prompt_b(), {"role": "user", "content": user_prompt}]
        
        # Create result messages
        result_messages = [{"role": "user", "content": user_prompt}]
        
        # Get number of turns from strategy
        num_turns = self.strategy.get_num_turns()
        
        # Run the debate for the specified number of turns
        for turn in range(num_turns):
            role = "Agent A" if turn % 2 == 0 else "Agent B"
            
            if role == "Agent A":
                # Get response from Agent A
                response = self.client.call_api(
                    messages_a,
                    temperature=self.strategy.get_temperature(),
                    max_tokens=self.strategy.get_max_tokens()
                )
                
                # Add the response to Agent A's message history
                messages_a.append({"role": "assistant", "content": response})
                
                # Add the response to Agent B's message history (as user)
                messages_b.append({"role": "user", "content": f"Agent A: {response}"})
                
                # Add the response to the result messages
                result_messages.append({"role": "assistant", "content": f"Agent A: {response}"})
            else:
                # Get response from Agent B
                response = self.client.call_api(
                    messages_b,
                    temperature=self.strategy.get_temperature(),
                    max_tokens=self.strategy.get_max_tokens()
                )
                
                # Add the response to Agent B's message history
                messages_b.append({"role": "assistant", "content": response})
                
                # Add the response to Agent A's message history (as user)
                messages_a.append({"role": "user", "content": f"Agent B: {response}"})
                
                # Add the response to the result messages
                result_messages.append({"role": "assistant", "content": f"Agent B: {response}"})
            
            print(f"[Turn {turn+1}] {role}: {response}")
            
            # Add a delay to avoid rate limiting
            time.sleep(1)
        
        return result_messages

    def extract_final_answer(self, messages: List[Dict[str, str]]) -> str:
        """
        Extract the final answer from the conversation
        
        Args:
            messages: List of message dictionaries
            
        Returns:
            Final answer string, or "No final answer found"
        """
        # Search through messages in reverse order
        for message in reversed(messages):
            content = message.get("content", "")
            
            # Look for the "Final Answer:" pattern
            answer = extract_final_answer(content)
            if answer:
                return answer
                
        return "No final answer found."