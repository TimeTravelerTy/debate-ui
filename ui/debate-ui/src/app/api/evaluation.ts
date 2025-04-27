// Types for the evaluation API

/**
 * Answer history item for evolution analysis
 */
export interface AnswerHistoryItem {
  turn: number;
  agent: string;
  answer: string;
  is_correct: boolean;
}

/**
 * Evolution analysis data
 */
export interface EvolutionData {
  agreement_pattern: string;
  correctness_pattern: string;
  answer_history: AnswerHistoryItem[];
}

/**
 * System message containing a benchmark run result
 */
export interface SystemMessage {
  role: 'system';
  content: string;
}

/**
 * User message containing a question
 */
export interface UserMessage {
  role: 'user';
  content: string;
}

/**
 * Agent message from the conversation
 */
export interface AgentMessage {
  role: string;
  agent?: string;
  content: string;
  original_role?: string;
  original_content?: string;
}

/**
 * Conversation log for a specific question/dialogue
 */
export interface ConversationLog {
  question_id: string;
  question: string;
  ground_truth: string;
  strategy: string;
  benchmark: string;
  simulated_messages: AgentMessage[];
  dual_messages: AgentMessage[];
  simulated_evolution?: EvolutionData;
  dual_evolution?: EvolutionData;
}

/**
 * Result for a single approach (either simulated or dual)
 */
export interface ApproachResult {
  answer: string;
  correct: boolean;
  time: number;
  log_id: string;
  evolution?: {
    agreement_pattern: string;
    correctness_pattern: string;
  };
}

/**
 * Result for a single benchmark question
 */
export interface BenchmarkResult {
  question_id: string;
  question: string;
  ground_truth: string;
  category: string;
  difficulty: string;
  simulated: ApproachResult;
  dual: ApproachResult;
}

/**
 * Summary of benchmark results
 */
export interface ResultsSummary {
  total_questions: number;
  simulated_correct: number;
  dual_correct: number;
  simulated_accuracy: number;
  dual_accuracy: number;
}

/**
 * Response from the evaluation results API
 */
export interface EvaluationResultResponse {
  run_id: string;
  timestamp: string;
  benchmark: string;
  strategy: string;
  summary: ResultsSummary;
  results: BenchmarkResult[];
}

/**
 * Fetch a list of available evaluation runs
 */
export async function getEvaluationRuns() {
  const response = await fetch('/api/evaluation/runs');
  if (!response.ok) {
    throw new Error('Failed to fetch evaluation runs');
  }
  return response.json();
}

/**
 * Fetch detailed results for a specific evaluation run
 * @param runId The ID of the run to fetch
 */
export async function getEvaluationResults(runId: string): Promise<EvaluationResultResponse> {
  const response = await fetch(`/api/evaluation/runs/${runId}`);
  if (!response.ok) {
    throw new Error('Failed to fetch evaluation results');
  }
  return response.json();
}

/**
 * Fetch a specific conversation log
 * @param logId The ID of the conversation log to fetch
 */
export async function getConversationLog(logId: string): Promise<ConversationLog> {
  const response = await fetch(`/api/logs/${logId}`);
  if (!response.ok) {
    throw new Error('Failed to fetch conversation log');
  }
  return response.json();
}