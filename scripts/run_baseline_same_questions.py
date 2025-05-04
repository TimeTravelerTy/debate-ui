#!/usr/bin/env python3
"""
Run baseline evaluation on the same AIME questions from a previous run
"""

import sys
import os
import argparse
import json
import time
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the parent directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import necessary modules
from agent.client import APIClient
from agent.utils import extract_answer
from evaluation.benchmarks.aime_benchmark import AIMEBenchmark

def extract_questions_from_result(result_file):
    """Extract questions from a previous result file"""
    with open(result_file, 'r') as f:
        data = json.load(f)
    
    questions = {}
    for result in data['results']:
        question_id = result['question_id']
        questions[question_id] = {
            'id': question_id,
            'question': result['question'],
            'answer': result['ground_truth']
        }
    
    return questions

def run_baseline_on_questions(questions, api_config, max_tokens=9000):
    """
    Run baseline evaluation on specific questions
    
    Args:
        questions: Dictionary of questions
        api_config: API configuration
        max_tokens: Maximum tokens for each response
    """
    # Initialize API client
    client = APIClient(api_config)
    
    print(f"Running baseline evaluation on {len(questions)} AIME questions")
    print(f"Using model: {api_config['model_name']}")
    print(f"Max tokens per response: {max_tokens}")
    
    # Initialize results
    results = []
    total_correct = 0
    total_tokens = 0
    
    # Create a dummy benchmark for evaluation
    benchmark = AIMEBenchmark(years_range=(2021, 2024))
    
    # Process each question
    for idx, (q_id, question) in enumerate(questions.items()):
        print(f"\nProcessing question {idx+1}/{len(questions)} (ID: {question['id']})")
        
        # Create a minimal prompt
        prompt = f"""Solve this AIME (American Invitational Mathematics Examination) problem. Give your answer as an integer between 0 and 999.
                    Problem:
                    {question['question']}

                    Please solve step by step and end with "Final Answer: N" where N is your integer answer."""
        
        # Call the API
        start_time = time.time()
        response, token_usage = client.call_api(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=max_tokens
        )
        end_time = time.time()

        # Print the raw response (limited for brevity) for debugging
        print(f"Raw response: {response[:1000]}...")  # Print first 1000 characters for brevity
        
        # Extract answer
        answer = extract_answer(response, "integer")
        
        # Evaluate answer
        ground_truth = question.get('answer', '')
        is_correct = benchmark.evaluate_answer(answer or "", ground_truth)
        
        # Record results
        result = {
            "question_id": question['id'],
            "question": question['question'],
            "ground_truth": ground_truth,
            "model_answer": answer,
            "correct": is_correct,
            "time": end_time - start_time,
            "tokens": token_usage['total_tokens'],
            "response": response  # Keep full response for analysis
        }
        results.append(result)
        
        # Update counters
        if is_correct:
            total_correct += 1
        total_tokens += token_usage['total_tokens']
        
        # Print result for this question
        print(f"Ground truth: {ground_truth}")
        print(f"Model answer: {answer}")
        print(f"Correct: {'Yes' if is_correct else 'No'}")
        print(f"Tokens used: {token_usage['total_tokens']}")
    
    # Calculate accuracy
    accuracy = total_correct / len(questions) if questions else 0
    
    # Create summary
    summary = {
        "total_questions": len(questions),
        "correct": total_correct,
        "accuracy": accuracy,
        "total_tokens": total_tokens,
        "average_tokens_per_question": total_tokens / len(questions) if questions else 0
    }
    
    # Create timestamp and run ID
    timestamp = datetime.now().isoformat()
    run_id = f"baseline_aime_same_{int(time.time())}"
    
    # Prepare output
    output = {
        "run_id": run_id,
        "timestamp": timestamp,
        "benchmark": "AIME",
        "model": api_config['model_name'],
        "evaluation_type": "baseline_same_questions",
        "summary": summary,
        "results": results
    }
    
    return output

def main():
    parser = argparse.ArgumentParser(description='Run baseline evaluation on same AIME questions from previous run')
    parser.add_argument('--result-file', type=str, required=True,
                        help='Previous result file to extract questions from')
    parser.add_argument('--max-tokens', type=int, default=9000,
                        help='Maximum tokens per response (default: 9000)')
    parser.add_argument('--results-dir', type=str, default='./results',
                        help='Directory to save results')
    parser.add_argument('--api-key', type=str, default=None,
                        help='API key for the model (or use API_KEY env var)')
    parser.add_argument('--base-url', type=str, default=None,
                        help='Base URL for the API (or use API_BASE_URL env var)')
    parser.add_argument('--model', type=str, default=None,
                        help='Model name to use (or use MODEL_NAME env var)')
    
    args = parser.parse_args()
    
    # Load API config
    api_config = {
        "api_key": args.api_key or os.environ.get("API_KEY"),
        "base_url": args.base_url or os.environ.get("API_BASE_URL"),
        "model_name": args.model or os.environ.get("MODEL_NAME", "deepseek-chat")
    }
    
    if not api_config["api_key"]:
        print("Error: API key not provided. Use --api-key or set API_KEY environment variable.")
        return
        
    if not api_config["base_url"]:
        print("Error: Base URL not provided. Use --base-url or set API_BASE_URL environment variable.")
        return
    
    # Extract questions from previous result
    try:
        questions = extract_questions_from_result(args.result_file)
        print(f"Extracted {len(questions)} questions from {args.result_file}")
    except Exception as e:
        print(f"Error extracting questions from result file: {e}")
        return
    
    # Run evaluation
    try:
        output = run_baseline_on_questions(
            questions=questions,
            api_config=api_config,
            max_tokens=args.max_tokens
        )
        
        # Save results
        os.makedirs(args.results_dir, exist_ok=True)
        results_path = os.path.join(args.results_dir, f"result_{output['run_id']}.json")
        
        with open(results_path, 'w') as f:
            json.dump(output, f, indent=2)
        
        # Print summary
        print("\n--- BASELINE EVALUATION SUMMARY ---")
        print(f"Total questions: {output['summary']['total_questions']}")
        print(f"Correct answers: {output['summary']['correct']}")
        print(f"Accuracy: {output['summary']['accuracy']:.2%}")
        print(f"Total tokens used: {output['summary']['total_tokens']}")
        print(f"Average tokens per question: {output['summary']['average_tokens_per_question']:.1f}")
        print(f"Results saved to: {results_path}")
        
    except Exception as e:
        print(f"Error during evaluation: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()