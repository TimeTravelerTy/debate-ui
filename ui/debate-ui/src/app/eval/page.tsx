'use client';

import React, { useState } from 'react';
import { BenchmarkSelector } from '@/components/evaluation/BenchmarkSelector';
import { startEvaluation } from '@/app/api/evaluation';
import { Toaster, toast } from 'sonner';
import { Button } from '@/components/ui/button';

// Available benchmarks
const benchmarks = [
  {
    id: 'simple',
    name: 'SimpleBench',
    description: 'Simple questions for humans that challenge LLMs'
  },
  // Add more benchmarks as they become available
];

// Available strategies
const strategies = [
  {
    id: 'debate',
    name: 'Debate Strategy',
    description: 'A proponent presents arguments while a critic challenges them to find flaws.'
  },
  {
    id: 'cooperative',
    name: 'Cooperative Strategy',
    description: 'Two agents work collaboratively, building on each other\'s ideas.'
  },
  {
    id: 'teacher-student',
    name: 'Teacher-Student Strategy',
    description: 'An expert guides a learner through the problem-solving process.'
  }
];

export default function EvaluationPage() {
  const [selectedBenchmark, setSelectedBenchmark] = useState<string>('simple');
  const [selectedStrategy, setSelectedStrategy] = useState<string>('debate');
  const [maxQuestions, setMaxQuestions] = useState<number>(5);
  const [isRunning, setIsRunning] = useState<boolean>(false);
  const [lastRunId, setLastRunId] = useState<string | null>(null);

  const handleRunEvaluation = async () => {
    setIsRunning(true);
    try {
      const evaluationId = await startEvaluation({
        benchmark_id: selectedBenchmark,
        strategy_id: selectedStrategy,
        max_questions: maxQuestions
      });
      setLastRunId(evaluationId);
      
      // Show success notification
      toast.success('Evaluation started successfully!', {
        description: `Evaluation ID: ${evaluationId}`,
        action: {
          label: 'View Results',
          onClick: () => window.location.href = `/benchmark?run=${evaluationId}`
        }
      });
      
      // Redirect to results after a short delay
      setTimeout(() => {
        window.location.href = `/benchmark?run=${evaluationId}`;
      }, 3000);
      
    } catch (error) {
      console.error('Error starting evaluation:', error);
      toast.error('Failed to start evaluation', {
        description: error instanceof Error ? error.message : 'Unknown error'
      });
    } finally {
      setIsRunning(false);
    }
  };

  return (
    <div className="container mx-auto py-8 px-4">
      <Toaster richColors position="top-center" />
      
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-2xl font-bold text-gray-100">Run Benchmark Evaluation</h1>
        {lastRunId && (
          <Button 
            variant="outline" 
            onClick={() => window.location.href = `/benchmark?run=${lastRunId}`}
            className="bg-gray-800 border-gray-700 hover:bg-gray-700 text-gray-200"
          >
            View Last Results
          </Button>
        )}
      </div>
      
      <div className="grid grid-cols-1 gap-6">
        <BenchmarkSelector 
          benchmarks={benchmarks}
          strategies={strategies}
          selectedBenchmark={selectedBenchmark}
          selectedStrategy={selectedStrategy}
          maxQuestions={maxQuestions}
          isRunning={isRunning}
          onBenchmarkChange={setSelectedBenchmark}
          onStrategyChange={setSelectedStrategy}
          onMaxQuestionsChange={setMaxQuestions}
          onRunEvaluation={handleRunEvaluation}
        />
        
        <div className="bg-gray-900 border border-gray-800 rounded-lg p-5">
          <h2 className="text-lg font-medium text-gray-100 mb-4">Evaluation Process</h2>
          <div className="space-y-3 text-gray-300">
            <p>
              When you run a benchmark evaluation, the system will:
            </p>
            <ol className="list-decimal list-inside space-y-2 pl-2">
              <li>Load questions from the selected benchmark</li>
              <li>Run both single-agent (simulated) and dual-agent approaches on each question</li>
              <li>Evaluate the responses against the benchmark's ground truth</li>
              <li>Generate detailed logs of all conversations</li>
              <li>Prepare a summary report for comparison</li>
            </ol>
            <p className="text-gray-400 mt-4">
              This process may take several minutes to complete depending on the number of questions
              and the complexity of the strategy.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

