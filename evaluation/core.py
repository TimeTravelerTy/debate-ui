"""Core evaluation framework"""

from typing import Dict, List, Any, Optional, Tuple
import json
import os
import asyncio
import time
from datetime import datetime

class EvaluationManager:
    """Manager for running benchmark evaluations"""
    
    def __init__(self, benchmark, framework, strategies, results_dir):
        """
        Initialize the evaluation manager
        
        Args:
            benchmark: The benchmark to evaluate
            framework: The agent framework to use
            strategies: Dict of available strategies
            results_dir: Directory to save results
        """
        self.benchmark = benchmark
        self.framework = framework
        self.strategies = strategies
        self.results_dir = results_dir
        
        # Ensure results directory exists
        os.makedirs(results_dir, exist_ok=True)
    
    async def run_evaluation(self, strategy_id: str, max_questions: Optional[int] = None) -> Tuple[str, Dict[str, Any]]:
        """
        Run a benchmark evaluation
        
        Args:
            strategy_id: ID of the strategy to use
            max_questions: Maximum number of questions to evaluate
            
        Returns:
            Tuple of (run_id, results_dict)
        """
        # Get the strategy
        if strategy_id in self.strategies:
            strategy = self.strategies[strategy_id]
        else:
            raise ValueError(f"Unknown strategy: {strategy_id}")
        
        # Update the framework's strategy
        self.framework.set_strategy(strategy)
        
        # Get questions from the benchmark
        questions = self.benchmark.get_questions(max_questions)
        if not questions:
            raise ValueError("No questions loaded from benchmark")
        
        print(f"Running evaluation with {len(questions)} questions from {self.benchmark.name}")
        print(f"Using strategy: {strategy_id}")
        
        results = []
        total_simulated_correct = 0
        total_dual_correct = 0
        
        for i, question in enumerate(questions):
            print(f"\nQuestion {i+1}/{len(questions)} - ID: {question['id']}")
            
            # Create a unique log ID for this question
            log_id = f"{self.benchmark.name.lower()}_{question['id']}_{int(time.time())}"
            
            try:
                # Run simulated debate
                print("Running simulated debate...")
                sim_start_time = time.time()
                sim_messages = await self.framework.run_simulation(question['question'])
                sim_end_time = time.time()
                
                # Extract final answer from simulated debate
                sim_answer = self.framework.extract_final_answer(sim_messages)
                sim_time = sim_end_time - sim_start_time
                
                # Run dual agent debate
                print("Running dual agent debate...")
                dual_start_time = time.time()
                dual_messages = await self.framework.run_dual_agent(question['question'])
                dual_end_time = time.time()
                
                # Extract final answer from dual agent debate
                dual_answer = self.framework.extract_final_answer(dual_messages)
                dual_time = dual_end_time - dual_start_time
                
                # Evaluate correctness
                sim_correct = self.benchmark.evaluate_answer(sim_answer, question['ground_truth'])
                dual_correct = self.benchmark.evaluate_answer(dual_answer, question['ground_truth'])
                
                if sim_correct:
                    total_simulated_correct += 1
                if dual_correct:
                    total_dual_correct += 1
                
                # Create result entry
                result = {
                    "question_id": question['id'],
                    "question": question['question'],
                    "ground_truth": question['ground_truth'],
                    "category": question.get('category', 'unknown'),
                    "difficulty": question.get('difficulty', 'unknown'),
                    "simulated": {
                        "answer": sim_answer,
                        "correct": sim_correct,
                        "time": sim_time,
                        "log_id": log_id  # Use the same log_id for both simulated and dual
                    },
                    "dual": {
                        "answer": dual_answer,
                        "correct": dual_correct,
                        "time": dual_time,
                        "log_id": log_id  # Use the same log_id for both simulated and dual
                    }
                }
                
                # Save a consolidated log file with both simulated and dual messages
                log_path = os.path.join(self.results_dir, f"log_{log_id}.json")
                with open(log_path, 'w') as f:
                    json.dump({
                        "question_id": question['id'],
                        "question": question['question'],
                        "ground_truth": question['ground_truth'],
                        "strategy": strategy_id,
                        "benchmark": self.benchmark.name,
                        "simulated_messages": sim_messages,
                        "dual_messages": dual_messages
                    }, f, indent=2)
                
                results.append(result)
                
                # Print progress
                print(f"Question: {question['id']}")
                print(f"Ground Truth: {question['ground_truth']}")
                print(f"Simulated Answer: {sim_answer} - {'✓' if sim_correct else '✗'} ({sim_time:.2f}s)")
                print(f"Dual Agent Answer: {dual_answer} - {'✓' if dual_correct else '✗'} ({dual_time:.2f}s)")
                
            except Exception as e:
                print(f"Error processing question {question['id']}: {e}")
                import traceback
                traceback.print_exc()
        
        # Calculate summary
        total_questions = len(questions)
        simulated_accuracy = total_simulated_correct / total_questions if total_questions > 0 else 0
        dual_accuracy = total_dual_correct / total_questions if total_questions > 0 else 0
        
        summary = {
            "total_questions": total_questions,
            "simulated_correct": total_simulated_correct,
            "dual_correct": total_dual_correct,
            "simulated_accuracy": simulated_accuracy,
            "dual_accuracy": dual_accuracy
        }
        
        # Create timestamp and unique run ID
        timestamp = datetime.now().isoformat()
        run_id = f"{self.benchmark.name.lower()}_{strategy_id}_{int(time.time())}"
        
        # Save results
        output = {
            "run_id": run_id,
            "timestamp": timestamp,
            "benchmark": self.benchmark.name,
            "strategy": strategy_id,
            "summary": summary,
            "results": results
        }
        
        results_path = os.path.join(self.results_dir, f"result_{run_id}.json")
        with open(results_path, 'w') as f:
            json.dump(output, f, indent=2)
        
        # Print summary
        print("\n--- SUMMARY ---")
        print(f"Total questions: {total_questions}")
        print(f"Simulated correct: {total_simulated_correct} ({simulated_accuracy:.2%})")
        print(f"Dual agent correct: {total_dual_correct} ({dual_accuracy:.2%})")
        print(f"Results saved to: {results_path}")
        
        return run_id, output