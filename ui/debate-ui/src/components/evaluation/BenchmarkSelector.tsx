import React from 'react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from "@/components/ui/select";
import { Button } from "@/components/ui/button";

interface Benchmark {
  id: string;
  name: string;
  description: string;
}

interface Strategy {
  id: string;
  name: string;
  description: string;
}

interface BenchmarkSelectorProps {
  benchmarks: Benchmark[];
  strategies: Strategy[];
  selectedBenchmark: string;
  selectedStrategy: string;
  maxQuestions: number;
  isRunning: boolean;
  onBenchmarkChange: (value: string) => void;
  onStrategyChange: (value: string) => void;
  onMaxQuestionsChange: (value: number) => void;
  onRunEvaluation: () => void;
}

export function BenchmarkSelector({
  benchmarks,
  strategies,
  selectedBenchmark,
  selectedStrategy,
  maxQuestions,
  isRunning,
  onBenchmarkChange,
  onStrategyChange,
  onMaxQuestionsChange,
  onRunEvaluation
}: BenchmarkSelectorProps) {
  const selectedBenchmarkObj = benchmarks.find(b => b.id === selectedBenchmark);
  const selectedStrategyObj = strategies.find(s => s.id === selectedStrategy);

  return (
    <Card className="bg-gray-900 border-gray-800">
      <CardHeader>
        <CardTitle className="text-gray-100">Run Benchmark Evaluation</CardTitle>
        <CardDescription className="text-gray-400">
          Configure and run evaluations to compare Single vs. Dual agent performance
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <div>
            <label className="text-sm font-medium text-gray-300 mb-2 block">
              Select Benchmark
            </label>
            <Select value={selectedBenchmark} onValueChange={onBenchmarkChange} disabled={isRunning}>
              <SelectTrigger className="w-full bg-gray-800 border-gray-700 text-gray-200">
                <SelectValue placeholder="Select a benchmark" />
              </SelectTrigger>
              <SelectContent className="bg-gray-800 border-gray-700">
                {benchmarks.map((benchmark) => (
                  <SelectItem 
                    key={benchmark.id} 
                    value={benchmark.id}
                    className="text-gray-200 focus:bg-gray-700 focus:text-gray-100"
                  >
                    {benchmark.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            {selectedBenchmarkObj && (
              <p className="mt-1 text-sm text-gray-400">{selectedBenchmarkObj.description}</p>
            )}
          </div>
          
          <div>
            <label className="text-sm font-medium text-gray-300 mb-2 block">
              Select Strategy
            </label>
            <Select value={selectedStrategy} onValueChange={onStrategyChange} disabled={isRunning}>
              <SelectTrigger className="w-full bg-gray-800 border-gray-700 text-gray-200">
                <SelectValue placeholder="Select a strategy" />
              </SelectTrigger>
              <SelectContent className="bg-gray-800 border-gray-700">
                {strategies.map((strategy) => (
                  <SelectItem 
                    key={strategy.id} 
                    value={strategy.id}
                    className="text-gray-200 focus:bg-gray-700 focus:text-gray-100"
                  >
                    {strategy.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            {selectedStrategyObj && (
              <p className="mt-1 text-sm text-gray-400">{selectedStrategyObj.description}</p>
            )}
          </div>
          
          <div>
            <label className="text-sm font-medium text-gray-300 mb-2 block">
              Maximum Questions
            </label>
            <Select 
              value={maxQuestions.toString()} 
              onValueChange={(value) => onMaxQuestionsChange(parseInt(value))}
              disabled={isRunning}
            >
              <SelectTrigger className="w-full bg-gray-800 border-gray-700 text-gray-200">
                <SelectValue placeholder="Select number of questions" />
              </SelectTrigger>
              <SelectContent className="bg-gray-800 border-gray-700">
                <SelectItem value="3" className="text-gray-200 focus:bg-gray-700 focus:text-gray-100">
                  3 questions (quick test)
                </SelectItem>
                <SelectItem value="5" className="text-gray-200 focus:bg-gray-700 focus:text-gray-100">
                  5 questions
                </SelectItem>
                <SelectItem value="10" className="text-gray-200 focus:bg-gray-700 focus:text-gray-100">
                  10 questions (full dataset)
                </SelectItem>
              </SelectContent>
            </Select>
          </div>
          
          <Button 
            className="w-full mt-4" 
            onClick={onRunEvaluation}
            disabled={isRunning}
          >
            {isRunning ? 
              <span className="flex items-center">
                <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Running Evaluation...
              </span> : 
              'Run Evaluation'
            }
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}