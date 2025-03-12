import React from 'react';
import { Card, CardContent } from "@/components/ui/card";

// Agent colors for different roles
const AGENT_COLORS = {
  'Agent A': 'bg-blue-950 border-blue-800',
  'Agent B': 'bg-amber-950 border-amber-800',
  'System': 'bg-purple-950 border-purple-800',
  'User': 'bg-gray-900 border-gray-800'
};

// Agent icons
const AGENT_ICONS = {
  'Agent A': '🧠',
  'Agent B': '🔍',
  'System': '⚙️',
  'User': '👤'
};

interface Message {
  id: string;
  role: string;
  content: string;
  timestamp: number;
}

interface AgentMessageProps {
  message: Message;
}

export function AgentMessage({ message }: AgentMessageProps) {
  // Get the appropriate color and icon for the agent
  const colorClass = AGENT_COLORS[message.role as keyof typeof AGENT_COLORS] || AGENT_COLORS['User'];
  const icon = AGENT_ICONS[message.role as keyof typeof AGENT_ICONS] || AGENT_ICONS['User'];

  return (
    <Card className={`mb-4 ${colorClass}`}>
      <CardContent className="pt-4">
        <div className="flex items-start gap-3">
          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-gray-800">
            <span>{icon}</span>
          </div>
          <div>
            <div className="font-semibold text-sm text-gray-300 mb-1">
              {message.role}
            </div>
            <div className="whitespace-pre-wrap text-gray-100 break-words">
              {message.content}
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}