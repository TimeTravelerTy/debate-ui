import React from 'react';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";

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

interface StrategySelectorProps {
  strategies: Strategy[];
  selectedStrategy: string;
  onStrategyChange: (value: string) => void;
}

export function StrategySelector({ strategies, selectedStrategy, onStrategyChange }: StrategySelectorProps) {
  const strategy = strategies.find(s => s.id === selectedStrategy);

  return (
    <div className="mb-6">
      <div className="flex items-center gap-4 mb-4">
        <h2 className="text-lg font-medium text-gray-200">Collaboration Strategy:</h2>
        <Select value={selectedStrategy} onValueChange={onStrategyChange}>
          <SelectTrigger className="w-60 bg-gray-800 border-gray-700 text-gray-200">
            <SelectValue placeholder="Select a strategy" />
          </SelectTrigger>
          <SelectContent className="bg-gray-800 border-gray-700">
            {strategies.map((s) => (
              <SelectItem key={s.id} value={s.id} className="text-gray-200 focus:bg-gray-700 focus:text-gray-100">
                {s.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>
      
      {strategy && (
        <Card className="bg-gray-900 border-gray-800">
          <CardHeader className="pb-2">
            <CardTitle className="text-gray-100">{strategy.name}</CardTitle>
            <CardDescription className="text-gray-400">{strategy.description}</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-4">
              <div className="p-3 bg-blue-900/30 rounded-md border border-blue-800/50">
                <div className="font-semibold text-blue-300">Agent A: {strategy.agentA.role}</div>
                <div className="text-sm text-blue-200 mt-1">{strategy.agentA.description}</div>
              </div>
              <div className="p-3 bg-amber-900/30 rounded-md border border-amber-800/50">
                <div className="font-semibold text-amber-300">Agent B: {strategy.agentB.role}</div>
                <div className="text-sm text-amber-200 mt-1">{strategy.agentB.description}</div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}