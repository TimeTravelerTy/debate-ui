from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
import asyncio
from asyncio import run_coroutine_threadsafe
import uuid
import time
import os
import sys
from threading import Thread
import json
from dotenv import load_dotenv

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
    user_message_sim = {
        'id': str(uuid.uuid4()),
        'type': 'simulated',
        'role': 'User',
        'content': request.problem,
        'timestamp': time.time()
    }
    
    user_message_dual = {
        'id': str(uuid.uuid4()),
        'type': 'dual',
        'role': 'User',
        'content': request.problem,
        'timestamp': time.time()
    }
    
    active_debates[debate_id]['simulatedMessages'].append(user_message_sim)
    active_debates[debate_id]['dualAgentMessages'].append(user_message_dual)
    
    # Create a message queue for this debate
    message_queues[debate_id] = asyncio.Queue()
    
    # Start the debate process in the background
    background_tasks.add_task(
        run_debate, 
        debate_id=debate_id, 
        problem=request.problem, 
        strategy_name=request.strategy
    )
    
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

@app.get("/api/stream/{debate_id}")
async def stream_messages(debate_id: str):
    """Server-Sent Events (SSE) endpoint"""
    if debate_id not in active_debates:
        raise HTTPException(status_code=404, detail="Debate not found")
    
    if debate_id not in message_queues:
        message_queues[debate_id] = asyncio.Queue()
    
    queue = message_queues[debate_id]
    
    async def event_generator():
        try:
            # Send initial state
            debate = active_debates[debate_id]
            yield f"data: {json.dumps({'messages': [], 'inProgress': debate['inProgress']})}\n\n"
            
            # Keep track of messages we've already sent
            sent_message_ids = set()
            
            # Send any existing messages that haven't been sent yet
            simulated_messages = [
                msg for msg in debate['simulatedMessages'] 
                if msg['id'] not in sent_message_ids
            ]
            dual_agent_messages = [
                msg for msg in debate['dualAgentMessages'] 
                if msg['id'] not in sent_message_ids
            ]
            
            if simulated_messages or dual_agent_messages:
                for msg in simulated_messages + dual_agent_messages:
                    sent_message_ids.add(msg['id'])
                
                yield f"data: {json.dumps({'messages': simulated_messages + dual_agent_messages, 'inProgress': debate['inProgress']})}\n\n"
            
            # Continue streaming updates while debate is in progress
            while debate['inProgress'] or not queue.empty():
                try:
                    # Wait for new messages with timeout
                    message = await asyncio.wait_for(queue.get(), timeout=1.0)
                    yield f"data: {json.dumps(message)}\n\n"
                except asyncio.TimeoutError:
                    # Send a keep-alive ping if no new messages
                    yield f"data: {json.dumps({'ping': True})}\n\n"
                    
                    # Check if any new messages appeared that weren't through the queue
                    new_simulated_messages = [
                        msg for msg in debate['simulatedMessages'] 
                        if msg['id'] not in sent_message_ids
                    ]
                    new_dual_agent_messages = [
                        msg for msg in debate['dualAgentMessages'] 
                        if msg['id'] not in sent_message_ids
                    ]
                    
                    if new_simulated_messages or new_dual_agent_messages:
                        for msg in new_simulated_messages + new_dual_agent_messages:
                            sent_message_ids.add(msg['id'])
                        
                        yield f"data: {json.dumps({'messages': new_simulated_messages + new_dual_agent_messages, 'inProgress': debate['inProgress']})}\n\n"
        
        except Exception as e:
            print(f"Error in SSE generator: {e}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
            
    # Use a more robust SSE response implementation
    return EventSourceResponse(event_generator())

async def run_debate(debate_id: str, problem: str, strategy_name: str):
    """Run the debate process in the background"""
    try:
        # Configure API using environment variables - fallback to hardcoded values that work in pilot test
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
        
        # Create a special system prompt for the simulated debate
        simulated_system_prompt = (
            "You are a helpful assistant who will simulate a debate between two agents—Agent A and Agent B—who are "
            "discussing and challenging each other's reasoning about the problem. For each turn, you will "
            "generate only the argument or counterargument content, without including any role labels "
            "(those will be provided externally). Your responses should be concise and focus on "
            "logical reasoning. In your debate, Agent A should take the position described as: "
            f"\"{system_prompt_a['content']}\", while Agent B should act as: "
            f"\"{system_prompt_b['content']}\". "
            "At the end of the debate, conclude with a final statement that starts with "
            "'Final Answer:' summarizing the agreed solution."
        )
        
        # Add system messages
        await add_message(debate_id, 'System', simulated_system_prompt, 'simulated')
        await add_message(debate_id, 'System', system_prompt_a['content'], 'dual')
        await add_message(debate_id, 'System', system_prompt_b['content'], 'dual')
        
        # Run simulated debate and dual agent debate concurrently
        # We need to run these in threads because the agent framework is synchronous
        # but we want to handle their messages asynchronously
        
        # Create threads
        sim_thread = Thread(target=run_simulated_debate_thread, args=(debate_id, framework, problem))
        dual_thread = Thread(target=run_dual_agent_debate_thread, args=(debate_id, framework, problem))
        
        # Start threads
        sim_thread.start()
        dual_thread.start()
        
        # Wait for threads to complete (this is non-blocking because we're already in a background task)
        sim_thread.join()
        dual_thread.join()
        
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

def run_simulated_debate_thread(debate_id, framework, problem):
    try:
        sim_results = framework.run_simulation(problem)
        for message in sim_results:
            role = 'System'
            content = message['content']
            if content.startswith('Agent A:'):
                role = 'Agent A'
                content = content[len('Agent A:'):].strip()
            elif content.startswith('Agent B:'):
                role = 'Agent B'
                content = content[len('Agent B:'):].strip()
            else:
                role = 'System'

            run_coroutine_threadsafe(
                add_message(debate_id, role, content, 'simulated'),
                MAIN_LOOP
            )
            time.sleep(1.5)
    except Exception as e:
        print(f"Error in simulated debate: {e}")

def run_dual_agent_debate_thread(debate_id, framework, problem):
    try:
        dual_results = framework.run_dual_agent(problem)
        for message in dual_results:
            if message['role'] == 'user':
                continue
            elif message['role'] == 'assistant':
                content = message['content']
                if content.startswith('Agent A:'):
                    role = 'Agent A'
                    content = content[len('Agent A:'):].strip()
                elif content.startswith('Agent B:'):
                    role = 'Agent B'
                    content = content[len('Agent B:'):].strip()
                else:
                    role = 'System'
                run_coroutine_threadsafe(add_message(debate_id, role, content, 'dual'), MAIN_LOOP)
                time.sleep(2)
            else:
                run_coroutine_threadsafe(add_message(debate_id, 'System', message['content'], 'dual'), MAIN_LOOP)
                time.sleep(0.5)
    except Exception as e:
        print(f"Error in dual agent debate: {e}")
        
async def add_message(debate_id, role, content, message_type):
    """Add a message to the debate and notify listeners"""
    if debate_id not in active_debates:
        return
        
    message = {
        'id': str(uuid.uuid4()),
        'type': message_type,
        'role': role,
        'content': content,
        'timestamp': time.time()
    }
    
    print(f"Adding message: {message_type} - {role} - {content[:50]}...")
    
    if message_type == 'simulated':
        active_debates[debate_id]['simulatedMessages'].append(message)
    else:  # dual
        active_debates[debate_id]['dualAgentMessages'].append(message)
    
    # Send update to the message queue
    if debate_id in message_queues:
        queue = message_queues[debate_id]
        await queue.put({'messages': [message], 'inProgress': True})

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

if __name__ == "__main__":
    import uvicorn
    # Get port from environment variable or use default
    port = int(os.getenv("PORT", 5001))
    uvicorn.run(app, host="0.0.0.0", port=port)