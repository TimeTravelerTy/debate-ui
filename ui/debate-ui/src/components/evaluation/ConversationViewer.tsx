import React, { useState, useEffect } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../ui/tabs";
import { Card, CardHeader, CardTitle, CardContent } from "../ui/card";
import { AgentMessage } from '../AgentMessage';
import { EvolutionAnalysisView } from '../evaluation/EvolutionAnalysisView';
import { Loader2 } from 'lucide-react';
import { ConversationLog, getConversationLog } from '@/app/api/evaluation';

// Add types for evolution data that should be in the ConversationLog
interface AnswerHistoryItem {
  turn: number;
  agent: string;
  answer: string;
  is_correct: boolean;
}

interface EvolutionData {
  agreement_pattern: string;
  correctness_pattern: string;
  answer_history: AnswerHistoryItem[];
}

// Update the ConversationLog interface (extends existing one)
interface EnhancedConversationLog extends ConversationLog {
  simulated_evolution?: EvolutionData;
  dual_evolution?: EvolutionData;
}

interface ConversationViewerProps {
  logId: string | null;
}

export function ConversationViewer({ logId }: ConversationViewerProps) {
  const [log, setLog] = useState<EnhancedConversationLog | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState('messages'); // New state for active tab

  useEffect(() => {
    if (!logId) return;

    async function fetchLog() {
      setLoading(true);
      setError(null);
      try {
        const data = await getConversationLog(logId!);
        setLog(data);
      } catch (err) {
        console.error("Error loading log:", err);
        setError(err instanceof Error ? err.message : 'Failed to load conversation log');
      } finally {
        setLoading(false);
      }
    }

    fetchLog();
  }, [logId]);

  if (!logId) {
    return (
      <Card className="bg-gray-900 border-gray-800">
        <CardContent className="p-10 text-center text-gray-400">
          Select a conversation to view details
        </CardContent>
      </Card>
    );
  }

  if (loading) {
    return (
      <Card className="bg-gray-900 border-gray-800">
        <CardContent className="p-10 text-center">
          <div className="flex justify-center">
            <Loader2 className="h-8 w-8 animate-spin text-blue-500" />
          </div>
          <div className="mt-4 text-gray-400">Loading conversation...</div>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className="bg-gray-900 border-gray-800">
        <CardContent className="p-10 text-center text-red-400">
          {error}
        </CardContent>
      </Card>
    );
  }

  if (!log) {
    return (
      <Card className="bg-gray-900 border-gray-800">
        <CardContent className="p-10 text-center text-red-400">
          No conversation data found
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="bg-gray-900 border-gray-800">
      <CardHeader>
        <CardTitle className="text-gray-100">
          Question {log.question_id} - {log.benchmark}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="mb-4 p-4 bg-gray-800 rounded-md border border-gray-700">
          <div className="font-medium mb-1 text-gray-200">Question:</div>
          <div className="text-gray-300 whitespace-pre-wrap">{log.question}</div>
          {log.ground_truth && (
            <div className="mt-2">
              <span className="font-medium text-gray-200">Ground Truth: </span>
              <span className="text-green-400">{log.ground_truth}</span>
            </div>
          )}
        </div>

        {/* Top-level tabs for Messages vs Analysis */}
        <Tabs value={activeTab} onValueChange={setActiveTab} className="mt-4">
          <TabsList className="bg-gray-800 border-gray-700">
            <TabsTrigger 
              value="messages" 
              className="data-[state=active]:bg-gray-700 text-gray-300"
            >
              Messages
            </TabsTrigger>
            <TabsTrigger 
              value="evolution" 
              className="data-[state=active]:bg-gray-700 text-gray-300"
            >
              Evolution Analysis
            </TabsTrigger>
          </TabsList>
          
          {/* Messages Tab Content */}
          <TabsContent value="messages">
            <Tabs defaultValue="simulated" className="mt-4">
              <TabsList className="bg-gray-800 border-gray-700">
                <TabsTrigger 
                  value="simulated" 
                  className="data-[state=active]:bg-gray-700 text-gray-300"
                >
                  Single Agent (Simulated)
                </TabsTrigger>
                <TabsTrigger 
                  value="dual" 
                  className="data-[state=active]:bg-gray-700 text-gray-300"
                >
                  Dual Agent
                </TabsTrigger>
              </TabsList>
              
              <TabsContent value="simulated">
                <div className="space-y-4 mt-4">
                  {log.simulated_messages && log.simulated_messages.map((msg, idx) => (
                    <AgentMessage 
                      key={idx} 
                      message={{
                        id: `sim-${idx}`,
                        role: msg.agent! || msg.role! || (msg.original_role === 'assistant' ? 'Agent A' : msg.original_role)!,
                        content: msg.content || msg.original_content || '',
                        timestamp: Date.now()
                      }} 
                    />
                  ))}
                </div>
              </TabsContent>
              
              <TabsContent value="dual">
                <div className="space-y-4 mt-4">
                  {log.dual_messages && log.dual_messages.map((msg, idx) => (
                    <AgentMessage 
                      key={idx} 
                      message={{
                        id: `dual-${idx}`,
                        role: msg.agent! || msg.role! || (msg.original_role === 'assistant' ? 'Agent A' : msg.original_role)!,
                        content: msg.content || msg.original_content || '',
                        timestamp: Date.now()
                      }} 
                    />
                  ))}
                </div>
              </TabsContent>
            </Tabs>
          </TabsContent>
          
          {/* Evolution Analysis Tab Content */}
          <TabsContent value="evolution">
            <div className="mt-4">
              <EvolutionAnalysisView 
                simulatedEvolution={log.simulated_evolution} 
                dualEvolution={log.dual_evolution} 
              />
            </div>
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
}