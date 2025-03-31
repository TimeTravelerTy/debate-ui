// API client for evaluation endpoints
export interface BenchmarkResult {
    question_id: number;
    simulated: {
      correct: boolean;
      answer: string;
      time: number;
      log_id: string;
    };
    dual: {
      correct: boolean;
      answer: string;
      time: number;
      log_id: string;
    };
    ground_truth: string;
  }
  
  export interface ResultsSummary {
    simulated_accuracy: number;
    dual_accuracy: number;
    total_questions: number;
  }
  
  export interface EvaluationRun {
    id: string;
    strategy: string;
    timestamp: string;
    benchmark: string;
  }
  
  export interface RunDetails {
    run_id: string;
    strategy: string;
    timestamp: string;
    benchmark: string;
    results: BenchmarkResult[];
    summary: ResultsSummary;
  }
  
  export interface ConversationLog {
    question_id: number;
    question: string;
    simulated_messages: Array<{
      role: string;
      content: string;
      agent?: string;
    }>;
    dual_messages: Array<{
      role: string;
      content: string;
      agent?: string;
    }>;
  }
  
  export interface EvaluationRequest {
    benchmark_id: string;
    strategy_id: string;
    max_questions?: number;
  }
  
  // API functions
  export async function startEvaluation(request: EvaluationRequest): Promise<string> {
    const response = await fetch('/api/evaluation/run', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });
  
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.error || 'Failed to start evaluation');
    }
  
    const data = await response.json();
    return data.evaluation_id;
  }
  
  export async function getEvaluationRuns(): Promise<EvaluationRun[]> {
    const response = await fetch('/api/evaluation/runs');
    
    if (!response.ok) {
      throw new Error('Failed to fetch evaluation runs');
    }
    
    const data = await response.json();
    return data.runs || [];
  }
  
  export async function getEvaluationRunDetails(runId: string): Promise<RunDetails> {
    const response = await fetch(`/api/evaluation/runs/${runId}`);
    
    if (!response.ok) {
      throw new Error('Failed to fetch run details');
    }
    
    return await response.json();
  }
  
  export async function getConversationLog(logId: string): Promise<ConversationLog> {
    const response = await fetch(`/api/logs/${logId}`);
    
    if (!response.ok) {
      throw new Error('Failed to fetch conversation log');
    }
    
    return await response.json();
  }