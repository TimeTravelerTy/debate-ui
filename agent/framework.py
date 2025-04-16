from typing import Dict, List, Any, Optional, Tuple, Callable
import json
import time
import re
import asyncio

from .client import APIClient
from .utils import extract_final_answer, format_message

class AgentFramework:
    """Core framework for managing agent interactions with asyncio support"""
    
    def __init__(self, api_config: Dict[str, Any], strategy):
        """
        Initialize the agent framework
        
        Args:
            api_config: Configuration for the API client
            strategy: Strategy object to use for the collaboration
        """
        self.client = APIClient(api_config)
        self.strategy = strategy

    def set_strategy(self, strategy):
        """
        Set or update the strategy used by the framework
        
        Args:
            strategy: Strategy object to use
        """
        self.strategy = strategy
        
    async def run_simulation(self, user_prompt: str, message_callback: Optional[Callable] = None) -> List[Dict[str, str]]:
        """
        Run a simulated dialogue with a single model alternating between two agents
        
        Args:
            user_prompt: The problem to solve
            message_callback: Optional callback function to receive messages in real-time
            
        Returns:
            List of message dictionaries
        """
        # Create system prompt that incorporates the strategy's system prompts
        system_prompt = {
            "role": "system",
            "content": (
                "You are a reasoning agent who will simulate a structured interaction between two agents—Agent A and Agent B—who are "
                "collaborating on solving the given problem. Your task is to alternate between these two agents' perspectives. "
                "Each time you see '(next turn)', switch to the other agent's role. "
                "IMPORTANT: For each response, start with either 'Agent A:' or 'Agent B:' to indicate which agent is speaking. "
                "DO NOT include '(next turn)' in your response as this is just a prompt for you to switch roles. DO NOT switch roles mid-response. "
                f"Agent A should take the position described as: \"{self.strategy.get_system_prompt_a()['content']}\", while "
                f"Agent B should act as: \"{self.strategy.get_system_prompt_b()['content']}\". "
                "When you see '(final turn)', provide your final conclusion. In this final turn, "
                "the designated agent should provide a final statement that starts with 'Final Answer:' the solution based on the entire discussion."
            )
        }
        
        # Initialize message history
        messages = [system_prompt, {"role": "user", "content": user_prompt}]
        
        # Create result messages (excluding system prompt)
        result_messages = [{"role": "user", "content": user_prompt}]
        
        # Get number of turns from strategy
        num_turns = self.strategy.get_num_turns()
        
        # Run the dialogue for the specified number of turns
        for turn in range(num_turns):
            role = "Agent A" if turn % 2 == 0 else "Agent B"
            
            # Prompt the model to respond as the current role
            if turn == 0:
                next_prompt = f"Please respond as {role}:"
            elif turn == num_turns - 1:  # If this is the final turn
                next_prompt = "(final turn)"
            else:
                next_prompt = "(next turn)"
            
            # Call the API for the current turn (using await with the async client)
            response = await self.client.call_api_async(
                messages + [{"role": "user", "content": next_prompt}],
                temperature=self.strategy.get_temperature(),
                max_tokens=self.strategy.get_max_tokens()
            )
            
            # Clean up any "(next turn)" or "(final turn)" that might have been included in the response
            response = response.replace("(next turn)", "").replace("(final turn)", "")
            
            # Add the response to the message history
            messages.append({"role": "assistant", "content": response})
            
            # Extract the actual agent prefix if present
            agent_role = role
            agent_content = response
            if response.startswith("Agent A:"):
                agent_role = "Agent A"
                agent_content = response[len("Agent A:"):].strip()
            elif response.startswith("Agent B:"):
                agent_role = "Agent B"
                agent_content = response[len("Agent B:"):].strip()
            
            # Create a message entry
            message_entry = {
                "role": "assistant", 
                "agent": agent_role,
                "content": agent_content
            }
            
            # Add the response to the result messages
            result_messages.append(message_entry)
            
            # Call the callback if provided
            if message_callback:
                await message_callback(agent_role, agent_content, "simulated")
            
            print(f"[Simulated Turn {turn+1}] {agent_role}: {agent_content[:100]}...")
            
            # Add a delay to avoid rate limiting
            await asyncio.sleep(1)
        
        return result_messages

    async def run_dual_agent(self, user_prompt: str, message_callback: Optional[Callable] = None) -> List[Dict[str, str]]:
        """
        Run a dialogue between two separate agent instances
        
        Args:
            user_prompt: The problem to solve
            message_callback: Optional callback function to receive messages in real-time
            
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
        
        # Run the dialogue for the specified number of turns
        for turn in range(num_turns):
            role = "Agent A" if turn % 2 == 0 else "Agent B"
            
            if role == "Agent A":
                # Check if this is the final turn for Agent A
                is_final_turn = (turn == num_turns - 1)
                
                # Get response from Agent A (using await with the async client)
                if is_final_turn:
                    # Add a hint for the final turn
                    messages_a.append({"role": "user", "content": "This is your final response. Please conclude with 'Final Answer:' followed by your conclusion based on the entire discussion."})
                
                response = await self.client.call_api_async(
                    messages_a,
                    temperature=self.strategy.get_temperature(),
                    max_tokens=self.strategy.get_max_tokens()
                )
                
                # If we added a final turn hint, remove it from the history for clean state
                if is_final_turn:
                    messages_a.pop()
                
                # Add the response to Agent A's message history
                messages_a.append({"role": "assistant", "content": response})
                
                # Add the response to Agent B's message history (as user)
                messages_b.append({"role": "user", "content": f"Agent A: {response}"})
                
                # Add the response to the result messages
                result_messages.append({"role": "assistant", "agent": "Agent A", "content": response})
                
                # Call the callback if provided
                if message_callback:
                    await message_callback("Agent A", response, "dual")
            else:
                # Check if this is the final turn for Agent B
                is_final_turn = (turn == num_turns - 1)
                
                # Get response from Agent B (using await with the async client)
                if is_final_turn:
                    # Add a hint for the final turn if it's Agent B's final turn
                    messages_b.append({"role": "user", "content": "This is your final response. Please provide your final thoughts on the problem."})
                
                response = await self.client.call_api_async(
                    messages_b,
                    temperature=self.strategy.get_temperature(),
                    max_tokens=self.strategy.get_max_tokens()
                )
                
                # If we added a final turn hint, remove it from the history for clean state
                if is_final_turn:
                    messages_b.pop()
                
                # Add the response to Agent B's message history
                messages_b.append({"role": "assistant", "content": response})
                
                # Add the response to Agent A's message history (as user)
                messages_a.append({"role": "user", "content": f"Agent B: {response}"})
                
                # Add the response to the result messages
                result_messages.append({"role": "assistant", "agent": "Agent B", "content": response})
                
                # Call the callback if provided
                if message_callback:
                    await message_callback("Agent B", response, "dual")
            
            print(f"[Turn {turn+1}] {role}: {response[:100]}...")
            
            # Add a delay to avoid rate limiting
            await asyncio.sleep(1)
        
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