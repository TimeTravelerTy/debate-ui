// Types for evaluation API

export interface EvaluationRequest {
  benchmark_id: string;
  strategy_id: string;
  max_questions?: number;
}

export interface EvaluationStatusResponse {
  id: string;
  benchmark_id: string;
  strategy_id: string;
  status: 'pending' | 'running' | 'completed' | 'error';
  run_id?: string;
  error?: string;
  progress?: {
    current: number;
    total: number;
  };
}

export interface ResultItem {
  answer: string;
  correct: boolean;
  time: number;
  log_id: string;
}

export interface BenchmarkResult {
  question_id: string;
  question: string;
  ground_truth: string;
  simulated: ResultItem;
  dual: ResultItem;
}

export interface ResultsSummary {
  total_questions: number;
  simulated_accuracy: number;
  dual_accuracy: number;
  simulated_time_avg: number;
  dual_time_avg: number;
}

export interface EvaluationResultResponse {
  run_id: string;
  strategy: string;
  benchmark: string;
  timestamp: string;
  summary: ResultsSummary;
  results: BenchmarkResult[];
}

export interface ConversationMessage {
  role: string;
  agent?: string;
  content: string;
}

export interface ConversationLog {
  log_id: string;
  question_id: string;
  question: string;
  simulated_messages: ConversationMessage[];
  dual_messages: ConversationMessage[];
}

// API functions

export const runEvaluation = async (request: EvaluationRequest): Promise<{ evaluation_id: string }> => {
  try {
    const response = await fetch('/api/evaluation/run', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });
    
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Failed to start evaluation');
    }
    
    return await response.json();
  } catch (error) {
    console.error('Error in runEvaluation:', error);
    throw error;
  }
};

export const getEvaluationStatus = async (evaluationId: string): Promise<EvaluationStatusResponse> => {
  try {
    const response = await fetch(`/api/evaluation/status/${evaluationId}`);
    
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Failed to get evaluation status');
    }
    
    return await response.json();
  } catch (error) {
    console.error('Error in getEvaluationStatus:', error);
    throw error;
  }
};

export const getEvaluationResults = async (runId: string): Promise<EvaluationResultResponse> => {
  try {
    const response = await fetch(`/api/evaluation/runs/${runId}`);
    
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Failed to get evaluation results');
    }
    
    return await response.json();
  } catch (error) {
    console.error('Error in getEvaluationResults:', error);
    throw error;
  }
};

export const getEvaluationRuns = async (): Promise<{ runs: { id: string; strategy: string; timestamp: string; benchmark: string }[] }> => {
  try {
    const response = await fetch('/api/evaluation/runs');
    
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Failed to get evaluation runs');
    }
    
    return await response.json();
  } catch (error) {
    console.error('Error in getEvaluationRuns:', error);
    throw error;
  }
};

export const getConversationLog = async (logId: string): Promise<ConversationLog> => {
  try {
    const response = await fetch(`/api/logs/${logId}`);
    
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Failed to get conversation log');
    }
    
    return await response.json();
  } catch (error) {
    console.error('Error in getConversationLog:', error);
    throw error;
  }
};