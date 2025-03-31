import React from 'react';
import { Table, TableHeader, TableBody, TableRow, TableCell } from "../ui/table";
import { Card, CardHeader, CardTitle, CardContent } from "../ui/card";
import { BenchmarkResult, ResultsSummary } from '@/app/api/evaluation';

interface ResultsTableProps {
  results: BenchmarkResult[];
  summary: ResultsSummary;
  onSelectConversation: (logId: string) => void;
}

export function ResultsTable({ results, summary, onSelectConversation }: ResultsTableProps) {
  return (
    <div className="space-y-6">
      <Card className="bg-gray-900 border-gray-800">
        <CardHeader>
          <CardTitle className="text-gray-100">Summary Results</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-3 gap-4">
            <div className="bg-blue-900/30 p-4 rounded-md border border-blue-800/50">
              <div className="text-xl font-bold text-blue-300">
                {(summary.simulated_accuracy * 100).toFixed(1)}%
              </div>
              <div className="text-sm text-blue-200">Single Agent Accuracy</div>
            </div>
            <div className="bg-amber-900/30 p-4 rounded-md border border-amber-800/50">
              <div className="text-xl font-bold text-amber-300">
                {(summary.dual_accuracy * 100).toFixed(1)}%
              </div>
              <div className="text-sm text-amber-200">Dual Agent Accuracy</div>
            </div>
            <div className="bg-purple-900/30 p-4 rounded-md border border-purple-800/50">
              <div className="text-xl font-bold text-purple-300">
                {summary.total_questions}
              </div>
              <div className="text-sm text-purple-200">Total Questions</div>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card className="bg-gray-900 border-gray-800">
        <CardHeader>
          <CardTitle className="text-gray-100">Detailed Results</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow className="border-gray-700">
                  <TableCell className="text-gray-300 font-medium">Question</TableCell>
                  <TableCell className="text-gray-300 font-medium">Ground Truth</TableCell>
                  <TableCell className="text-gray-300 font-medium">Single Agent</TableCell>
                  <TableCell className="text-gray-300 font-medium">Dual Agent</TableCell>
                  <TableCell className="text-gray-300 font-medium">Actions</TableCell>
                </TableRow>
              </TableHeader>
              <TableBody>
                {results.map((result) => (
                  <TableRow key={result.question_id} className="border-gray-800 hover:bg-gray-800/50">
                    <TableCell className="text-gray-300">{result.question_id}</TableCell>
                    <TableCell className="text-gray-300 font-medium">{result.ground_truth}</TableCell>
                    <TableCell className={result.simulated.correct ? "text-green-500" : "text-red-500"}>
                      {result.simulated.answer} ({result.simulated.time.toFixed(1)}s)
                    </TableCell>
                    <TableCell className={result.dual.correct ? "text-green-500" : "text-red-500"}>
                      {result.dual.answer} ({result.dual.time.toFixed(1)}s)
                    </TableCell>
                    <TableCell>
                      <button 
                        onClick={() => onSelectConversation(result.simulated.log_id)}
                        className="text-blue-400 hover:text-blue-300 underline"
                      >
                        View Details
                      </button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}