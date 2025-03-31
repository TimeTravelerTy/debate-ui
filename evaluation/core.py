import os
import time
import json
import uuid
import asyncio
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable, Tuple, TypedDict

from agent.framework import AgentFramework
from .benchmarks.base import Benchmark

class EvaluationManager:
    """Core manager for running evaluations"""
    
    def __init__(
        self, 
        benchmark: Benchmark, 
        agent_framework: AgentFramework, 
        strategies: Dict[str, Any],
        output_dir: str = "./results"
    ):
        """
        Initialize the evaluation manager
        
        Args:
            benchmark: Benchmark instance
            agent_framework: AgentFramework instance
            strategies: Dictionary mapping strategy IDs to strategy instances
            output_dir: Directory to store evaluation results
        """
        self.benchmark = benchmark
        self.agent_framework = agent_framework
        self.strategies = strategies
        self.output_dir = output_dir
        
        # Create output directory if it doesn't exist
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
    async def run_evaluation(
        self, 
        strategy_id: str, 
        max_questions: Optional[int] = None,
        progress_callback: Optional[Callable[[int, int, Dict[str, Any]], None]] = None
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Run evaluation for a specific strategy
        
        Args:
            strategy_id: ID of the strategy to use
            max_questions: Maximum number of questions to evaluate
            progress_callback: Optional callback for progress updates
            
        Returns:
            Tuple containing the run ID and results
        """
        # Check if strategy exists
        if strategy_id not in self.strategies:
            raise ValueError(f"Strategy '{strategy_id}' not found")
            
        questions = self.benchmark.get_questions()
        
        # Limit questions if specified
        if max_questions:
            question_ids = sorted(list(questions.keys()))[:max_questions]
        else:
            question_ids = sorted(list(questions.keys()))
            
        strategy = self.strategies[strategy_id]
        results = []
        
        # Set benchmark name in strategy
        strategy.benchmark_name = self.benchmark.name
        
        # Create unique run ID
        run_id = f"{strategy_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Set the strategy in the agent framework
        self.agent_framework.set_strategy(strategy)
        
        for i, q_id in enumerate(question_ids):
            print(f"Processing question {q_id} ({i+1}/{len(question_ids)})")
            question_data = questions[q_id]
            question = question_data["prompt"]
            
            # Run simulated and dual agent approaches in parallel
            sim_task = asyncio.create_task(
                self._run_simulated(question)
            )
            
            dual_task = asyncio.create_task(
                self._run_dual_agent(question)
            )
            
            # Wait for both tasks to complete
            try:
                # Use asyncio.gather to run both tasks concurrently
                simulated_result, dual_result = await asyncio.gather(sim_task, dual_task)
                simulated_messages, simulated_final, single_time = simulated_result
                dual_messages, dual_final, dual_time = dual_result
            except Exception as e:
                print(f"Error running tasks in parallel: {e}")
                # Fallback to sequential execution if parallel fails
                simulated_result = await self._run_simulated(question)
                dual_result = await self._run_dual_agent(question)
                simulated_messages, simulated_final, single_time = simulated_result
                dual_messages, dual_final, dual_time = dual_result
            
            # Extract and evaluate answers
            simulated_eval = self.benchmark.evaluate_response(q_id, simulated_final)
            dual_eval = self.benchmark.evaluate_response(q_id, dual_final)
            
            # Save conversation logs
            log_id = f"{run_id}_{q_id}"
            self._save_conversation_log(log_id, {
                "question_id": q_id,
                "question": question,
                "simulated_messages": simulated_messages,
                "dual_messages": dual_messages,
                "simulated_final": simulated_final,
                "dual_final": dual_final
            })
            
            # Record result
            result = {
                "question_id": q_id,
                "simulated": {
                    "correct": simulated_eval["correct"],
                    "answer": simulated_eval["extracted_answer"],
                    "time": single_time,
                    "log_id": log_id
                },
                "dual": {
                    "correct": dual_eval["correct"],
                    "answer": dual_eval["extracted_answer"],
                    "time": dual_time,
                    "log_id": log_id
                },
                "ground_truth": simulated_eval["ground_truth"]
            }
            results.append(result)
            
            # Call progress callback if provided
            if progress_callback:
                progress_callback(i + 1, len(question_ids), result)
                
            # Save intermediate results
            self._save_results(run_id, results, strategy_id)
            
            # Add a delay between questions to avoid rate limiting
            await asyncio.sleep(2)
                
        # Save final results
        self._save_results(run_id, results, strategy_id)
        return run_id, results

    async def _run_simulated(self, question: str) -> Tuple[List[Dict[str, Any]], str, float]:
        """
        Run the simulated approach for a question
        
        Args:
            question: The question to process
            
        Returns:
            Tuple of (messages, final_answer, elapsed_time)
        """
        start_time = time.time()
        try:
            messages = await self.agent_framework.run_simulation(question)
            final_answer = self._get_final_answer(messages)
        except Exception as e:
            print(f"Error in simulated run: {e}")
            messages = []
            final_answer = f"Error: {str(e)}"
        elapsed_time = time.time() - start_time
        
        return messages, final_answer, elapsed_time

    async def _run_dual_agent(self, question: str) -> Tuple[List[Dict[str, Any]], str, float]:
        """
        Run the dual agent approach for a question
        
        Args:
            question: The question to process
            
        Returns:
            Tuple of (messages, final_answer, elapsed_time)
        """
        start_time = time.time()
        try:
            messages = await self.agent_framework.run_dual_agent(question)
            final_answer = self._get_final_answer(messages)
        except Exception as e:
            print(f"Error in dual agent run: {e}")
            messages = []
            final_answer = f"Error: {str(e)}"
        elapsed_time = time.time() - start_time
        
        return messages, final_answer, elapsed_time  
    def _save_conversation_log(self, log_id: str, data: Dict[str, Any]) -> None:
        """
        Save raw conversation logs
        
        Args:
            log_id: Unique ID for the log
            data: Log data to save
        """
        log_path = os.path.join(self.output_dir, f"log_{log_id}.json")
        with open(log_path, 'w') as f:
            json.dump(data, f, indent=2)
            
    def _save_results(self, run_id: str, results: List[Dict[str, Any]], strategy_id: str) -> None:
        """
        Save summary results
        
        Args:
            run_id: Unique ID for the run
            results: List of result dictionaries
            strategy_id: ID of the strategy used
        """
        # Calculate statistics
        simulated_correct = sum(1 for r in results if r.get("simulated", {}).get("correct", False))
        dual_correct = sum(1 for r in results if r.get("dual", {}).get("correct", False))
        total = len(results)
        
        if total == 0:
            simulated_accuracy = 0
            dual_accuracy = 0
        else:
            simulated_accuracy = simulated_correct / total
            dual_accuracy = dual_correct / total
        
        summary = {
            "run_id": run_id,
            "strategy": strategy_id,
            "timestamp": datetime.now().isoformat(),
            "benchmark": self.benchmark.name,
            "results": results,
            "summary": {
                "simulated_accuracy": simulated_accuracy,
                "dual_accuracy": dual_accuracy,
                "total_questions": total,
                "simulated_correct": simulated_correct,
                "dual_correct": dual_correct
            }
        }
        
        result_path = os.path.join(self.output_dir, f"result_{run_id}.json")
        with open(result_path, 'w') as f:
            json.dump(summary, f, indent=2)
            
    def _get_final_answer(self, messages: List[Dict[str, Any]]) -> str:
        """
        Extract the final answer from the conversation
        
        Args:
            messages: List of message dictionaries
            
        Returns:
            Final answer as a string
        """
        # If empty messages, return empty string
        if not messages:
            return ""
            
        # Get the last message from the assistant
        for message in reversed(messages):
            if message.get("role") == "assistant" or message.get("agent", "").startswith("Agent"):
                return message.get("content", "")
                
        # If no assistant message found, return the last message content
        return messages[-1].get("content", "")