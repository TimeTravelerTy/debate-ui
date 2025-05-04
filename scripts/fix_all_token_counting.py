#!/usr/bin/env python3
"""
Fix token counting for all result files in the results directory
"""

import sys
import os
import argparse
import json
import glob
from datetime import datetime

# Add the parent directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def recalculate_token_counts(data):
    """Recalculate token counts using completion tokens only"""
    # Initialize counters for completion tokens
    simulated_completion_tokens = 0
    dual_completion_tokens = 0
    
    # Also track prompt tokens for reference
    simulated_prompt_tokens = 0
    dual_prompt_tokens = 0
    
    # Process individual results
    if 'results' in data:
        for result in data['results']:
            if 'simulated' in result and 'tokens' in result['simulated']:
                tokens = result['simulated']['tokens']
                simulated_completion_tokens += tokens.get('completion_tokens', 0)
                simulated_prompt_tokens += tokens.get('prompt_tokens', 0)
            
            if 'dual' in result and 'tokens' in result['dual']:
                tokens = result['dual']['tokens']
                dual_completion_tokens += tokens.get('completion_tokens', 0)
                dual_prompt_tokens += tokens.get('prompt_tokens', 0)
    
    # Update summary with both total and completion-only counts
    if 'summary' in data:
        # For baseline results, all tokens are completion tokens
        if data.get('evaluation_type') == 'baseline' or data.get('evaluation_type') == 'baseline_same_questions':
            if 'total_tokens' in data['summary']:
                data['summary']['completion_token_usage'] = {
                    "total_completion_tokens": data['summary']['total_tokens']
                }
                data['summary']['prompt_token_usage'] = {
                    "total_prompt_tokens": 0
                }
        else:
            # For agent results
            if 'token_usage' in data['summary']:
                # Keep original token counts as "total_token_usage"
                data['summary']['total_token_usage'] = data['summary']['token_usage'].copy()
                
                # Add completion-only token counts
                data['summary']['completion_token_usage'] = {
                    "simulated_completion_tokens": simulated_completion_tokens,
                    "dual_completion_tokens": dual_completion_tokens,
                    "total_completion_tokens": simulated_completion_tokens + dual_completion_tokens
                }
                
                # Add prompt token counts for reference
                data['summary']['prompt_token_usage'] = {
                    "simulated_prompt_tokens": simulated_prompt_tokens,
                    "dual_prompt_tokens": dual_prompt_tokens,
                    "total_prompt_tokens": simulated_prompt_tokens + dual_prompt_tokens
                }
    
    return data

def update_comparison_report(data):
    """Update comparison report with completion token data"""
    # Update each strategy's token counts
    if 'strategies' in data:
        total_completion_tokens = 0
        total_prompt_tokens = 0
        
        for strategy, strategy_data in data['strategies'].items():
            if 'run_id' in strategy_data:
                # Load the individual result file
                result_file = os.path.join(os.path.dirname(data['_file_path']), f"result_{strategy_data['run_id']}.json")
                try:
                    with open(result_file, 'r') as f:
                        result_data = json.load(f)
                    
                    # Check if already has completion tokens
                    if 'summary' in result_data and 'completion_token_usage' in result_data['summary']:
                        # Already processed, use existing data
                        strategy_data['summary']['completion_token_usage'] = result_data['summary']['completion_token_usage']
                        strategy_data['summary']['prompt_token_usage'] = result_data['summary']['prompt_token_usage']
                    else:
                        # Need to recalculate
                        updated_result = recalculate_token_counts(result_data)
                        if 'summary' in updated_result and 'completion_token_usage' in updated_result['summary']:
                            strategy_data['summary']['completion_token_usage'] = updated_result['summary']['completion_token_usage']
                            strategy_data['summary']['prompt_token_usage'] = updated_result['summary']['prompt_token_usage']
                    
                    # Accumulate totals
                    if 'summary' in strategy_data and 'completion_token_usage' in strategy_data['summary']:
                        total_completion_tokens += strategy_data['summary']['completion_token_usage']['total_completion_tokens']
                        total_prompt_tokens += strategy_data['summary']['prompt_token_usage']['total_prompt_tokens']
                        
                except Exception as e:
                    print(f"  Warning: Could not process result file: {result_file} - {e}")
        
        # Add completion token summary to the comparison report
        data['completion_token_usage'] = {
            "total_completion_tokens": total_completion_tokens,
            "total_prompt_tokens": total_prompt_tokens
        }
    
    return data

def process_file(file_path, output_dir, backup_dir, dry_run=False):
    """Process a single file"""
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        # Add file path for reference
        data['_file_path'] = file_path
        
        # Check if already processed
        if 'summary' in data and 'completion_token_usage' in data['summary']:
            print(f"  Already processed, skipping")
            return False
        
        # Determine file type and process accordingly
        if 'strategies' in data and 'questions' in data:
            # This is a comparison report
            print(f"  Processing as comparison report")
            updated_data = update_comparison_report(data)
        else:
            # This is an individual result file
            print(f"  Processing as result file")
            updated_data = recalculate_token_counts(data)
        
        # Remove the temporary file path
        if '_file_path' in updated_data:
            del updated_data['_file_path']
        
        if not dry_run:
            # Create backup
            backup_path = os.path.join(backup_dir, os.path.basename(file_path))
            with open(backup_path, 'w') as f:
                json.dump(data, f, indent=2)
            
            # Save updated file
            output_path = os.path.join(output_dir, os.path.basename(file_path))
            with open(output_path, 'w') as f:
                json.dump(updated_data, f, indent=2)
            
            print(f"  Updated and saved to: {output_path}")
            print(f"  Backup saved to: {backup_path}")
        else:
            print(f"  [Dry run] Would update: {file_path}")
        
        return True
        
    except Exception as e:
        print(f"  Error processing {file_path}: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Fix token counting for all result files')
    parser.add_argument('--results-dir', type=str, default='./results',
                        help='Directory containing result files')
    parser.add_argument('--output-dir', type=str, default=None,
                        help='Output directory (default: same as results-dir)')
    parser.add_argument('--backup-dir', type=str, default=None,
                        help='Backup directory (default: results-dir/backup_TIMESTAMP)')
    parser.add_argument('--pattern', type=str, default='*.json',
                        help='File pattern to match (default: *.json)')
    parser.add_argument('--dry-run', action='store_true',
                        help='Show what would be done without making changes')
    parser.add_argument('--verbose', action='store_true',
                        help='Show detailed information')
    
    args = parser.parse_args()
    
    # Set up directories
    results_dir = args.results_dir
    output_dir = args.output_dir or results_dir
    
    if args.backup_dir:
        backup_dir = args.backup_dir
    else:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_dir = os.path.join(results_dir, f'backup_{timestamp}')
    
    # Create directories if needed
    if not args.dry_run:
        os.makedirs(output_dir, exist_ok=True)
        os.makedirs(backup_dir, exist_ok=True)
    
    # Find all matching files
    pattern = os.path.join(results_dir, args.pattern)
    files = glob.glob(pattern)
    
    # Filter to only result and comparison files
    result_files = []
    comparison_files = []
    
    for file_path in files:
        basename = os.path.basename(file_path)
        if basename.startswith('result_'):
            result_files.append(file_path)
        elif basename.startswith('comparison_'):
            comparison_files.append(file_path)
    
    print(f"Found {len(result_files)} result files and {len(comparison_files)} comparison files")
    
    if args.dry_run:
        print("DRY RUN - No files will be modified")
    
    print(f"\nResults directory: {results_dir}")
    print(f"Output directory: {output_dir}")
    print(f"Backup directory: {backup_dir}")
    print()
    
    # Process result files first
    processed_count = 0
    skipped_count = 0
    
    print("Processing result files...")
    for file_path in result_files:
        print(f"\n{os.path.basename(file_path)}:")
        if process_file(file_path, output_dir, backup_dir, args.dry_run):
            processed_count += 1
        else:
            skipped_count += 1
    
    # Then process comparison files
    print("\nProcessing comparison files...")
    for file_path in comparison_files:
        print(f"\n{os.path.basename(file_path)}:")
        if process_file(file_path, output_dir, backup_dir, args.dry_run):
            processed_count += 1
        else:
            skipped_count += 1
    
    print("\n" + "="*50)
    print(f"Summary:")
    print(f"  Processed: {processed_count} files")
    print(f"  Skipped: {skipped_count} files")
    print(f"  Total: {processed_count + skipped_count} files")
    
    if args.dry_run:
        print("\nThis was a dry run. No files were modified.")
        print("Run without --dry-run to actually update files.")

if __name__ == "__main__":
    main()