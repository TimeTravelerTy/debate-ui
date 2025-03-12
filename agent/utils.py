from typing import Dict, List, Any, Optional
import time
import re

def format_message(role: str, text: str) -> str:
    """Format a message with role label"""
    return f"{role}: {text}\n"

def extract_final_answer(text: str) -> Optional[str]:
    """Extract final answer from text if present"""
    match = re.search(r"Final Answer:\s*(.*?)(?:\n|$)", text, re.DOTALL)
    if match:
        return match.group(1).strip()
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