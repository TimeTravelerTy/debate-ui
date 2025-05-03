from typing import Dict, List, Any, Optional, Tuple, Callable
import time
import json
import re
import asyncio

from .client import APIClient
from .utils import extract_answer

class AgentFramework:
    """Core framework for managing agent interactions with asyncio support and token tracking"""
    
    def __init__(self, api_config: Dict[str, Any], strategy):
        """
        Initialize the agent framework
        
        Args:
            api_config: Configuration for the API client
            strategy: Strategy object to use for the collaboration
        """
        self.client = APIClient(api_config)
        self.strategy = strategy
        # Store the strategy name for debugging
        self._strategy_name = strategy.name if hasattr(strategy, 'name') else str(strategy)
        print(f"Initialized AgentFramework with strategy: {self._strategy_name}")
        
        # Initialize token tracking for each mode
        self.reset_token_counters()

    def set_strategy(self, strategy):
        """
        Set or update the strategy used by the framework
        
        Args:
            strategy: Strategy object to use
        """
        old_strategy = self._strategy_name
        self.strategy = strategy
        self._strategy_name = strategy.name if hasattr(strategy, 'name') else str(strategy)
        print(f"Strategy updated: {old_strategy} -> {self._strategy_name}")

    def set_answer_format(self, format: str):
        """Set the answer format for this framework instance"""
        self.answer_format = format
    
    def reset_token_counters(self):
        """Reset all token counters"""
        self.simulation_tokens = {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0
        }
        
        self.dual_agent_tokens = {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0
        }
        
    def get_token_usage(self):
        """Get token usage for both simulation and dual-agent approaches"""
        return {
            "simulation": self.simulation_tokens,
            "dual_agent": self.dual_agent_tokens,
            "total": {
                "prompt_tokens": self.simulation_tokens["prompt_tokens"] + self.dual_agent_tokens["prompt_tokens"],
                "completion_tokens": self.simulation_tokens["completion_tokens"] + self.dual_agent_tokens["completion_tokens"],
                "total_tokens": self.simulation_tokens["total_tokens"] + self.dual_agent_tokens["total_tokens"]
            }
        }
        
    async def run_simulation(self, user_prompt: str, message_callback: Optional[Callable] = None, question_id: Optional[int] = None) -> Tuple[List[Dict[str, str]], float, Dict[str, int]]:
        """
        Run a simulated dialogue with a single model alternating between two agents
        
        Args:
            user_prompt: The problem to solve
            message_callback: Optional callback function to receive messages in real-time
            question_id: Optional question ID to determine final answerer
                
        Returns:
            Tuple of (list of message dictionaries, execution_time_in_seconds, token_usage)
        """
        # Reset token counter for this run
        self.simulation_tokens = {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0
        }
        
        # Log which strategy we're using
        print(f"Running simulation with strategy: {self._strategy_name}")
        
        # Start timing
        start_time = time.time()
        # Determine which agent gives the final answer based on question_id
        # Even question_id -> Agent A, Odd question_id -> Agent B
        if question_id is not None:
            final_agent = "Agent A" if question_id % 2 == 0 else "Agent B"
        else:
            final_agent = "Agent A"  # Default to Agent A if no question_id provided
            
        # Create system prompt that incorporates the strategy's system prompts
        system_prompt = {
            "role": "system",
            "content": (
                "You are a reasoning agent who will simulate a structured interaction between two agents—Agent A and Agent B—who are "
                "collaborating on solving the given problem. Your task is to alternate between these two agents' perspectives. "
                "Each time you see '(next turn)', switch to the other agent's role. "
                "IMPORTANT: For each response, start with either 'Agent A:' or 'Agent B:' to indicate which agent is speaking. "
                "DO NOT include '(next turn)' in your response as this is just a prompt for you to switch roles. "
                "DO NOT switch roles mid-response. Each of your responses must be from ONE agent only. "
                "DO NOT simulate how the other agent would respond - wait for the next turn to do that. "
                f"Agent A should take the position described as: \"{self.strategy.get_system_prompt_a()['content']}\", while "
                f"Agent B should act as: \"{self.strategy.get_system_prompt_b()['content']}\". "
                f"When you see '(final turn)', {final_agent} should provide the final conclusion. In this final turn, "
                f"{final_agent} should provide a final statement that starts with 'Final Answer:' the solution based on the entire discussion."
            )
        }
        
        # Initialize message history
        messages = [system_prompt, {"role": "user", "content": user_prompt}]
        
        # Create result messages (excluding system prompt)
        result_messages = [{"role": "user", "content": user_prompt}]
        
        # Get number of turns from strategy
        num_turns = self.strategy.get_num_turns()
        
        # Track final answers for convergence detection
        previous_final_answer = None
        
        # Run the dialogue for the specified number of turns
        for turn in range(num_turns):
            role = "Agent A" if turn % 2 == 0 else "Agent B"
            
            # Prompt the model to respond as the current role
            if turn == 0:
                next_prompt = f"Please respond as {role}. Remember to only respond as {role}, not both agents:"
            elif turn == num_turns - 1:  # If this is the final turn
                next_prompt = f"(final turn) This is the final turn. Only {final_agent} should respond with the final answer."
            else:
                next_prompt = f"(next turn) Now respond as {role}. Remember to only respond as {role}, not both agents:"
            
            # Call the API for the current turn (using await with the async client)
            response, token_usage = await self.client.call_api_async(
                messages + [{"role": "user", "content": next_prompt}],
                temperature=self.strategy.get_temperature(),
                max_tokens=self.strategy.get_max_tokens()
            )
            
            # Track token usage
            self.simulation_tokens["prompt_tokens"] += token_usage["prompt_tokens"]
            self.simulation_tokens["completion_tokens"] += token_usage["completion_tokens"]
            self.simulation_tokens["total_tokens"] += token_usage["total_tokens"]
            
            # Clean up any "(next turn)" or "(final turn)" that might have been included in the response
            response = response.replace("(next turn)", "").replace("(final turn)", "")
            
            # Check for and fix role-switching within the response
            processed_response = self._process_simulation_response(response, role)
            
            # Add the processed response to the message history
            messages.append({"role": "assistant", "content": processed_response})
            
            # Extract the actual agent prefix if present
            agent_role = role
            agent_content = processed_response
            if processed_response.startswith("Agent A:"):
                agent_role = "Agent A"
                agent_content = processed_response[len("Agent A:"):].strip()
            elif processed_response.startswith("Agent B:"):
                agent_role = "Agent B"
                agent_content = processed_response[len("Agent B:"):].strip()
            
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
            
            # Check for convergence (if not the final turn)
            if turn < num_turns - 1:
                current_final_answer = extract_answer(agent_content, self.answer_format)
                if current_final_answer and previous_final_answer:
                    if current_final_answer == previous_final_answer:
                        print(f"Convergence detected! Both agents agree on: {current_final_answer}")
                        
                        # Add a final message to indicate convergence
                        convergence_message = f"(Interaction concluded early due to convergence on answer: {current_final_answer})"
                        result_messages.append({
                            "role": "system", 
                            "agent": "System",
                            "content": convergence_message
                        })
                        
                        # If callback provided, notify about convergence
                        if message_callback:
                            await message_callback("System", convergence_message, "simulated")
                        
                        break
                        
                previous_final_answer = current_final_answer
            
            # No delay - DeepSeek doesn't enforce rate limits
        
        # Calculate total execution time
        execution_time = time.time() - start_time
        
        # Print token usage
        print(f"Simulation token usage: {self.simulation_tokens['total_tokens']} total tokens")
        
        return result_messages, execution_time, self.simulation_tokens

    def _process_simulation_response(self, response: str, expected_role: str) -> str:
        """
        Process simulation response to handle cases where the model switches roles mid-response
        
        Args:
            response: The raw response from the model
            expected_role: The role that was expected to respond
            
        Returns:
            Processed response with only the expected role's content
        """
        # If the response doesn't start with a role prefix, add it
        if not response.startswith("Agent A:") and not response.startswith("Agent B:"):
            response = f"{expected_role}: {response}"
        
        # Check if there's a role switch in the middle
        lines = response.split("\n")
        processed_lines = []
        
        # The role we're currently processing
        current_role = expected_role
        if response.startswith("Agent A:"):
            current_role = "Agent A"
        elif response.startswith("Agent B:"):
            current_role = "Agent B"
        
        # Keep only the first role's content
        for line in lines:
            # Check for role switch indicators
            if re.match(r"^Agent [AB]:", line.strip()):
                role_in_line = line.strip().split(":")[0]
                if role_in_line != current_role:
                    # Found a mid-response role switch, stop processing
                    break
            
            processed_lines.append(line)
        
        # Join the processed lines
        processed_response = "\n".join(processed_lines)
        
        # Ensure the response starts with the role prefix
        if current_role == "Agent A" and not processed_response.startswith("Agent A:"):
            processed_response = f"Agent A: {processed_response}"
        elif current_role == "Agent B" and not processed_response.startswith("Agent B:"):
            processed_response = f"Agent B: {processed_response}"
        
        return processed_response

    async def run_dual_agent(self, user_prompt: str, message_callback: Optional[Callable] = None, question_id: Optional[int] = None) -> Tuple[List[Dict[str, str]], float, Dict[str, int]]:
        """
        Run a dialogue between two separate agent instances
        
        Args:
            user_prompt: The problem to solve
            message_callback: Optional callback function to receive messages in real-time
            question_id: Optional question ID to determine final answerer
            
        Returns:
            Tuple of (list of message dictionaries, execution_time_in_seconds, token_usage)
        """
        # Reset token counter for this run
        self.dual_agent_tokens = {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0
        }
        
        # Log which strategy we're using
        print(f"Running dual agent with strategy: {self._strategy_name}")
        
        # Start timing
        start_time = time.time()
        # Determine which agent gives the final answer based on question_id
        # Even question_id -> Agent A, Odd question_id -> Agent B
        if question_id is not None:
            final_agent_role = "Agent A" if question_id % 2 == 0 else "Agent B"
        else:
            final_agent_role = "Agent A"  # Default to Agent A if no question_id provided
            
        # Initialize message histories for both agents
        system_prompt_a = self.strategy.get_system_prompt_a()
        system_prompt_b = self.strategy.get_system_prompt_b()
        
        # Create enhanced user prompts with general role adherence instructions
        agent_a_prompt = (
            "You are in a collaborative dialogue with another agent. "
            "Please strictly adhere to your assigned role as specified in the system prompt. "
            "Be concise in your responses - this is a dialogue, not a monologue. "
            "Provide a final answer when confident enough or when explicitly instructed with '(final turn)'. "
            "The problem to discuss is:\n\n"
            f"{user_prompt}"
        )
        
        agent_b_prompt = (
            "You are in a collaborative dialogue with another agent. "
            "Please strictly adhere to your assigned role as specified in the system prompt. "
            "Be concise in your responses - this is a dialogue, not a monologue. "
            "Provide a final answer when confident enough or when explicitly instructed with '(final turn)'. "
            "The problem to discuss is:\n\n"
            f"{user_prompt}"
        )
        
        # Initialize message histories for both agents with enhanced prompts
        messages_a = [system_prompt_a, {"role": "user", "content": agent_a_prompt}]
        messages_b = [system_prompt_b, {"role": "user", "content": agent_b_prompt}]
        
        # Create result messages
        result_messages = [{"role": "user", "content": user_prompt}]
        
        # Get number of turns from strategy - allow for early stopping to save time
        num_turns = min(self.strategy.get_num_turns(), 5)  # Limit to 5 turns for optimization
        
        # Track final answers for convergence detection
        previous_final_answer = None
        
        # Run the dialogue for the specified number of turns
        for turn in range(num_turns):
            role = "Agent A" if turn % 2 == 0 else "Agent B"
            
            if role == "Agent A":
                # Check if this is the final turn for Agent A
                is_final_turn = (turn == num_turns - 1)
                is_final_answerer = (final_agent_role == "Agent A")
                
                # Get response from Agent A (using await with the async client)
                if is_final_turn and is_final_answerer:
                    # Add a hint for the final turn
                    messages_a.append({"role": "user", "content": "This is your final response. Please conclude with 'Final Answer:' followed by your conclusion based on the entire discussion."})
                
                response, token_usage = await self.client.call_api_async(
                    messages_a,
                    temperature=self.strategy.get_temperature(),
                    max_tokens=self.strategy.get_max_tokens()
                )
                
                # Track token usage
                self.dual_agent_tokens["prompt_tokens"] += token_usage["prompt_tokens"]
                self.dual_agent_tokens["completion_tokens"] += token_usage["completion_tokens"]
                self.dual_agent_tokens["total_tokens"] += token_usage["total_tokens"]
                
                # If we added a final turn hint, remove it from the history for clean state
                if is_final_turn and is_final_answerer:
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

                # Print strategy name with response for debugging
                print(f"[Turn {turn+1}] Agent A (strategy: {self._strategy_name}): {response[:100]}...")
            else:
                # Check if this is the final turn for Agent B
                is_final_turn = (turn == num_turns - 1)
                is_final_answerer = (final_agent_role == "Agent B")
                
                # Get response from Agent B (using await with the async client)
                if is_final_turn and is_final_answerer:
                    # Add a hint for the final turn if it's Agent B's final turn
                    messages_b.append({"role": "user", "content": "This is your final response. Please conclude with 'Final Answer:' followed by your conclusion based on the entire discussion."})
                elif is_final_turn and not is_final_answerer:
                    # If it's the final turn but B is not the final answerer
                    messages_b.append({"role": "user", "content": "This is your final response. Please provide your final thoughts on the problem."})
                
                response, token_usage = await self.client.call_api_async(
                    messages_b,
                    temperature=self.strategy.get_temperature(),
                    max_tokens=self.strategy.get_max_tokens()
                )
                
                # Track token usage
                self.dual_agent_tokens["prompt_tokens"] += token_usage["prompt_tokens"]
                self.dual_agent_tokens["completion_tokens"] += token_usage["completion_tokens"]
                self.dual_agent_tokens["total_tokens"] += token_usage["total_tokens"]
                
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
                
                # Print strategy name with response for debugging
                print(f"[Turn {turn+1}] Agent B (strategy: {self._strategy_name}): {response[:100]}...")
            
            # Check for convergence (if not the final turn)
            if turn < num_turns - 1:
                current_final_answer = extract_answer(response, self.answer_format)
                if current_final_answer and previous_final_answer:
                    if current_final_answer == previous_final_answer:
                        print(f"Convergence detected! Both agents agree on: {current_final_answer}")
                        
                        # Add a final message to indicate convergence
                        convergence_message = f"(Debate concluded early due to convergence on answer: {current_final_answer})"
                        result_messages.append({
                            "role": "system", 
                            "agent": "System",
                            "content": convergence_message
                        })
                        
                        # If callback provided, notify about convergence
                        if message_callback:
                            await message_callback("System", convergence_message, "dual")
                        
                        break
                        
                previous_final_answer = current_final_answer
            
            # No delay - DeepSeek doesn't enforce rate limits
        
        # Calculate total execution time
        execution_time = time.time() - start_time
        
        # Print token usage
        print(f"Dual agent token usage: {self.dual_agent_tokens['total_tokens']} total tokens")
        
        return result_messages, execution_time, self.dual_agent_tokens

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
            answer = extract_answer(content, self.answer_format)
            if answer:
                return answer
                
        return "No final answer found."