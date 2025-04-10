'use client';

import React, { useState, useEffect } from 'react';
import { v4 as uuidv4 } from 'uuid';
import { ProblemForm } from '../components/ProblemForm';
import { StrategySelector } from '../components/StrategySelector';
import { DebateArena } from '../components/DebateArena';
import { Toaster, toast } from 'sonner';

// Message type
interface Message {
  id: string;
  role: string;
  content: string;
  timestamp: number;
  type?: string;
}

// Strategy type
interface Strategy {
  id: string;
  name: string;
  description: string;
  agentA: {
    role: string;
    description: string;
  };
  agentB: {
    role: string;
    description: string;
  };
}

// Sample strategies data
const strategies: Strategy[] = [
  {
    id: 'debate',
    name: 'Debate Strategy',
    description: 'A proponent presents arguments while a critic challenges them to find flaws.',
    agentA: {
      role: 'Proponent',
      description: 'Presents a well-structured argument supporting the correct answer.'
    },
    agentB: {
      role: 'Critic',
      description: 'Critically evaluates and challenges the argument presented by Agent A.'
    }
  },
  {
    id: 'cooperative',
    name: 'Cooperative Strategy',
    description: 'Two agents work collaboratively, building on each other\'s ideas.',
    agentA: {
      role: 'Proposer',
      description: 'Proposes initial solutions and approaches to the problem.'
    },
    agentB: {
      role: 'Extender',
      description: 'Builds upon and refines the initial proposals.'
    }
  },
  {
    id: 'teacher-student',
    name: 'Teacher-Student Strategy',
    description: 'An expert guides a learner through the problem-solving process.',
    agentA: {
      role: 'Teacher',
      description: 'Provides expert guidance and corrects misconceptions.'
    },
    agentB: {
      role: 'Student',
      description: 'Asks probing questions and attempts to solve the problem step by step.'
    }
  }
];

export default function Home() {
  const [selectedStrategy, setSelectedStrategy] = useState('debate');
  const [inProgress, setInProgress] = useState(false);
  const [simulatedMessages, setSimulatedMessages] = useState<Message[]>([]);
  const [dualAgentMessages, setDualAgentMessages] = useState<Message[]>([]);
  const [eventSource, setEventSource] = useState<EventSource | null>(null);
  
  // Cleanup event source on unmount
  useEffect(() => {
    return () => {
      if (eventSource) {
        eventSource.close();
      }
    };
  }, [eventSource]);

  const handleStartDebate = async (problem: string) => {
    try {
      // Reset previous messages
      setSimulatedMessages([]);
      setDualAgentMessages([]);
      
      setInProgress(true);
      
      // Close any existing event source
      if (eventSource) {
        eventSource.close();
      }
      
      // Add the user's question as the first message in both debates
      // Do this BEFORE sending the API request to avoid duplication
      const userMessage = {
        id: uuidv4(),
        role: 'User',
        content: problem,
        timestamp: Date.now()
      };
      
      setSimulatedMessages([userMessage]);
      setDualAgentMessages([userMessage]);
      
      // Start debate
      toast.promise(
        async () => {
          const response = await fetch('/api/debate', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({ problem, strategy: selectedStrategy }),
          });
          
          if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Failed to start debate');
          }
          
          const { debateId } = await response.json();
          
          // Create event source for real-time updates
          console.log(`Creating EventSource for debate ${debateId}`);
          const es = new EventSource(`/api/stream?debateId=${debateId}`);
  
          es.onopen = () => {
            console.log("SSE connection opened successfully");
          };
  
          es.onmessage = (event) => {
            console.log("SSE message received:", event.data);
            let data;
            try {
              data = JSON.parse(event.data);
            } catch (error) {
              // If parsing fails, it might be a plain "ping" message
              if (event.data.trim() === "ping") {
                console.log("Received ping");
                return;
              }
              console.error("Error parsing SSE message:", error);
              return;
            }
  
            // If the parsed JSON is a ping, just ignore it
            if (data.ping) {
              console.log("Received ping");
              return;
            }
  
            // Handle error messages sent by the server
            if (data.error) {
              console.error("SSE error:", data.error);
              toast.error(`Error: ${data.error}`);
              return;
            }
  
            // Process new messages
            if (data.messages && data.messages.length > 0) {
              console.log(`Received ${data.messages.length} messages:`, data.messages);
                interface MessageData {
                id: string;
                role: string;
                content: string;
                timestamp: number;
                type: 'simulated' | 'dual' | 'initial';
                }
  
                interface MessageUpdate {
                messages: MessageData[];
                inProgress?: boolean;
                error?: string;
                }
  
                (data.messages as MessageData[]).forEach((msg: MessageData) => {
                // Skip user messages from the server since we already added them locally
                if (msg.role === 'User') {
                  console.log("Skipping user message from server:", msg);
                  return;
                }
                  
                if (msg.type === 'simulated' || msg.type === 'initial') {
                  setSimulatedMessages((prev: Message[]) => {
                  // Check if message with this ID already exists
                  if (prev.some((m: Message) => m.id === msg.id)) {
                    console.log("Skipping duplicate simulated message:", msg.id);
                    return prev;
                  }
                  console.log("Adding simulated message:", msg);
                  return [...prev, {
                    id: msg.id,
                    role: msg.role,
                    content: msg.content,
                    timestamp: msg.timestamp
                  }];
                  });
                } else if (msg.type === 'dual') {
                  setDualAgentMessages((prev: Message[]) => {
                  // Check if message with this ID already exists
                  if (prev.some((m: Message) => m.id === msg.id)) {
                    console.log("Skipping duplicate dual message:", msg.id);
                    return prev;
                  }
                  console.log("Adding dual message:", msg);
                  return [...prev, {
                    id: msg.id,
                    role: msg.role,
                    content: msg.content,
                    timestamp: msg.timestamp
                  }];
                  });
                }
                });
            }
            
            // Check if debate is complete
            if (data.inProgress === false) {
              console.log("Debate is complete");
              setInProgress(false);
              es.close();
              setEventSource(null);
            }
          };
  
          es.onerror = (error) => {
            console.error('SSE Error:', error);
            toast.error('Connection to debate stream lost. Please refresh the page.');
            es.close();
            setInProgress(false);
            setEventSource(null);
          };
          
          setEventSource(es);
          return debateId;
        },
        {
          loading: 'Starting debate...',
          success: (debateId) => `Debate started!`,
          error: (err) => `Error: ${err.message}`
        }
      );
    } catch (error) {
      console.error('Failed to start debate:', error);
      setInProgress(false);
      toast.error(`Error: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  };


  return (
    <main className="container mx-auto py-8 px-4">
      <Toaster richColors position="top-center" />
      
      <div className="grid grid-cols-1 gap-6">
        <ProblemForm onSubmit={handleStartDebate} isLoading={inProgress} />
        
        <StrategySelector 
          strategies={strategies} 
          selectedStrategy={selectedStrategy} 
          onStrategyChange={setSelectedStrategy}
        />
        
        <DebateArena 
          simulatedMessages={simulatedMessages} 
          dualAgentMessages={dualAgentMessages}
          inProgress={inProgress}
        />
      </div>
    </main>
  );
}
