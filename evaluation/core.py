"""
Optimized evaluation module with token tracking and parallel processing
"""

from typing import Dict, List, Any, Optional, Tuple
import json
import os
import asyncio
import time
from datetime import datetime
from agent.framework import AgentFramework

class EvaluationManager:
    """Manager for running benchmark evaluations with optimizations"""
    
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
        
        # Configure batch processing
        self.batch_size = 5  # Process 5 questions in parallel for better performance
    
    async def run_parallel_evaluation(self, strategy_ids: List[str], max_questions: Optional[int] = None) -> Dict[str, Tuple[str, Dict[str, Any]]]:
        """
        Run benchmark evaluations for multiple strategies in parallel
        
        Args:
            strategy_ids: List of strategy IDs to evaluate
            max_questions: Maximum number of questions to evaluate
            
        Returns:
            Dictionary mapping strategy IDs to (run_id, results_dict) tuples
        """
        # Verify all strategies exist
        invalid_strategies = [s_id for s_id in strategy_ids if s_id not in self.strategies]
        if invalid_strategies:
            raise ValueError(f"Unknown strategies: {', '.join(invalid_strategies)}")
        
        print(f"Running parallel evaluation with {len(strategy_ids)} strategies:")
        for s_id in strategy_ids:
            print(f"  - {s_id}")
        print(f"Using {max_questions or 'all'} questions from {self.benchmark.name}")
        
        # Get the API configuration from the current framework
        api_config = self.framework.client.config
        
        # Create framework instances for each strategy and store them
        framework_instances = {}
        for strategy_id in strategy_ids:
            strategy = self.strategies[strategy_id]
            print(f"Creating framework for {strategy_id} with strategy name: {strategy.name}")
            framework_instances[strategy_id] = AgentFramework(api_config, strategy)
        
        # Create tasks for each strategy with its dedicated framework
        tasks = {}
        for strategy_id in strategy_ids:
            # Use the stored framework instance for this strategy
            strategy_framework = framework_instances[strategy_id]
            tasks[strategy_id] = asyncio.create_task(
                self._run_strategy_evaluation(strategy_id, max_questions, strategy_framework)
            )
        
        # Wait for all tasks to complete
        results = {}
        for strategy_id, task in tasks.items():
            try:
                run_id, result = await task
                results[strategy_id] = (run_id, result)
                print(f"Strategy {strategy_id} completed with run_id: {run_id}")
            except Exception as e:
                print(f"Error running strategy {strategy_id}: {e}")
                import traceback
                traceback.print_exc()
        
        # Generate a summary report comparing all strategies
        if results:
            await self._save_comparison_report(results)
        
        return results
    
    async def _run_strategy_evaluation(self, strategy_id: str, max_questions: Optional[int], strategy_framework: AgentFramework) -> Tuple[str, Dict[str, Any]]:
        """
        Run evaluation for a single strategy with a dedicated framework
        
        Args:
            strategy_id: ID of the strategy to use
            max_questions: Maximum number of questions to evaluate
            strategy_framework: Dedicated framework instance for this strategy
            
        Returns:
            Tuple of (run_id, results_dict)
        """
        # No need to swap frameworks, just use the dedicated one directly
        print(f"Running parallel evaluation for {strategy_id} using strategy: {strategy_framework.strategy.name}")
        
        # Run the evaluation with the dedicated framework
        # The parameter order should match the run_evaluation definition
        return await self.run_evaluation(
            strategy_id=strategy_id, 
            max_questions=max_questions, 
            skip_strategy_setting=True,  # Important! Don't try to set the strategy
            framework=strategy_framework  # Pass the framework as the last parameter
        )
    
    async def run_evaluation(self, strategy_id: str, max_questions: Optional[int] = None, 
                         skip_strategy_setting: bool = False, framework: Optional[AgentFramework] = None) -> Tuple[str, Dict[str, Any]]:
        """
        Run a benchmark evaluation with optimized batching
        
        Args:
            strategy_id: ID of the strategy to use
            max_questions: Maximum number of questions to evaluate
            skip_strategy_setting: If True, don't override the framework's strategy (for parallel execution)
            framework: Optional specific framework instance to use (for parallel execution)
            
        Returns:
            Tuple of (run_id, results_dict)
        """
        # Use the provided framework or fallback to self.framework
        current_framework = framework if framework is not None else self.framework
        
        # Only set the strategy if not in parallel mode and no custom framework provided
        if not skip_strategy_setting and framework is None:
            # Get the strategy
            if strategy_id in self.strategies:
                strategy = self.strategies[strategy_id]
            else:
                raise ValueError(f"Unknown strategy: {strategy_id}")
            
            # Update the framework's strategy
            current_framework.set_strategy(strategy)
        
        # Log which strategy we're using
        strategy_name = current_framework.strategy.name
        print(f"Framework is using strategy: {strategy_name}")
        
        # Get questions from the benchmark
        questions = self.benchmark.get_questions(max_questions)
        if not questions:
            raise ValueError("No questions loaded from benchmark")
        
        print(f"Running evaluation with {len(questions)} questions from {self.benchmark.name}")
        print(f"Using strategy: {strategy_id} (Framework strategy: {strategy_name})")
        
        # Initialize results and stats
        results = []
        total_simulated_correct = 0
        total_dual_correct = 0
        total_simulated_tokens = 0
        total_dual_tokens = 0
        
        # Convert dict to list if needed (SimpleBenchmark returns dict, GPQA returns list)
        questions_list = []
        if isinstance(questions, dict):
            for q_id, q_data in questions.items():
                q_data['id'] = q_id  # Ensure id is included if not already
                questions_list.append(q_data)
        else:
            questions_list = questions
        
        # Process questions in batches
        batches = self._create_batches(questions_list, self.batch_size)
        
        for batch_idx, batch in enumerate(batches):
            print(f"Processing batch {batch_idx+1}/{len(batches)} with strategy {strategy_id} ({strategy_name})")
            
            # Create tasks for all questions in the batch
            batch_tasks = []
            for question in batch:
                task = asyncio.create_task(self._process_question(question, strategy_id, current_framework))
                batch_tasks.append(task)
            
            # Wait for all tasks in the batch to complete
            batch_results = await asyncio.gather(*batch_tasks)
            
            # Process batch results
            for result in batch_results:
                if result is None:
                    continue  # Skip failed questions
                    
                results.append(result)
                
                # Update stats
                if result["simulated"]["correct"]:
                    total_simulated_correct += 1
                if result["dual"]["correct"]:
                    total_dual_correct += 1
                    
                # Update token counts
                total_simulated_tokens += result["simulated"].get("tokens", {}).get("total_tokens", 0)
                total_dual_tokens += result["dual"].get("tokens", {}).get("total_tokens", 0)
                
                # Print summary for this question
                print(f"Question: {result['question_id']}")
                print(f"Ground Truth: {result['ground_truth']}")
                print(f"Simulated Answer: {result['simulated']['answer']} - {'✓' if result['simulated']['correct'] else '✗'} ({result['simulated']['time']:.2f}s, {result['simulated'].get('tokens', {}).get('total_tokens', 0)} tokens)")
                print(f"Dual Agent Answer: {result['dual']['answer']} - {'✓' if result['dual']['correct'] else '✗'} ({result['dual']['time']:.2f}s, {result['dual'].get('tokens', {}).get('total_tokens', 0)} tokens)")
                
                # Print evolution info if available
                if "evolution" in result["simulated"] and "evolution" in result["dual"]:
                    print(f"Simulated Evolution: {result['simulated']['evolution']['agreement_pattern']} / {result['simulated']['evolution']['correctness_pattern']}")
                    print(f"Dual Evolution: {result['dual']['evolution']['agreement_pattern']} / {result['dual']['evolution']['correctness_pattern']}")
        
        # Calculate summary
        total_questions = len(results)
        simulated_accuracy = total_simulated_correct / total_questions if total_questions > 0 else 0
        dual_accuracy = total_dual_correct / total_questions if total_questions > 0 else 0
        
        summary = {
            "total_questions": total_questions,
            "simulated_correct": total_simulated_correct,
            "dual_correct": total_dual_correct,
            "simulated_accuracy": simulated_accuracy,
            "dual_accuracy": dual_accuracy,
            "token_usage": {
                "simulated_tokens": total_simulated_tokens,
                "dual_tokens": total_dual_tokens,
                "total_tokens": total_simulated_tokens + total_dual_tokens
            }
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
        
        # Try to generate evolution summary if available
        try:
            from evaluation.solution_evolution import get_analysis_summary
            evolution_summary = get_analysis_summary(results)
            output["evolution_summary"] = evolution_summary
        except Exception as e:
            print(f"Could not generate evolution summary: {e}")
        
        results_path = os.path.join(self.results_dir, f"result_{run_id}.json")
        with open(results_path, 'w') as f:
            json.dump(output, f, indent=2)
        
        # Print summary
        print("\n--- SUMMARY ---")
        print(f"Total questions: {total_questions}")
        print(f"Simulated correct: {total_simulated_correct} ({simulated_accuracy:.2%})")
        print(f"Dual agent correct: {total_dual_correct} ({dual_accuracy:.2%})")
        print(f"Token usage: {total_simulated_tokens + total_dual_tokens} total tokens")
        print(f"  - Simulated: {total_simulated_tokens} tokens")
        print(f"  - Dual agent: {total_dual_tokens} tokens")
        print(f"Results saved to: {results_path}")
        
        return run_id, output
    
    def _create_batches(self, items: List[Any], batch_size: int) -> List[List[Any]]:
        """
        Create batches of items for parallel processing
        
        Args:
            items: List of items to batch
            batch_size: Size of each batch
            
        Returns:
            List of batches, where each batch is a list of items
        """
        return [items[i:i + batch_size] for i in range(0, len(items), batch_size)]
    
    async def _process_question(self, question: Dict[str, Any], strategy_id: str, framework: AgentFramework) -> Optional[Dict[str, Any]]:
        """
        Process a single question
        
        Args:
            question: Question data
            strategy_id: ID of the strategy being used
            framework: Framework instance to use for this question
            
        Returns:
            Result dictionary or None if processing failed
        """
        try:
            # Use the provided framework
            print(f"Processing question {question['id']} using {framework.strategy.name}")
            
            # Create a unique log ID for this question
            log_id = f"{self.benchmark.name.lower()}_{question['id']}_{strategy_id}_{int(time.time())}"
            
            question_text = question.get('question', question.get('question_text', question.get('prompt', '')))
            
            # Get question_id for alternating final answerer
            # Convert to a numeric hash value if it's not already an integer
            if isinstance(question['id'], int):
                question_id = question['id']
            else:
                # Generate a consistent numeric hash for string IDs
                # This ensures the same question gets the same agent assignment
                question_id_str = str(question['id'])
                question_id = sum(ord(c) for c in question_id_str) % 1000  # Simple hash
            
            # Run simulated and dual agent debates concurrently using the provided framework
            print(f"Running debates for question {question['id']} using {framework.strategy.name}...")
            
            # The run_simulation and run_dual_agent methods now return (messages, time, tokens) tuples
            sim_task = framework.run_simulation(question_text, question_id=question_id)
            dual_task = framework.run_dual_agent(question_text, question_id=question_id)

            # Wait for both to complete
            sim_result, dual_result = await asyncio.gather(sim_task, dual_task)
            
            # Unpack the results
            sim_messages, sim_time, sim_tokens = sim_result
            dual_messages, dual_time, dual_tokens = dual_result

            # Extract final answers
            sim_answer = framework.extract_final_answer(sim_messages)
            dual_answer = framework.extract_final_answer(dual_messages)
            
            # Get ground truth from question data
            ground_truth = question.get('ground_truth', question.get('answer', ''))
            
            # Evaluate correctness
            sim_correct = self.benchmark.evaluate_answer(sim_answer, ground_truth)
            dual_correct = self.benchmark.evaluate_answer(dual_answer, ground_truth)
            
            # Process results with evolution analysis if available
            try:
                # Import the solution_evolution module
                from evaluation.solution_evolution import analyze_solution_evolution
                
                # Analyze solution evolution
                sim_evolution = analyze_solution_evolution(sim_messages, ground_truth, self.benchmark)
                dual_evolution = analyze_solution_evolution(dual_messages, ground_truth, self.benchmark)
                
                # Create result with evolution analysis
                result = {
                    "question_id": question['id'],
                    "question": question_text,
                    "ground_truth": ground_truth,
                    "category": question.get('category', 'unknown'),
                    "difficulty": question.get('difficulty', 'unknown'),
                    "simulated": {
                        "answer": sim_answer,
                        "correct": sim_correct,
                        "time": sim_time,
                        "tokens": sim_tokens,
                        "log_id": log_id,
                        "evolution": {
                            "agreement_pattern": sim_evolution["agreement_pattern"],
                            "correctness_pattern": sim_evolution["correctness_pattern"]
                        }
                    },
                    "dual": {
                        "answer": dual_answer,
                        "correct": dual_correct,
                        "time": dual_time,
                        "tokens": dual_tokens,
                        "log_id": log_id,
                        "evolution": {
                            "agreement_pattern": dual_evolution["agreement_pattern"],
                            "correctness_pattern": dual_evolution["correctness_pattern"]
                        }
                    }
                }
                
                # Save conversation logs
                self._save_conversation_log(log_id, question, ground_truth, strategy_id, sim_messages, dual_messages, sim_evolution, dual_evolution)
                
            except Exception as e:
                print(f"Error in solution evolution analysis: {e}")
                
                # Fallback to result without evolution analysis
                result = {
                    "question_id": question['id'],
                    "question": question_text,
                    "ground_truth": ground_truth,
                    "category": question.get('category', 'unknown'),
                    "difficulty": question.get('difficulty', 'unknown'),
                    "simulated": {
                        "answer": sim_answer,
                        "correct": sim_correct,
                        "time": sim_time,
                        "tokens": sim_tokens,
                        "log_id": log_id
                    },
                    "dual": {
                        "answer": dual_answer,
                        "correct": dual_correct,
                        "time": dual_time,
                        "tokens": dual_tokens,
                        "log_id": log_id
                    }
                }
                
                # Save basic logs
                self._save_conversation_log(log_id, question, ground_truth, strategy_id, sim_messages, dual_messages)
            
            return result
            
        except Exception as e:
            print(f"Error processing question {question['id']}: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _save_conversation_log(self, log_id: str, question: Dict[str, Any], ground_truth: str, 
                              strategy_id: str, sim_messages: List[Dict[str, Any]], 
                              dual_messages: List[Dict[str, Any]], 
                              sim_evolution: Optional[Dict[str, Any]] = None, 
                              dual_evolution: Optional[Dict[str, Any]] = None):
        """
        Save conversation logs to disk
        
        Args:
            log_id: Unique log ID
            question: Question data
            ground_truth: Ground truth answer
            strategy_id: Strategy ID
            sim_messages: Simulated messages
            dual_messages: Dual agent messages
            sim_evolution: Optional simulation evolution data
            dual_evolution: Optional dual agent evolution data
        """
        log_data = {
            "question_id": question['id'],
            "question": question.get('question', question.get('question_text', question.get('prompt', ''))),
            "ground_truth": ground_truth,
            "strategy": strategy_id,
            "benchmark": self.benchmark.name,
            "simulated_messages": sim_messages,
            "dual_messages": dual_messages
        }
        
        # Add evolution data if available
        if sim_evolution:
            log_data["simulated_evolution"] = sim_evolution
        if dual_evolution:
            log_data["dual_evolution"] = dual_evolution
        
        # Save to disk
        log_path = os.path.join(self.results_dir, f"log_{log_id}.json")
        with open(log_path, 'w') as f:
            json.dump(log_data, f, indent=2)
        
    async def _save_comparison_report(self, results: Dict[str, Tuple[str, Dict[str, Any]]]):
        """
        Generate and save a comparison report for multiple strategies
        
        Args:
            results: Dictionary mapping strategy IDs to (run_id, results_dict) tuples
        """
        # Extract summary data
        comparison = {
            "timestamp": datetime.now().isoformat(),
            "benchmark": self.benchmark.name,
            "strategies": {},
            "questions": {},
            "token_usage": {}
        }
        
        total_tokens = 0
        
        # Build strategy comparison data
        for strategy_id, (run_id, result) in results.items():
            # Add basic summary data
            comparison["strategies"][strategy_id] = {
                "run_id": run_id,
                "summary": result["summary"]
            }
            
            # Track token usage
            if "token_usage" in result["summary"]:
                strategy_tokens = result["summary"]["token_usage"].get("total_tokens", 0)
                comparison["token_usage"][strategy_id] = strategy_tokens
                total_tokens += strategy_tokens
            
            # Add evolution summary if available
            if "evolution_summary" in result:
                comparison["strategies"][strategy_id]["evolution_summary"] = result["evolution_summary"]
        
        # Add total token usage
        comparison["token_usage"]["total"] = total_tokens
        
        # Build question-by-question comparison
        # First, get all unique question IDs
        question_ids = set()
        for _, (_, result) in results.items():
            for question_result in result["results"]:
                question_ids.add(question_result["question_id"])
        
        # Now build the question comparison data
        for q_id in question_ids:
            comparison["questions"][q_id] = {}
            for strategy_id, (_, result) in results.items():
                # Find this question in the strategy's results
                for question_result in result["results"]:
                    if question_result["question_id"] == q_id:
                        question_data = {
                            "ground_truth": question_result["ground_truth"],
                            "simulated": {
                                "answer": question_result["simulated"]["answer"],
                                "correct": question_result["simulated"]["correct"],
                                "time": question_result["simulated"]["time"]
                            },
                            "dual": {
                                "answer": question_result["dual"]["answer"],
                                "correct": question_result["dual"]["correct"],
                                "time": question_result["dual"]["time"]
                            }
                        }
                        
                        # Add token usage if available
                        if "tokens" in question_result["simulated"]:
                            question_data["simulated"]["tokens"] = question_result["simulated"]["tokens"]
                        if "tokens" in question_result["dual"]:
                            question_data["dual"]["tokens"] = question_result["dual"]["tokens"]
                        
                        # Add evolution data if available
                        if "evolution" in question_result["simulated"]:
                            question_data["simulated"]["evolution"] = question_result["simulated"]["evolution"]
                        if "evolution" in question_result["dual"]:
                            question_data["dual"]["evolution"] = question_result["dual"]["evolution"]
                        
                        comparison["questions"][q_id][strategy_id] = question_data
                        break
        
        # Save the comparison report
        timestamp = int(time.time())
        report_path = os.path.join(self.results_dir, f"comparison_{self.benchmark.name.lower()}_{timestamp}.json")
        with open(report_path, 'w') as f:
            json.dump(comparison, f, indent=2)
        
        print(f"Strategy comparison report saved to: {report_path}")
        print(f"Total tokens used across all strategies: {total_tokens}")