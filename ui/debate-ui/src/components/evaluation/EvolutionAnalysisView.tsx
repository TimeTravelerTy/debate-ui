import React from 'react';
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

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

interface EvolutionAnalysisViewProps {
  simulatedEvolution?: EvolutionData;
  dualEvolution?: EvolutionData;
}

const patternColors = {
  // Agreement patterns
  "Complete Agreement": "bg-green-900/40 border-green-800/50 text-green-300",
  "Resolved Disagreement": "bg-blue-900/40 border-blue-800/50 text-blue-300",
  "Unresolved Disagreement": "bg-amber-900/40 border-amber-800/50 text-amber-300",
  
  // Correctness patterns
  "Stable Correct": "bg-green-900/40 border-green-800/50 text-green-300",
  "Stable Incorrect": "bg-red-900/40 border-red-800/50 text-red-300",
  "Stable Correct (One Agent)": "bg-emerald-900/40 border-emerald-800/50 text-emerald-300",
  "Improvement": "bg-blue-900/40 border-blue-800/50 text-blue-300",
  "Deterioration": "bg-amber-900/40 border-amber-800/50 text-amber-300",
  "Mixed Pattern": "bg-purple-900/40 border-purple-800/50 text-purple-300",
  "Mixed Pattern (Final Correct)": "bg-indigo-900/40 border-indigo-800/50 text-indigo-300",
  "Insufficient Data": "bg-gray-900/40 border-gray-800/50 text-gray-300"
};

interface PatternBadgeProps {
  pattern: string;
}

const PatternBadge: React.FC<PatternBadgeProps> = ({ pattern }) => {
    const colorClass =
      (patternColors as Record<string, string>)[pattern] ||
      "bg-gray-900/40 border-gray-800/50 text-gray-300";
  
    return (
      <div className={`px-3 py-1 rounded-full ${colorClass} inline-block text-sm font-medium border`}>
        {pattern}
      </div>
    );
  };

interface AnswerHistoryTimelineProps {
  answerHistory?: AnswerHistoryItem[];
}

const AnswerHistoryTimeline: React.FC<AnswerHistoryTimelineProps> = ({ answerHistory }) => {
  if (!answerHistory || answerHistory.length === 0) {
    return <div className="text-gray-400 text-center py-4">No answer history available</div>;
  }

  return (
    <div className="mt-4 space-y-4">
      <h3 className="text-sm font-medium text-gray-300">Answer Evolution Timeline</h3>
      <div className="relative">
        {/* Timeline line */}
        <div className="absolute left-6 top-0 bottom-0 w-px bg-gray-700"></div>
        
        {/* Timeline events */}
        <div className="space-y-4">
          {answerHistory.map((item, index) => (
            <div key={index} className="relative pl-14">
              {/* Timeline marker */}
              <div className={`absolute left-4 top-1 w-4 h-4 rounded-full ${item.is_correct ? 'bg-green-500' : 'bg-red-500'} flex items-center justify-center`}>
                <span className="text-white text-xs">{index + 1}</span>
              </div>
              
              {/* Content */}
              <div className={`p-3 rounded-md ${item.is_correct ? 'bg-green-900/20 border-green-800/30' : 'bg-red-900/20 border-red-800/30'} border`}>
                <div className="flex justify-between">
                  <div className="font-medium text-gray-200">{item.agent}</div>
                  <div className="text-xs text-gray-400">Turn {item.turn + 1}</div>
                </div>
                <div className="mt-1 text-sm">
                  <span className="text-gray-400">Answer: </span>
                  <span className={item.is_correct ? 'text-green-300' : 'text-red-300'}>
                    {item.answer}
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export function EvolutionAnalysisView({ simulatedEvolution, dualEvolution }: EvolutionAnalysisViewProps) {
  if (!simulatedEvolution && !dualEvolution) {
    return (
      <Card className="bg-gray-900 border-gray-800">
        <CardContent className="p-6 text-center text-gray-400">
          No solution evolution analysis available
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="bg-gray-900 border-gray-800">
      <CardHeader>
        <CardTitle className="text-gray-100">Solution Evolution Analysis</CardTitle>
      </CardHeader>
      <CardContent>
        <Tabs defaultValue="simulated" className="w-full">
          <TabsList className="bg-gray-800 mb-4">
            <TabsTrigger value="simulated" className="data-[state=active]:bg-gray-700 text-gray-300">
              Simulated Dialogue
            </TabsTrigger>
            <TabsTrigger value="dual" className="data-[state=active]:bg-gray-700 text-gray-300">
              Dual-Agent Dialogue
            </TabsTrigger>
          </TabsList>
          
          <TabsContent value="simulated">
            {simulatedEvolution ? (
              <div className="space-y-6">
                <div className="grid grid-cols-2 gap-4">
                  <div className="p-4 rounded-md bg-gray-800 border border-gray-700">
                    <div className="text-sm font-medium text-gray-400 mb-2">Agreement Pattern</div>
                    <PatternBadge pattern={simulatedEvolution.agreement_pattern} />
                  </div>
                  <div className="p-4 rounded-md bg-gray-800 border border-gray-700">
                    <div className="text-sm font-medium text-gray-400 mb-2">Correctness Pattern</div>
                    <PatternBadge pattern={simulatedEvolution.correctness_pattern} />
                  </div>
                </div>
                
                <AnswerHistoryTimeline answerHistory={simulatedEvolution.answer_history} />
              </div>
            ) : (
              <div className="text-center text-gray-400 py-4">
                No data available for simulated dialogue
              </div>
            )}
          </TabsContent>
          
          <TabsContent value="dual">
            {dualEvolution ? (
              <div className="space-y-6">
                <div className="grid grid-cols-2 gap-4">
                  <div className="p-4 rounded-md bg-gray-800 border border-gray-700">
                    <div className="text-sm font-medium text-gray-400 mb-2">Agreement Pattern</div>
                    <PatternBadge pattern={dualEvolution.agreement_pattern} />
                  </div>
                  <div className="p-4 rounded-md bg-gray-800 border border-gray-700">
                    <div className="text-sm font-medium text-gray-400 mb-2">Correctness Pattern</div>
                    <PatternBadge pattern={dualEvolution.correctness_pattern} />
                  </div>
                </div>
                
                <AnswerHistoryTimeline answerHistory={dualEvolution.answer_history} />
              </div>
            ) : (
              <div className="text-center text-gray-400 py-4">
                No data available for dual-agent dialogue
              </div>
            )}
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
}

// Default export is required for React artifacts
export default function EvolutionAnalysisComponent() {
  // Sample data for demonstration
  const sampleData = {
    simulatedEvolution: {
      agreement_pattern: "Resolved Disagreement",
      correctness_pattern: "Improvement",
      answer_history: [
        { turn: 0, agent: "Agent A", answer: "5", is_correct: false },
        { turn: 1, agent: "Agent B", answer: "4", is_correct: false },
        { turn: 2, agent: "Agent A", answer: "3", is_correct: true },
        { turn: 3, agent: "Agent B", answer: "3", is_correct: true }
      ]
    },
    dualEvolution: {
      agreement_pattern: "Unresolved Disagreement",
      correctness_pattern: "Stable Correct (One Agent)",
      answer_history: [
        { turn: 0, agent: "Agent A", answer: "3", is_correct: true },
        { turn: 1, agent: "Agent B", answer: "5", is_correct: false },
        { turn: 2, agent: "Agent A", answer: "3", is_correct: true },
        { turn: 3, agent: "Agent B", answer: "4", is_correct: false }
      ]
    }
  };
  
  return <EvolutionAnalysisView 
    simulatedEvolution={sampleData.simulatedEvolution} 
    dualEvolution={sampleData.dualEvolution} 
  />;
}