'use client';

import React, { useState, useEffect } from 'react';
import { v4 as uuidv4 } from 'uuid';
import { ThemeProvider } from '../../components/ThemeProvider';
import { ThemeToggle } from '../../components/ThemeToggle';
import { BenchmarkSelector } from '../../components/evaluation/BenchmarkSelector';
import { ResultsTable } from '../../components/evaluation/ResultsTable';
import { ConversationViewer } from '../../components/evaluation/ConversationViewer';
import { Toaster, toast } from 'sonner';

// API functions - these will need to be implemented
import { 
  runEvaluation, 
  getEvaluationStatus, 
  getEvaluationResults,
  BenchmarkResult,
  ResultsSummary
} from '../api/evaluation';

// Benchmark type
interface Benchmark {
  id: string;
  name: string;
  description: string;
}

// Strategy type
interface Strategy {
  id: string;
  name: string;
  description: string;
}

// Sample benchmarks data
const benchmarks: Benchmark[] = [
  {
    id: 'simple',
    name: 'SimpleBench',
    description: 'A collection of seemingly simple problems that require real-world reasoning.'
  },
  {
    id: 'gpqa',
    name: 'GPQA (Coming Soon)',
    description: 'Graduate-level questions across various knowledge domains.'
  },
  {
    id: 'aime',
    name: 'AIME (Coming Soon)',
    description: 'American Invitational Mathematics Examination problems.'
  }
];

// Sample strategies data - same as in the main app
const strategies: Strategy[] = [
  {
    id: 'debate',
    name: 'Debate Strategy',
    description: 'A proponent presents arguments while a critic challenges them to find flaws.',
  },
  {
    id: 'cooperative',
    name: 'Cooperative Strategy',
    description: 'Two agents work collaboratively, building on each other\'s ideas.',
  },
  {
    id: 'teacher-student',
    name: 'Teacher-Student Strategy',
    description: 'An expert guides a learner through the problem-solving process.',
  }
];

export default function EvaluationPage() {
  const [selectedBenchmark, setSelectedBenchmark] = useState('simple');
  const [selectedStrategy, setSelectedStrategy] = useState('debate');
  const [maxQuestions, setMaxQuestions] = useState(5);
  const [isRunning, setIsRunning] = useState(false);
  const [evaluationId, setEvaluationId] = useState<string | null>(null);
  const [results, setResults] = useState<BenchmarkResult[] | null>(null);
  const [summary, setSummary] = useState<ResultsSummary | null>(null);
  const [selectedConversation, setSelectedConversation] = useState<string | null>(null);

  // Poll for status updates when an evaluation is running
  useEffect(() => {
    let intervalId: NodeJS.Timeout;
    
    if (isRunning && evaluationId) {
      intervalId = setInterval(async () => {
        try {
          const status = await getEvaluationStatus(evaluationId);
          
          if (status.status === 'completed') {
            setIsRunning(false);
            // Fetch the results
            const results = await getEvaluationResults(status.run_id!);
            setResults(results.results);
            setSummary(results.summary);
            toast.success('Evaluation completed successfully!');
          } else if (status.status === 'error') {
            setIsRunning(false);
            toast.error(`Evaluation failed: ${status.error}`);
          }
          // Otherwise, continue polling
        } catch (error) {
          console.error('Error checking evaluation status:', error);
          toast.error('Failed to check evaluation status');
          setIsRunning(false);
        }
      }, 3000); // Poll every 3 seconds
    }
    
    // Clean up on unmount
    return () => {
      if (intervalId) clearInterval(intervalId);
    };
  }, [isRunning, evaluationId]);

  const handleRunEvaluation = async () => {
    try {
      setIsRunning(true);
      setResults(null);
      setSummary(null);
      setSelectedConversation(null);
      
      // Run the evaluation
      const { evaluation_id } = await runEvaluation(selectedBenchmark, selectedStrategy, maxQuestions);
      
      setEvaluationId(evaluation_id);
      toast.success('Evaluation started!');
      
    } catch (error) {
      console.error('Failed to start evaluation:', error);
      setIsRunning(false);
      toast.error(`Error: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  };

  const handleSelectConversation = (logId: string) => {
    setSelectedConversation(logId);
  };

  return (
    <main className="min-h-screen bg-gray-950 text-gray-100">
      <Toaster richColors position="top-center" />
      <div className="container mx-auto py-8 px-4">
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-2xl font-bold">Benchmark Evaluation</h1>
          <ThemeToggle />
        </div>
        
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-1">
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
          </div>
          
          <div className="lg:col-span-2">
            {results && summary ? (
              <ResultsTable 
                results={results} 
                summary={summary}
                onSelectConversation={handleSelectConversation}
              />
            ) : (
              <div className="bg-gray-900 border border-gray-800 rounded-xl p-8 text-center">
                {isRunning ? (
                  <div className="flex flex-col items-center">
                    <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500 mb-4"></div>
                    <p className="text-gray-400">Running evaluation...</p>
                  </div>
                ) : (
                  <div>
                    <p className="text-gray-400 mb-2">No evaluation results yet.</p>
                    <p className="text-gray-500">Configure and run an evaluation to see results here.</p>
                  </div>
                )}
              </div>
            )}
            
            {selectedConversation && (
              <div className="mt-6">
                <ConversationViewer logId={selectedConversation} />
              </div>
            )}
          </div>
        </div>
      </div>
    </main>
  );
}
