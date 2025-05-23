from typing import Dict, List, Any, Optional
import time
import re

def format_message(role: str, text: str) -> str:
    """Format a message with role label"""
    return f"{role}: {text}\n"

def extract_answer_livebench(content: str) -> Optional[str]:
    """
    Extract the proper answer from message content, handling various formats from LiveBench.
    
    Args:
        content: Message content
    
    Returns:
        Extracted answer or None if not found
    """
    # Look for <solution>...</solution> format after "Final Answer" or "Answer"
    final_solution_match = re.search(r'final answer:\s+<solution>(.*?)</solution>', content, re.IGNORECASE | re.DOTALL)
    if final_solution_match:
        return final_solution_match.group(1).strip()
    
    solution_match = re.search(r'answer:\s+<solution>(.*?)</solution>', content, re.IGNORECASE | re.DOTALL)
    if solution_match:
        return solution_match.group(1).strip()
    
    # General <solution> tag anywhere
    general_solution_match = re.search(r'<solution>(.*?)</solution>', content, re.IGNORECASE | re.DOTALL)
    if general_solution_match:
        return general_solution_match.group(1).strip()
    
    # Final Answer with bold (support 2-5 asterisks)
    final_bold_match = re.search(r'final answer:\s+\*{2,5}(.*?)\*{2,5}', content, re.IGNORECASE)
    if final_bold_match:
        return final_bold_match.group(1).strip()
        
    # Answer with bold (support 2-5 asterisks)
    bold_match = re.search(r'answer:\s+\*{2,5}(.*?)\*{2,5}', content, re.IGNORECASE)
    if bold_match:
        return bold_match.group(1).strip()
    
    # Final Answer without formatting
    final_plain_match = re.search(r'final answer:\s+([\w\d\s,.;]+)', content, re.IGNORECASE)
    if final_plain_match:
        return final_plain_match.group(1).strip()
    
    # Answer without formatting
    plain_match = re.search(r'answer:\s+([\w\d\s,.;]+)', content, re.IGNORECASE)
    if plain_match:
        # Make sure this is actually the answer, not just a mention of "answer"
        answer_text = plain_match.group(1).strip()
        # Only accept if it's reasonably short and looks like an answer
        if len(answer_text.split()) <= 15:
            return answer_text
    
    # Handle numbered/comma-separated answers in solution-like format
    # This catches answers like "1, 2, 3, 4" or "yes, no, yes"
    list_pattern_match = re.search(r'answer:\s+((?:[\w-]+(?:,\s*[\w-]+)+))', content, re.IGNORECASE)
    if list_pattern_match:
        return list_pattern_match.group(1).strip()
    
    # bolded numbers
    bolded_numbers_match = re.search(r'\*{2,5}([\d\s,.;]+)\*{2,5}', content, re.IGNORECASE)
    if bolded_numbers_match:
        return bolded_numbers_match.group(1).strip()
    
    return None

def extract_answer(text: str, answer_format: str = "letter") -> Optional[str]:
    """
    Extract answer from text based on expected format
    
    Args:
        text: Text to extract answer from
        answer_format: Expected format ('letter', 'integer', 'word', etc.)
    """
    # Look for Final Answer: X pattern
    match = re.search(r'Final Answer:\s*([^\n]+)', text, re.IGNORECASE)
    if not match:
        # Fallback to Answer: X
        match = re.search(r'Answer:\s*([^\n]+)', text, re.IGNORECASE)
    
    if not match:
        return None
        
    answer = match.group(1).strip()
    
    # Validate format
    if answer_format == "letter":
        # Extract just the letter if there's extra text
        letter_match = re.search(r'^\*{0,2}([A-Z])\*{0,2}', answer, re.IGNORECASE)
        if letter_match:
            return letter_match.group(1).upper()
    elif answer_format == "integer":
        # Check for work-in-progress indicators
        if re.search(r'Answer:\s*\[(working|calculating|in progress)\]', answer, re.IGNORECASE):
            return None  # Don't count as a real answer
        # Extract just the integer
        int_match = re.search(r'^\*{0,2}(-?\d+)\*{0,2}', answer)
        if int_match:
            return int_match.group(1)
    elif answer_format == "word":
        # Extract just the first word
        word_match = re.search(r'^\*{0,2}([a-zA-Z]+)\*{0,2}', answer)
        if word_match:
            return word_match.group(1)
    else:
        # Return as-is for unknown formats
        return answer
    
    return None
    

def parse_agent_message(message: Dict[str, str]) -> Dict[str, Any]:
    """
    Parse an agent message to extract the role and content
    
    Args:
        message: Message dictionary with role and content keys
        
    Returns:
        Dictionary with extracted role and content
    """
    result = {
        "original_role": message["role"],
        "original_content": message["content"],
    }
    
    # If message is from assistant or user, try to extract agent role
    if message["role"] in ["assistant", "user"]:
        content = message["content"]
        
        # Try to match "Agent X: content"
        match = re.match(r"^(Agent [AB]):\s*(.*)", content, re.DOTALL)
        if match:
            result["role"] = match.group(1)
            result["content"] = match.group(2).strip()
        else:
            # No explicit agent role, use original
            result["role"] = message["role"]
            result["content"] = content
    else:
        # For system messages, keep as is
        result["role"] = message["role"]
        result["content"] = message["content"]
        
    return result
    
def measure_response_time(func):
    """Decorator to measure response time of a function"""
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        elapsed_time = end_time - start_time
        print(f"Function {func.__name__} took {elapsed_time:.2f} seconds")
        return result
    return wrapper