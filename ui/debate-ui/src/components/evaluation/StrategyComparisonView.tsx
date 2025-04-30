import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Loader2, BarChart2, GitCompare, GitBranch, CheckCircle } from "lucide-react";

// Types for comparison data with evolution metrics
interface StrategyResults {
  run_id: string;
  summary: {
    total_questions: number;
    simulated_correct: number;
    dual_correct: number;
    simulated_accuracy: number;
    dual_accuracy: number;
  };
  evolution_summary?: {
    agreement_counts: Record<string, number>;
    correctness_counts: Record<string, number>;
    simulated: {
      agreement: Record<string, number>;
      correctness: Record<string, number>;
    };
    dual: {
      agreement: Record<string, number>;
      correctness: Record<string, number>;
    };
  };
}

interface QuestionComparison {
  [strategy: string]: {
    ground_truth: string;
    simulated: {
      answer: string;
      correct: boolean;
      time: number;
      evolution?: {
        agreement_pattern: string;
        correctness_pattern: string;
      };
    };
    dual: {
      answer: string;
      correct: boolean;
      time: number;
      evolution?: {
        agreement_pattern: string;
        correctness_pattern: string;
      };
    };
  };
}

interface ComparisonData {
  timestamp: string;
  benchmark: string;
  strategies: {
    [strategy: string]: StrategyResults;
  };
  questions: {
    [questionId: string]: QuestionComparison;
  };
}

interface StrategyComparisonViewProps {
  comparisonId: string;
}

// Simple table components
const Table: React.FC<React.PropsWithChildren<{ className?: string }>> = ({ children, className = "" }) => (
  <div className="w-full overflow-auto">
    <table className={`w-full caption-bottom text-sm ${className}`}>
      {children}
    </table>
  </div>
);

const TableHeader: React.FC<React.PropsWithChildren<{ className?: string }>> = ({ children, className = "" }) => (
  <thead className={`[&_tr]:border-b ${className}`}>{children}</thead>
);

const TableBody: React.FC<React.PropsWithChildren<{ className?: string }>> = ({ children, className = "" }) => (
  <tbody className={`[&_tr:last-child]:border-0 ${className}`}>{children}</tbody>
);

const TableRow: React.FC<React.PropsWithChildren<{ className?: string }>> = ({ children, className = "" }) => (
  <tr className={`border-b transition-colors hover:bg-muted/50 data-[state=selected]:bg-muted ${className}`}>
    {children}
  </tr>
);

const TableHead: React.FC<React.PropsWithChildren<{ className?: string }>> = ({ children, className = "" }) => (
  <th className={`h-10 px-2 text-left align-middle font-medium text-muted-foreground ${className}`}>
    {children}
  </th>
);

const TableCell: React.FC<React.PropsWithChildren<{ className?: string }>> = ({ children, className = "" }) => (
  <td className={`p-2 align-middle ${className}`}>{children}</td>
);

// Component to display pattern badges
interface PatternBadgeProps {
  pattern: string;
  size?: "default" | "small";
}

const PatternBadge: React.FC<PatternBadgeProps> = ({ pattern, size = "default" }) => {
  let colorClass = "bg-gray-700 text-gray-300";
  
  // Agreement patterns
  if (pattern === "Complete Agreement") colorClass = "bg-green-900/50 text-green-300";
  else if (pattern === "Resolved Disagreement") colorClass = "bg-blue-900/50 text-blue-300";
  else if (pattern === "Unresolved Disagreement") colorClass = "bg-amber-900/50 text-amber-300";
  
  // Correctness patterns
  else if (pattern === "Stable Correct") colorClass = "bg-green-900/50 text-green-300";
  else if (pattern === "Stable Incorrect") colorClass = "bg-red-900/50 text-red-300";
  else if (pattern === "Stable Correct (One Agent)") colorClass = "bg-emerald-900/50 text-emerald-300";
  else if (pattern === "Improvement") colorClass = "bg-blue-900/50 text-blue-300";
  else if (pattern === "Deterioration") colorClass = "bg-amber-900/50 text-amber-300";
  else if (pattern === "Mixed Pattern") colorClass = "bg-purple-900/50 text-purple-300";
  else if (pattern === "Mixed Pattern (Final Correct)") colorClass = "bg-indigo-900/50 text-indigo-300";
  
  const sizeClass = size === "small" ? "text-xs px-1.5 py-0.5" : "text-sm px-2 py-1";
  
  return (
    <span className={`${colorClass} ${sizeClass} rounded-full inline-block font-medium border border-opacity-30`}>
      {pattern}
    </span>
  );
};

// Component to display a horizontal bar chart
interface PatternBarChartProps {
  data: Record<string, number>;
  title: string;
  className?: string;
}

const PatternBarChart: React.FC<PatternBarChartProps> = ({ data, title, className = "" }) => {
  const total = Object.values(data).reduce((sum, count) => sum + Number(count), 0);
  
  if (total === 0) {
    return (
      <div className={`mb-4 ${className}`}>
        <div className="text-sm font-medium text-gray-300 mb-1">{title}</div>
        <div className="text-gray-400 text-sm">No data available</div>
      </div>
    );
  }
  
  return (
    <div className={`mb-4 ${className}`}>
      <div className="text-sm font-medium text-gray-300 mb-1">{title}</div>
      <div className="h-8 flex rounded-md overflow-hidden">
        {Object.entries(data).map(([pattern, count]) => {
          const width = (Number(count) / total) * 100;
          if (width === 0) return null;
          
          let bgColor = "bg-gray-700";
          // Agreement patterns
          if (pattern === "Complete Agreement") bgColor = "bg-green-600";
          else if (pattern === "Resolved Disagreement") bgColor = "bg-blue-600";
          else if (pattern === "Unresolved Disagreement") bgColor = "bg-amber-600";
          
          // Correctness patterns
          else if (pattern === "Stable Correct") bgColor = "bg-green-600";
          else if (pattern === "Stable Incorrect") bgColor = "bg-red-600";
          else if (pattern === "Stable Correct (One Agent)") bgColor = "bg-emerald-600";
          else if (pattern === "Improvement") bgColor = "bg-blue-600";
          else if (pattern === "Deterioration") bgColor = "bg-amber-600";
          else if (pattern === "Mixed Pattern") bgColor = "bg-purple-600";
          else if (pattern === "Mixed Pattern (Final Correct)") bgColor = "bg-indigo-600";
          
          return (
            <div 
              key={pattern} 
              className={`${bgColor} relative group`}
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
          .map(([pattern, count]) => {
            let bgColor = "bg-gray-700";
            // Agreement patterns
            if (pattern === "Complete Agreement") bgColor = "bg-green-600";
            else if (pattern === "Resolved Disagreement") bgColor = "bg-blue-600";
            else if (pattern === "Unresolved Disagreement") bgColor = "bg-amber-600";
            
            // Correctness patterns
            else if (pattern === "Stable Correct") bgColor = "bg-green-600";
            else if (pattern === "Stable Incorrect") bgColor = "bg-red-600";
            else if (pattern === "Stable Correct (One Agent)") bgColor = "bg-emerald-600";
            else if (pattern === "Improvement") bgColor = "bg-blue-600";
            else if (pattern === "Deterioration") bgColor = "bg-amber-600";
            else if (pattern === "Mixed Pattern") bgColor = "bg-purple-600";
            else if (pattern === "Mixed Pattern (Final Correct)") bgColor = "bg-indigo-600";
            
            return (
              <div key={pattern} className="flex items-center text-xs">
                <div className={`w-3 h-3 mr-1 rounded-sm ${bgColor}`}></div>
                <span>{pattern}: {count}</span>
              </div>
            );
          })
        }
      </div>
    </div>
  );
};

export const StrategyComparisonView: React.FC<StrategyComparisonViewProps> = ({ comparisonId }) => {
  const [comparisonData, setComparisonData] = useState<ComparisonData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchComparisonData = async () => {
      if (!comparisonId) return;
      
      setLoading(true);
      setError(null);
      
      try {
        const response = await fetch(`/api/comparison/${comparisonId}`);
        if (!response.ok) {
          throw new Error(`Failed to fetch comparison data: ${response.statusText}`);
        }
        
        const data = await response.json();
        setComparisonData(data);
      } catch (err) {
        console.error('Error fetching comparison data:', err);
        setError(err instanceof Error ? err.message : 'Failed to load comparison data');
      } finally {
        setLoading(false);
      }
    };
    
    fetchComparisonData();
  }, [comparisonId]);

  if (loading) {
    return (
      <Card className="bg-gray-900 border-gray-800">
        <CardContent className="p-6 flex justify-center items-center">
          <div className="text-center">
            <Loader2 className="h-8 w-8 animate-spin text-blue-500 mx-auto mb-4" />
            <p className="text-gray-400">Loading comparison data...</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className="bg-gray-900 border-gray-800">
        <CardContent className="p-6 text-center">
          <div className="text-red-500 mb-4">{error}</div>
        </CardContent>
      </Card>
    );
  }

  if (!comparisonData) {
    return (
      <Card className="bg-gray-900 border-gray-800">
        <CardContent className="p-6 text-center text-gray-400">
          No comparison data available
        </CardContent>
      </Card>
    );
  }

  // Extract strategy IDs from the data
  const strategyIds = Object.keys(comparisonData.strategies);
  const questionIds = Object.keys(comparisonData.questions);

  return (
    <Card className="bg-gray-900 border-gray-800">
      <CardHeader>
        <CardTitle className="text-gray-100">
          Strategy Comparison - {comparisonData.benchmark}
        </CardTitle>
        <div className="text-sm text-gray-400">
          {new Date(comparisonData.timestamp).toLocaleString()}
        </div>
      </CardHeader>
      <CardContent>
        <Tabs defaultValue="summary" className="w-full">
          <TabsList className="bg-gray-800">
            <TabsTrigger 
              value="summary" 
              className="data-[state=active]:bg-gray-700 text-gray-300"
            >
              Performance Summary
            </TabsTrigger>
            <TabsTrigger 
              value="evolution" 
              className="data-[state=active]:bg-gray-700 text-gray-300"
            >
              Solution Evolution
            </TabsTrigger>
            <TabsTrigger 
              value="questions" 
              className="data-[state=active]:bg-gray-700 text-gray-300"
            >
              Question Details
            </TabsTrigger>
          </TabsList>
          
          {/* Performance Summary Tab */}
          <TabsContent value="summary">
            <div className="mt-4">
              <div className="grid grid-cols-1 gap-4 mb-6">
                <div className="p-4 rounded-md bg-gray-800 border border-gray-700">
                  <div className="flex items-center mb-4">
                    <BarChart2 className="w-5 h-5 mr-2 text-blue-400" />
                    <h3 className="text-lg font-semibold text-gray-200">Performance Comparison</h3>
                  </div>
                  
                  <Table>
                    <TableHeader>
                      <TableRow className="border-gray-700">
                        <TableHead className="text-gray-300">Strategy</TableHead>
                        <TableHead className="text-gray-300 text-right">Single Agent Accuracy</TableHead>
                        <TableHead className="text-gray-300 text-right">Dual Agent Accuracy</TableHead>
                        <TableHead className="text-gray-300 text-right">Improvement</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {strategyIds.map(strategyId => {
                        const strategyData = comparisonData.strategies[strategyId];
                        const improvement = (
                          strategyData.summary.dual_accuracy - 
                          strategyData.summary.simulated_accuracy
                        ) * 100;
                        
                        return (
                          <TableRow key={strategyId} className="border-gray-800">
                            <TableCell className="font-medium text-gray-300">
                              {strategyId.charAt(0).toUpperCase() + strategyId.slice(1)}
                            </TableCell>
                            <TableCell className="text-right text-gray-300">
                              {(strategyData.summary.simulated_accuracy * 100).toFixed(1)}%
                            </TableCell>
                            <TableCell className="text-right text-gray-300">
                              {(strategyData.summary.dual_accuracy * 100).toFixed(1)}%
                            </TableCell>
                            <TableCell className={`text-right font-medium ${
                              improvement > 0 ? 'text-green-500' : 
                              improvement < 0 ? 'text-red-500' : 'text-gray-400'
                            }`}>
                              {improvement > 0 ? '+' : ''}{improvement.toFixed(1)}%
                            </TableCell>
                          </TableRow>
                        );
                      })}
                    </TableBody>
                  </Table>
                </div>
              </div>
            </div>
          </TabsContent>
          
          {/* Solution Evolution Tab */}
          <TabsContent value="evolution">
            <div className="mt-4 space-y-6">
              {strategyIds.map(strategyId => {
                const strategy = comparisonData.strategies[strategyId];
                if (!strategy.evolution_summary) return null;
                
                return (
                  <div key={strategyId} className="p-4 rounded-md bg-gray-800 border border-gray-700">
                    <h3 className="text-lg font-semibold text-gray-200 mb-4">
                      {strategyId.charAt(0).toUpperCase() + strategyId.slice(1)} Evolution Patterns
                    </h3>
                    
                    <div className="mb-6">
                      <div className="flex items-center mb-2">
                        <GitBranch className="w-4 h-4 mr-2 text-blue-400" />
                        <h4 className="text-md font-medium text-gray-300">Agreement Patterns</h4>
                      </div>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                        <div className="p-3 bg-gray-850 rounded-md border border-gray-700">
                          <h5 className="text-sm font-medium text-gray-400 mb-2">Single Agent</h5>
                          <PatternBarChart 
                            data={strategy.evolution_summary.simulated.agreement}
                            title=""
                          />
                        </div>
                        <div className="p-3 bg-gray-850 rounded-md border border-gray-700">
                          <h5 className="text-sm font-medium text-gray-400 mb-2">Dual Agent</h5>
                          <PatternBarChart 
                            data={strategy.evolution_summary.dual.agreement}
                            title=""
                          />
                        </div>
                      </div>
                    </div>
                    
                    <div>
                      <div className="flex items-center mb-2">
                        <CheckCircle className="w-4 h-4 mr-2 text-green-400" />
                        <h4 className="text-md font-medium text-gray-300">Correctness Patterns</h4>
                      </div>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="p-3 bg-gray-850 rounded-md border border-gray-700">
                          <h5 className="text-sm font-medium text-gray-400 mb-2">Single Agent</h5>
                          <PatternBarChart 
                            data={strategy.evolution_summary.simulated.correctness}
                            title=""
                          />
                        </div>
                        <div className="p-3 bg-gray-850 rounded-md border border-gray-700">
                          <h5 className="text-sm font-medium text-gray-400 mb-2">Dual Agent</h5>
                          <PatternBarChart 
                            data={strategy.evolution_summary.dual.correctness}
                            title=""
                          />
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </TabsContent>
          
          {/* Questions Tab */}
          <TabsContent value="questions">
            <div className="mt-4 space-y-4">
              {questionIds.map(questionId => (
                <div key={questionId} className="p-4 rounded-md bg-gray-800 border border-gray-700">
                  <h3 className="text-lg font-semibold text-gray-200 mb-3">
                    Question {questionId}
                  </h3>
                  
                  <div className="mb-2 flex">
                    <div className="text-gray-400 mr-2">Ground Truth:</div>
                    <div className="text-green-400 font-medium">
                      {Object.values(comparisonData.questions[questionId])[0].ground_truth}
                    </div>
                  </div>
                  
                  <Table>
                    <TableHeader>
                      <TableRow className="border-gray-700">
                        <TableHead className="text-gray-300">Strategy</TableHead>
                        <TableHead className="text-gray-300">Simulated Answer</TableHead>
                        <TableHead className="text-gray-300">Evolution</TableHead>
                        <TableHead className="text-gray-300">Dual Answer</TableHead>
                        <TableHead className="text-gray-300">Evolution</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {strategyIds.map(strategyId => {
                        const questionData = comparisonData.questions[questionId][strategyId];
                        if (!questionData) return null;
                        
                        return (
                          <TableRow key={strategyId} className="border-gray-800">
                            <TableCell className="font-medium text-gray-300">
                              {strategyId.charAt(0).toUpperCase() + strategyId.slice(1)}
                            </TableCell>
                            <TableCell>
                              <div className={
                                questionData.simulated.correct ? 'text-green-500' : 'text-red-500'
                              }>
                                {questionData.simulated.answer}
                                <span className="text-gray-400 text-xs ml-2">
                                  ({questionData.simulated.time.toFixed(1)}s)
                                </span>
                              </div>
                            </TableCell>
                            <TableCell>
                              {questionData.simulated.evolution && (
                                <div className="flex flex-col gap-1">
                                  <PatternBadge 
                                    pattern={questionData.simulated.evolution.agreement_pattern}
                                    size="small"
                                  />
                                  <PatternBadge 
                                    pattern={questionData.simulated.evolution.correctness_pattern}
                                    size="small"
                                  />
                                </div>
                              )}
                            </TableCell>
                            <TableCell>
                              <div className={
                                questionData.dual.correct ? 'text-green-500' : 'text-red-500'
                              }>
                                {questionData.dual.answer}
                                <span className="text-gray-400 text-xs ml-2">
                                  ({questionData.dual.time.toFixed(1)}s)
                                </span>
                              </div>
                            </TableCell>
                            <TableCell>
                              {questionData.dual.evolution && (
                                <div className="flex flex-col gap-1">
                                  <PatternBadge 
                                    pattern={questionData.dual.evolution.agreement_pattern}
                                    size="small"
                                  />
                                  <PatternBadge 
                                    pattern={questionData.dual.evolution.correctness_pattern}
                                    size="small"
                                  />
                                </div>
                              )}
                            </TableCell>
                          </TableRow>
                        );
                      })}
                    </TableBody>
                  </Table>
                </div>
              ))}
            </div>
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
};