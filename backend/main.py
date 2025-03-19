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
            
            # Send any existing messages that haven't been sent yet
            simulated_messages = [
                msg for msg in debate['simulatedMessages'] 
                if msg['id'] not in sent_message_ids and msg['role'] != 'System'  # Skip system messages in initial load
            ]
            dual_agent_messages = [
                msg for msg in debate['dualAgentMessages'] 
                if msg['id'] not in sent_message_ids and msg['role'] != 'System'  # Skip system messages in initial load
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
                        if msg['id'] not in sent_message_ids and msg['role'] != 'System'
                    ]
                    new_dual_agent_messages = [
                        msg for msg in debate['dualAgentMessages'] 
                        if msg['id'] not in sent_message_ids and msg['role'] != 'System'
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

if __name__ == "__main__":
    import uvicorn
    # Get port from environment variable or use default
    port = int(os.getenv("PORT", 5001))
    uvicorn.run(app, host="0.0.0.0", port=port)