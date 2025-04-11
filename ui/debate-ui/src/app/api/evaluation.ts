// This would typically be in src/app/api/evaluation.ts or similar

// Types for evaluation runs and results
export interface EvaluationRun {
  id: string;
  strategy: string;
  timestamp: string;
  benchmark: string;
}

export interface RunsResponse {
  runs: EvaluationRun[];
}

export interface ResultsSummary {
  total_questions: number;
  simulated_correct: number;
  dual_correct: number;
  simulated_accuracy: number;
  dual_accuracy: number;
}

export interface BenchmarkResult {
  question_id: string;
  question: string;
  ground_truth: string;
  category: string;
  difficulty: string;
  simulated: {
    answer: string;
    correct: boolean;
    time: number;
    log_id: string;
  };
  dual: {
    answer: string;
    correct: boolean;
    time: number;
    log_id: string;
  };
}

export interface EvaluationResultResponse {
  run_id: string;
  timestamp: string;
  benchmark: string;
  strategy: string;
  summary: ResultsSummary;
  results: BenchmarkResult[];
}

// Types for conversation logs
export interface MessageData {
  agent?: string;
  role?: string;
  content?: string;
  original_role?: string;
  original_content?: string;
}

export interface ConversationLog {
  question_id: string;
  question: string;
  ground_truth: string;
  strategy: string;
  benchmark: string;
  simulated_messages: MessageData[];
  dual_messages: MessageData[];
}

// API functions
export async function getEvaluationRuns(): Promise<RunsResponse> {
  const response = await fetch('/api/evaluation/runs');
  if (!response.ok) {
    throw new Error('Failed to fetch evaluation runs');
  }
  return response.json();
}

export async function getEvaluationResults(runId: string): Promise<EvaluationResultResponse> {
  const response = await fetch(`/api/evaluation/runs/${runId}`);
  if (!response.ok) {
    throw new Error(`Failed to fetch evaluation results for run ${runId}`);
  }
  return response.json();
}

export async function getConversationLog(logId: string): Promise<ConversationLog> {
  const response = await fetch(`/api/logs/${logId}`);
  if (!response.ok) {
    throw new Error(`Failed to fetch conversation log ${logId}`);
  }
  return response.json();
}

export async function runEvaluation(benchmarkId: string, strategyId: string, maxQuestions?: number) {
  const response = await fetch('/api/evaluation/run', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      benchmark_id: benchmarkId,
      strategy_id: strategyId,
      max_questions: maxQuestions
    })
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to start evaluation');
  }
  
  return response.json();
}

export async function getEvaluationStatus(evaluationId: string) {
  const response = await fetch(`/api/evaluation/status/${evaluationId}`);
  if (!response.ok) {
    throw new Error(`Failed to fetch status for evaluation ${evaluationId}`);
  }
  return response.json();
}