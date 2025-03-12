import React from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { AgentMessage } from './AgentMessage';
import { Loader2 } from 'lucide-react';

interface Message {
  id: string;
  role: string;
  content: string;
  timestamp: number;
}

interface DebateArenaProps {
  simulatedMessages: Message[];
  dualAgentMessages: Message[];
  inProgress: boolean;
}

export function DebateArena({ simulatedMessages, dualAgentMessages, inProgress }: DebateArenaProps) {
  return (
    <Tabs defaultValue="simulated" className="w-full">
      <div className="flex justify-between items-center mb-4">
        <TabsList className="bg-gray-800">
          <TabsTrigger value="simulated" className="data-[state=active]:bg-gray-700">
            Simulated Dialogue ({simulatedMessages.length > 0 ? simulatedMessages.length - 1 : 0})
          </TabsTrigger>
          <TabsTrigger value="dual" className="data-[state=active]:bg-gray-700">
            Dual-Agent Dialogue ({dualAgentMessages.length > 0 ? dualAgentMessages.length - 1 : 0})
          </TabsTrigger>
        </TabsList>
      </div>

      <TabsContent value="simulated" className="mt-0">
        <Card className="bg-gray-900 border-gray-800">
          <CardHeader>
            <CardTitle className="text-gray-100">Simulated Two-Agent Dialogue</CardTitle>
            <CardDescription className="text-gray-400">
              A single model alternating between two roles
              {inProgress && <span className="ml-2 inline-block animate-pulse">• Processing...</span>}
            </CardDescription>
          </CardHeader>
          <CardContent className="max-h-[600px] overflow-y-auto">
            {simulatedMessages.length > 0 ? (
              simulatedMessages.map((message) => (
                <AgentMessage key={message.id} message={message} />
              ))
            ) : inProgress ? (
              <div className="flex justify-center items-center h-40">
                <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
              </div>
            ) : (
              <div className="text-center py-10 text-gray-400">
                No conversation yet. Enter a problem to start.
              </div>
            )}
          </CardContent>
        </Card>
      </TabsContent>

      <TabsContent value="dual" className="mt-0">
        <Card className="bg-gray-900 border-gray-800">
          <CardHeader>
            <CardTitle className="text-gray-100">Dual-Agent Debate</CardTitle>
            <CardDescription className="text-gray-400">
              Two separate agents with distinct roles
              {inProgress && <span className="ml-2 inline-block animate-pulse">• Processing...</span>}
            </CardDescription>
          </CardHeader>
          <CardContent className="max-h-[600px] overflow-y-auto">
            {dualAgentMessages.length > 0 ? (
              dualAgentMessages.map((message) => (
                <AgentMessage key={message.id} message={message} />
              ))
            ) : inProgress ? (
              <div className="flex justify-center items-center h-40">
                <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
              </div>
            ) : (
              <div className="text-center py-10 text-gray-400">
                No conversation yet. Enter a problem to start.
              </div>
            )}
          </CardContent>
        </Card>
      </TabsContent>
    </Tabs>
  );
}