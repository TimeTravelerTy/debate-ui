from typing import Dict, List, Any, Optional, Tuple, Callable
import time
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
        
    async def run_simulation(self, user_prompt: str, message_callback: Optional[Callable] = None, question_id: Optional[int] = None) -> Tuple[List[Dict[str, str]], float]:
        """
        Run a simulated dialogue with a single model alternating between two agents
        
        Args:
            user_prompt: The problem to solve
            message_callback: Optional callback function to receive messages in real-time
            question_id: Optional question ID to determine final answerer
            
        Returns:
            Tuple of (list of message dictionaries, execution_time_in_seconds)
        """
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
                "Each time and only when you see '(next turn)', switch to the other agent's role. "
                "IMPORTANT: For each response, start with either 'Agent A:' or 'Agent B:' to indicate which agent is speaking. "
                "DO NOT include '(next turn)' in your response as this is just a prompt for you to switch roles. DO NOT switch roles mid-response. "
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
            
            # Check for convergence (if not the final turn)
            if turn < num_turns - 1:
                current_final_answer = extract_final_answer(agent_content)
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
                            await message_callback("System", convergence_message, "simulated")
                        
                        break
                        
                previous_final_answer = current_final_answer
            
            # Add a delay to avoid rate limiting
            await asyncio.sleep(1)
        
        # Calculate total execution time
        execution_time = time.time() - start_time
        
        return result_messages, execution_time

    async def run_dual_agent(self, user_prompt: str, message_callback: Optional[Callable] = None, question_id: Optional[int] = None) -> Tuple[List[Dict[str, str]], float]:
        """
        Run a dialogue between two separate agent instances
        
        Args:
            user_prompt: The problem to solve
            message_callback: Optional callback function to receive messages in real-time
            question_id: Optional question ID to determine final answerer
            
        Returns:
            Tuple of (list of message dictionaries, execution_time_in_seconds)
        """
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
        
        # Get number of turns from strategy
        num_turns = self.strategy.get_num_turns()
        
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
                
                response = await self.client.call_api_async(
                    messages_a,
                    temperature=self.strategy.get_temperature(),
                    max_tokens=self.strategy.get_max_tokens()
                )
                
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
            
            # Check for convergence (if not the final turn)
            if turn < num_turns - 1:
                current_final_answer = extract_final_answer(response)
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
            
            # Add a delay to avoid rate limiting
            await asyncio.sleep(1)
        
        # Calculate total execution time
        execution_time = time.time() - start_time
        
        return result_messages, execution_time

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