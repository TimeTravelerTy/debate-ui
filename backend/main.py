from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
import asyncio
import traceback
import uuid
import time
import os
import sys
from threading import Thread
import json
from dotenv import load_dotenv
from agent.client import APIClient
from datetime import datetime
from evaluation.core import EvaluationManager
from evaluation.benchmarks.simple_bench import SimpleBenchmark

# Capture the main event loop at startup
MAIN_LOOP = asyncio.get_event_loop()

# Load environment variables
load_dotenv()

# Add parent directory to Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import agent framework modules
try:
    from agent.framework import AgentFramework
    from strategies.debate import DebateStrategy
    from strategies.cooperative import CooperativeStrategy
    from strategies.teacher_student import TeacherStudentStrategy
except ImportError:
    print("Error: Unable to import agent framework modules")
    raise

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this to your frontend origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store active debates
active_debates = {}

# Request models
class DebateRequest(BaseModel):
    problem: str
    strategy: str = "debate"

class MessageResponse(BaseModel):
    messages: List[Dict[str, Any]]
    in_progress: bool

# Message queue for each debate
message_queues = {}

@app.post("/api/debate")
async def start_debate(request: DebateRequest, background_tasks: BackgroundTasks):
    # Create debate ID
    debate_id = str(uuid.uuid4())
    
    # Initialize the debate in storage
    active_debates[debate_id] = {
        'id': debate_id,
        'problem': request.problem,
        'strategy': request.strategy,
        'simulatedMessages': [],
        'dualAgentMessages': [],
        'inProgress': True,
        'startTime': time.time()
    }
    
    # Add the user's question as the first message in both debates
    # BUT marked as "type":"initial" which the frontend will use to avoid duplication
    user_message_sim = {
        'id': str(uuid.uuid4()),
        'type': 'initial',  # Changed from 'simulated' to 'initial'
        'role': 'User',
        'content': request.problem,
        'timestamp': time.time()
    }
    
    user_message_dual = {
        'id': str(uuid.uuid4()),
        'type': 'initial',  # Changed from 'dual' to 'initial'
        'role': 'User',
        'content': request.problem,
        'timestamp': time.time()
    }
    
    active_debates[debate_id]['simulatedMessages'].append(user_message_sim)
    active_debates[debate_id]['dualAgentMessages'].append(user_message_dual)
    
    # Create a message queue for this debate
    message_queues[debate_id] = asyncio.Queue()
    
    # Start the debate process in the background using asyncio
    background_tasks.add_task(run_debate, debate_id, request.problem, request.strategy)
    
    return {"debateId": debate_id}

@app.get("/api/debate/{debate_id}")
async def get_debate(debate_id: str):
    if debate_id not in active_debates:
        raise HTTPException(status_code=404, detail="Debate not found")
    
    return active_debates[debate_id]

@app.get("/api/messages/{debate_id}")
async def get_messages(debate_id: str, since: float = 0):
    if debate_id not in active_debates:
        raise HTTPException(status_code=404, detail="Debate not found")
    
    # Get messages since a timestamp
    simulated_messages = [
        msg for msg in active_debates[debate_id]['simulatedMessages']
        if msg['timestamp'] > since
    ]
    
    dual_agent_messages = [
        msg for msg in active_debates[debate_id]['dualAgentMessages']
        if msg['timestamp'] > since
    ]
    
    return {
        'messages': simulated_messages + dual_agent_messages,
        'inProgress': active_debates[debate_id]['inProgress']
    }

@app.get("/api/stream")
async def stream_messages_by_query(debateId: str):
    """Server-Sent Events (SSE) endpoint using query parameter"""
    print(f"SSE connection requested for debate {debateId} via query parameter")
    return await stream_messages(debateId)

@app.get("/api/stream/{debate_id}")
async def stream_messages(debate_id: str):
    """Server-Sent Events (SSE) endpoint"""
    print(f"SSE connection requested for debate {debate_id}")
    
    if debate_id not in active_debates:
        raise HTTPException(status_code=404, detail="Debate not found")
    
    if debate_id not in message_queues:
        print(f"Creating new message queue for debate {debate_id}")
        message_queues[debate_id] = asyncio.Queue()
    
    queue = message_queues[debate_id]
    
    async def event_generator():
        try:
            # Send initial state
            debate = active_debates[debate_id]
            print(f"SSE: Sending initial state for debate {debate_id}")
            yield f"data: {json.dumps({'messages': [], 'inProgress': debate['inProgress']})}\n\n"
            
            # Keep track of messages we've already sent
            sent_message_ids = set()
            
            # Send any existing messages that haven't been sent yet, EXCLUDING User messages
            # since the frontend will handle those
            simulated_messages = [
                msg for msg in debate['simulatedMessages'] 
                if (msg['id'] not in sent_message_ids and 
                    msg['role'] != 'System' and 
                    msg['role'] != 'User')  # Skip system and user messages
            ]
            dual_agent_messages = [
                msg for msg in debate['dualAgentMessages'] 
                if (msg['id'] not in sent_message_ids and 
                    msg['role'] != 'System' and 
                    msg['role'] != 'User')  # Skip system and user messages
            ]
            
            if simulated_messages or dual_agent_messages:
                print(f"SSE: Sending {len(simulated_messages)} simulated and {len(dual_agent_messages)} dual messages initially")
                for msg in simulated_messages + dual_agent_messages:
                    sent_message_ids.add(msg['id'])
                
                yield f"data: {json.dumps({'messages': simulated_messages + dual_agent_messages, 'inProgress': debate['inProgress']})}\n\n"
            
            # Continue streaming updates while debate is in progress
            ping_count = 0
            while debate['inProgress'] or not queue.empty():
                try:
                    # Wait for new messages with timeout
                    print(f"SSE: Waiting for messages in queue for debate {debate_id}")
                    message = await asyncio.wait_for(queue.get(), timeout=2.0)
                    print(f"SSE: Got message from queue: {message}")
                    
                    # Track sent message IDs if this is a message update
                    if 'messages' in message and message['messages']:
                        # Filter out user messages
                        message['messages'] = [msg for msg in message['messages'] if msg['role'] != 'User']
                        
                        if not message['messages']:
                            # Skip sending if there are no messages after filtering
                            continue
                            
                        for msg in message['messages']:
                            if 'id' in msg:
                                sent_message_ids.add(msg['id'])
                    
                    # Send message to client
                    yield f"data: {json.dumps(message)}\n\n"
                    ping_count = 0
                except asyncio.TimeoutError:
                    # Send a keep-alive ping if no new messages
                    ping_count += 1
                    print(f"SSE: Sending ping #{ping_count} for debate {debate_id}")
                    yield f"data: {json.dumps({'ping': True})}\n\n"
                    
                    # Check if any new messages appeared that weren't through the queue
                    new_simulated_messages = [
                        msg for msg in debate['simulatedMessages'] 
                        if (msg['id'] not in sent_message_ids and 
                            msg['role'] != 'System' and 
                            msg['role'] != 'User')  # Skip system and user messages
                    ]
                    new_dual_agent_messages = [
                        msg for msg in debate['dualAgentMessages'] 
                        if (msg['id'] not in sent_message_ids and 
                            msg['role'] != 'System' and 
                            msg['role'] != 'User')  # Skip system and user messages
                    ]
                    
                    if new_simulated_messages or new_dual_agent_messages:
                        print(f"SSE: Found {len(new_simulated_messages)} new simulated and {len(new_dual_agent_messages)} new dual messages")
                        for msg in new_simulated_messages + new_dual_agent_messages:
                            sent_message_ids.add(msg['id'])
                        
                        yield f"data: {json.dumps({'messages': new_simulated_messages + new_dual_agent_messages, 'inProgress': debate['inProgress']})}\n\n"
                    
                    # If we've sent too many pings without activity, check if the debate is actually still running
                    if ping_count > 10 and not debate['inProgress']:
                        print(f"SSE: Ending connection for completed debate {debate_id} after {ping_count} pings")
                        break
        
        except Exception as e:
            print(f"Error in SSE generator: {e}")
            traceback.print_exc()
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
            
    # Use EventSourceResponse for SSE
    return EventSourceResponse(event_generator())

async def run_debate(debate_id: str, problem: str, strategy_name: str):
    """Run the debate process in the background using asyncio"""
    try:
        # Configure API using environment variables
        api_config = {
            "api_key": os.getenv("API_KEY"),
            "base_url": os.getenv("API_BASE_URL"),
            "model_name": os.getenv("MODEL_NAME")
        }
        
        print(f"Using API configuration: {api_config['base_url']} with model {api_config['model_name']}")
        
        # Create strategy based on name
        if strategy_name == 'debate':
            strategy = DebateStrategy()
        elif strategy_name == 'cooperative':
            strategy = CooperativeStrategy()
        elif strategy_name == 'teacher-student':
            strategy = TeacherStudentStrategy()
        else:
            strategy = DebateStrategy()  # Default
        
        # Initialize framework
        framework = AgentFramework(api_config, strategy)
        
        # Get system prompts from strategy
        system_prompt_a = strategy.get_system_prompt_a()
        system_prompt_b = strategy.get_system_prompt_b()
        
        # Add system messages for the dual agent approach
        await add_message(debate_id, 'System', system_prompt_a['content'], 'dual')
        await add_message(debate_id, 'System', system_prompt_b['content'], 'dual')
        
        # Define callback functions to handle messages in real-time
        async def simulated_callback(role, content, msg_type):
            await add_message(debate_id, role, content, 'simulated')
            
        async def dual_agent_callback(role, content, msg_type):
            await add_message(debate_id, role, content, 'dual')
        
        # Run simulated debate and dual agent debate concurrently using asyncio
        sim_task = asyncio.create_task(
            framework.run_simulation(problem, simulated_callback)
        )
        
        dual_task = asyncio.create_task(
            framework.run_dual_agent(problem, dual_agent_callback)
        )
        
        # Wait for both tasks to complete
        await asyncio.gather(sim_task, dual_task)
        
        # Mark as complete
        if debate_id in active_debates:
            active_debates[debate_id]['inProgress'] = False
            
            # Send final update to clients
            if debate_id in message_queues:
                queue = message_queues[debate_id]
                await queue.put({
                    'inProgress': False,
                    'messages': []
                })
            
    except Exception as e:
        print(f"Error in debate: {e}")
        traceback.print_exc()
        if debate_id in active_debates:
            active_debates[debate_id]['inProgress'] = False
            active_debates[debate_id]['error'] = str(e)
            
            # Send error to clients
            if debate_id in message_queues:
                queue = message_queues[debate_id]
                await queue.put({
                    'inProgress': False,
                    'error': str(e),
                    'messages': []
                })

async def add_message(debate_id, role, content, message_type):
    """Add a message to the debate and notify listeners"""
    if debate_id not in active_debates:
        print(f"Warning: Debate {debate_id} not found")
        return
        
    message = {
        'id': str(uuid.uuid4()),
        'type': message_type,
        'role': role,
        'content': content,
        'timestamp': time.time()
    }
    
    print(f"Adding message to {message_type} debate - {role}: {content[:50]}...")
    
    if message_type == 'simulated':
        active_debates[debate_id]['simulatedMessages'].append(message)
    else:  # dual
        active_debates[debate_id]['dualAgentMessages'].append(message)
    
    # Only send non-User messages via SSE since User messages are handled by the frontend
    if role != 'User':
        # Send update to the message queue
        if debate_id in message_queues:
            queue = message_queues[debate_id]
            print(f"Queueing message for SSE: {role} - {message_type}")
            await queue.put({'messages': [message], 'inProgress': True})
        else:
            print(f"Warning: No message queue found for debate {debate_id}")

# Define EventSourceResponse for SSE
from starlette.responses import Response
from typing import AsyncGenerator, Callable, Any

class EventSourceResponse(Response):
    media_type = "text/event-stream"

    def __init__(
        self,
        content: AsyncGenerator[str, Any],
        status_code: int = 200,
        headers: dict = None,
        media_type: str = None,
    ):
        # Pass None for content so that no Content-Length is computed
        super().__init__(content=None, status_code=status_code, headers=headers, media_type=media_type)
        self.body_iterator = content
        # Set the necessary SSE headers
        self.headers["Cache-Control"] = "no-cache"
        self.headers["Connection"] = "keep-alive"
        if "content-length" in self.headers:
            del self.headers["content-length"]

    async def __call__(self, scope, receive, send):
        await send(
            {
                "type": "http.response.start",
                "status": self.status_code,
                "headers": [
                    [k.encode(), v.encode()] for k, v in self.headers.items()
                ],
            }
        )
        try:
            async for chunk in self.body_iterator:
                if not chunk:
                    continue
                await send(
                    {
                        "type": "http.response.body",
                        "body": chunk.encode("utf-8"),
                        "more_body": True,
                    }
                )
            await send({"type": "http.response.body", "body": b"", "more_body": False})
        except Exception as e:
            print(f"Error in SSE response: {e}")
            await send({"type": "http.response.body", "body": b"", "more_body": False})

# Evaluation request model
class EvaluationRequest(BaseModel):
    benchmark_id: str
    strategy_id: str
    max_questions: Optional[int] = None

# Set up results directory
RESULTS_DIR = os.environ.get("RESULTS_DIR", "./results")
BENCHMARKS_DIR = os.environ.get("BENCHMARKS_DIR", "./data/benchmarks")

# Ensure directories exist
os.makedirs(RESULTS_DIR, exist_ok=True)
os.makedirs(BENCHMARKS_DIR, exist_ok=True)

# Track active evaluations
active_evaluations = {}

# Function to load benchmark
def load_benchmark(benchmark_id: str):
    """Load a benchmark by ID"""
    if benchmark_id == "simple":
        json_path = os.path.join(BENCHMARKS_DIR, "simple_bench/questions.json")
        csv_path = os.path.join(BENCHMARKS_DIR, "simple_bench/questions.csv")
        return SimpleBenchmark(json_path, csv_path)
    else:
        raise ValueError(f"Unknown benchmark: {benchmark_id}")

# Function to run evaluation in background
async def run_evaluation_task(evaluation_id: str, benchmark_id: str, strategy_id: str, max_questions: Optional[int] = None):
    """Run evaluation in background"""
    try:
        # Load benchmark
        benchmark = load_benchmark(benchmark_id)
        
        # Load API config
        api_config = {
            "api_key": os.environ.get("API_KEY"),
            "base_url": os.environ.get("API_BASE_URL"),
            "model_name": os.environ.get("MODEL_NAME", "deepseek-chat")
        }
        
        # Initialize API client
        client = APIClient(api_config)
        
        # Initialize strategies
        strategies = {
            "debate": DebateStrategy(),
            "cooperative": CooperativeStrategy(),
            "teacher-student": TeacherStudentStrategy()
        }
        
        # Get the selected strategy
        strategy = strategies[strategy_id]
        
        # Initialize framework with client and strategy
        framework = AgentFramework(api_config, strategy)
        
        # Initialize evaluation manager
        manager = EvaluationManager(benchmark, framework, strategies, RESULTS_DIR)
        
        # Update evaluation status
        active_evaluations[evaluation_id]["status"] = "running"
        
        # Run evaluation
        run_id, results = await manager.run_evaluation(strategy_id, max_questions)
        
        # Update evaluation status
        active_evaluations[evaluation_id]["status"] = "completed"
        active_evaluations[evaluation_id]["run_id"] = run_id
        active_evaluations[evaluation_id]["results"] = results
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        # Update evaluation status with error
        active_evaluations[evaluation_id]["status"] = "error"
        active_evaluations[evaluation_id]["error"] = str(e)

# Evaluation endpoints
@app.post("/api/evaluation/run")
async def start_evaluation(request: EvaluationRequest, background_tasks: BackgroundTasks):
    """Start a benchmark evaluation"""
    try:
        # Validate benchmark ID
        try:
            load_benchmark(request.benchmark_id)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        
        # Validate strategy ID
        valid_strategies = ["debate", "cooperative", "teacher-student"]
        if request.strategy_id not in valid_strategies:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid strategy: {request.strategy_id}. Valid options: {', '.join(valid_strategies)}"
            )
        
        # Create evaluation ID
        evaluation_id = str(uuid.uuid4())
        
        # Create initial evaluation record
        active_evaluations[evaluation_id] = {
            "id": evaluation_id,
            "benchmark_id": request.benchmark_id,
            "strategy_id": request.strategy_id,
            "max_questions": request.max_questions,
            "status": "pending",
            "created_at": datetime.now().isoformat(),
            "progress": {"current": 0, "total": 0}
        }
        
        # Start evaluation in background
        background_tasks.add_task(
            run_evaluation_task,
            evaluation_id,
            request.benchmark_id,
            request.strategy_id,
            request.max_questions
        )
        
        return {"evaluation_id": evaluation_id}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/evaluation/status/{evaluation_id}")
async def get_evaluation_status(evaluation_id: str):
    """Get status of a running evaluation"""
    if evaluation_id not in active_evaluations:
        raise HTTPException(status_code=404, detail="Evaluation not found")
    
    return active_evaluations[evaluation_id]

@app.get("/api/evaluation/runs")
async def get_evaluation_runs():
    """Get list of available evaluation runs"""
    try:
        if not os.path.exists(RESULTS_DIR):
            return {"runs": []}
            
        run_files = [f for f in os.listdir(RESULTS_DIR) if f.startswith("result_")]
        
        runs = []
        for file in run_files:
            path = os.path.join(RESULTS_DIR, file)
            try:
                with open(path, 'r') as f:
                    data = json.load(f)
                    runs.append({
                        "id": data.get("run_id", "unknown"),
                        "strategy": data.get("strategy", "unknown"),
                        "timestamp": data.get("timestamp", "unknown"),
                        "benchmark": data.get("benchmark", "unknown")
                    })
            except Exception as e:
                print(f"Error loading run file {file}: {e}")
        
        # Sort runs by timestamp (newest first)
        runs.sort(key=lambda x: x["timestamp"], reverse=True)
        
        return {"runs": runs}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/evaluation/runs/{run_id}")
async def get_evaluation_run(run_id: str):
    """Get details of a specific evaluation run"""
    try:
        file_path = os.path.join(RESULTS_DIR, f"result_{run_id}.json")
        
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="Run not found")
        
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        return data
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/logs/{log_id}")
async def get_conversation_log(log_id: str):
    """Get a specific conversation log"""
    try:
        file_path = os.path.join(RESULTS_DIR, f"log_{log_id}.json")
        
        if not os.path.exists(file_path):
            # For backward compatibility, try the old format with _sim and _dual suffixes
            sim_file_path = os.path.join(RESULTS_DIR, f"log_{log_id}_sim.json")
            dual_file_path = os.path.join(RESULTS_DIR, f"log_{log_id}_dual.json")
            
            # If we find the old format files, merge them into a consolidated format
            if os.path.exists(sim_file_path) and os.path.exists(dual_file_path):
                with open(sim_file_path, 'r') as f:
                    sim_data = json.load(f)
                
                with open(dual_file_path, 'r') as f:
                    dual_data = json.load(f)
                
                # Create a consolidated response
                consolidated_data = {
                    "question_id": sim_data.get("question_id"),
                    "question": sim_data.get("question"),
                    "ground_truth": sim_data.get("ground_truth"),
                    "strategy": sim_data.get("strategy"),
                    "benchmark": sim_data.get("benchmark", "Unknown"),  # Add a default
                    "simulated_messages": sim_data.get("simulated_messages", []),
                    "dual_messages": dual_data.get("dual_messages", [])
                }
                
                return consolidated_data
            else:
                raise HTTPException(status_code=404, detail="Log not found")
        
        # New consolidated format
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        # Ensure all required fields are present
        if "simulated_messages" not in data or "dual_messages" not in data:
            raise HTTPException(status_code=500, detail="Invalid log format")
        
        return data
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
if __name__ == "__main__":
    import uvicorn
    # Get port from environment variable or use default
    port = int(os.getenv("PORT", 5001))
    uvicorn.run(app, host="0.0.0.0", port=port)