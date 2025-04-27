import React from 'react';
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

interface PatternCounts {
  [key: string]: number;
}

interface AgentPatternData {
  agreement: PatternCounts;
  correctness: PatternCounts;
}

interface EvolutionSummaryData {
  agreement_counts: PatternCounts;
  correctness_counts: PatternCounts;
  simulated: AgentPatternData;
  dual: AgentPatternData;
}

interface EvolutionSummaryViewProps {
  summaryData?: EvolutionSummaryData;
}

interface PatternBarProps {
  data: PatternCounts;
  title: string;
  colorClasses: {[key: string]: string};
}

const PatternBar: React.FC<PatternBarProps> = ({ data, title, colorClasses }) => {
  const total = Object.values(data).reduce((sum, count) => sum + Number(count), 0);
  
  if (total === 0) {
    return (
      <div className="mb-4">
        <h4 className="text-sm font-medium text-gray-300 mb-1">{title}</h4>
        <div className="text-gray-400 text-sm">No data available</div>
      </div>
    );
  }
  
  return (
    <div className="mb-4">
      <h4 className="text-sm font-medium text-gray-300 mb-1">{title}</h4>
      <div className="h-8 flex rounded-md overflow-hidden">
        {Object.entries(data).map(([pattern, count]) => {
          const width = (Number(count) / total) * 100;
          if (width === 0) return null;
          
          return (
            <div 
              key={pattern} 
              className={`${colorClasses[pattern] || 'bg-gray-700'} relative group`}
              style={{ width: `${width}%` }}
            >
              {/* Tooltip */}
              <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-2 py-1 bg-gray-900 text-gray-200 text-xs rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap z-10 pointer-events-none">
                {pattern}: {count} ({(width).toFixed(1)}%)
              </div>
            </div>
          );
        })}
      </div>
      
      {/* Legend */}
      <div className="mt-2 flex flex-wrap gap-2">
        {Object.entries(data)
          .filter(([_, count]) => Number(count) > 0)
          .map(([pattern, count]) => (
            <div key={pattern} className="flex items-center text-xs">
              <div className={`w-3 h-3 mr-1 rounded-sm ${colorClasses[pattern] || 'bg-gray-700'}`}></div>
              <span>{pattern}: {count}</span>
            </div>
          ))
        }
      </div>
    </div>
  );
};

const patternColors = {
  // Agreement patterns
  "Complete Agreement": "bg-green-600",
  "Resolved Disagreement": "bg-blue-600",
  "Unresolved Disagreement": "bg-amber-600",
  "Insufficient Data": "bg-gray-600",
  
  // Correctness patterns
  "Stable Correct": "bg-green-600",
  "Stable Incorrect": "bg-red-600",
  "Stable Correct (One Agent)": "bg-emerald-600",
  "Improvement": "bg-blue-600",
  "Deterioration": "bg-amber-600",
  "Mixed Pattern": "bg-purple-600",
  "Mixed Pattern (Final Correct)": "bg-indigo-600"
};

export function EvolutionSummaryView({ summaryData }: EvolutionSummaryViewProps) {
  if (!summaryData) {
    return (
      <Card className="bg-gray-900 border-gray-800">
        <CardContent className="p-6 text-center text-gray-400">
          No evolution summary data available
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="bg-gray-900 border-gray-800">
      <CardHeader>
        <CardTitle className="text-gray-100">Solution Evolution Patterns</CardTitle>
      </CardHeader>
      <CardContent>
        <Tabs defaultValue="combined" className="w-full">
          <TabsList className="bg-gray-800 mb-4">
            <TabsTrigger value="combined" className="data-[state=active]:bg-gray-700 text-gray-300">
              Combined
            </TabsTrigger>
            <TabsTrigger value="comparison" className="data-[state=active]:bg-gray-700 text-gray-300">
              Simulated vs Dual
            </TabsTrigger>
          </TabsList>
          
          <TabsContent value="combined">
            <div className="space-y-6">
              <div className="p-4 rounded-md bg-gray-800 border border-gray-700">
                <h3 className="font-medium text-gray-200 mb-4">Agreement Patterns</h3>
                <PatternBar 
                  data={summaryData.agreement_counts} 
                  title="All Conversations" 
                  colorClasses={patternColors} 
                />
              </div>
              
              <div className="p-4 rounded-md bg-gray-800 border border-gray-700">
                <h3 className="font-medium text-gray-200 mb-4">Correctness Patterns</h3>
                <PatternBar 
                  data={summaryData.correctness_counts} 
                  title="All Conversations" 
                  colorClasses={patternColors} 
                />
              </div>
            </div>
          </TabsContent>
          
          <TabsContent value="comparison">
            <div className="space-y-6">
              <div className="p-4 rounded-md bg-gray-800 border border-gray-700">
                <h3 className="font-medium text-gray-200 mb-4">Agreement Patterns: Simulated vs Dual</h3>
                <PatternBar 
                  data={summaryData.simulated.agreement} 
                  title="Simulated Dialogue" 
                  colorClasses={patternColors} 
                />
                <PatternBar 
                  data={summaryData.dual.agreement} 
                  title="Dual-Agent Dialogue" 
                  colorClasses={patternColors} 
                />
              </div>
              
              <div className="p-4 rounded-md bg-gray-800 border border-gray-700">
                <h3 className="font-medium text-gray-200 mb-4">Correctness Patterns: Simulated vs Dual</h3>
                <PatternBar 
                  data={summaryData.simulated.correctness} 
                  title="Simulated Dialogue" 
                  colorClasses={patternColors} 
                />
                <PatternBar 
                  data={summaryData.dual.correctness} 
                  title="Dual-Agent Dialogue" 
                  colorClasses={patternColors} 
                />
              </div>
            </div>
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
}

// Default export is required for React artifacts
export default function EvolutionSummaryComponent() {
  // Sample data for demonstration
  const sampleData = {
    agreement_counts: {
      "Complete Agreement": 12,
      "Resolved Disagreement": 23,
      "Unresolved Disagreement": 15,
      "Insufficient Data": 2
    },
    correctness_counts: {
      "Stable Correct": 18,
      "Stable Incorrect": 8,
      "Stable Correct (One Agent)": 10,
      "Improvement": 7,
      "Deterioration": 4,
      "Mixed Pattern": 3,
      "Mixed Pattern (Final Correct)": 2,
      "Insufficient Data": 0
    },
    simulated: {
      agreement: {
        "Complete Agreement": 8,
        "Resolved Disagreement": 11,
        "Unresolved Disagreement": 6
      },
      correctness: {
        "Stable Correct": 9,
        "Stable Incorrect": 4,
        "Improvement": 5,
        "Deterioration": 2
      }
    },
    dual: {
      agreement: {
        "Complete Agreement": 4,
        "Resolved Disagreement": 12,
        "Unresolved Disagreement": 9
      },
      correctness: {
        "Stable Correct": 9,
        "Stable Incorrect": 4,
        "Improvement": 2,
        "Deterioration": 2
      }
    }
  };
  
  return <EvolutionSummaryView summaryData={sampleData} />;
}