import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Loader2, FileText, BarChart, ArrowLeft } from "lucide-react";
import { ConversationViewer } from "./evaluation/ConversationViewer";
import { ResultsTable } from "./evaluation/ResultsTable";
import { 
  getEvaluationRuns,
  getEvaluationResults,
  getConversationLog,
  BenchmarkResult,
  ResultsSummary,
  EvaluationResultResponse
} from "@/app/api/evaluation";

// Table components (copied from ui/table.tsx to avoid import issues)
const Table = React.forwardRef<
  HTMLTableElement,
  React.HTMLAttributes<HTMLTableElement>
>(({ className, ...props }, ref) => (
  <div className="w-full overflow-auto">
    <table
      ref={ref}
      className={`w-full caption-bottom text-sm ${className || ''}`}
      {...props}
    />
  </div>
));
Table.displayName = "Table";

const TableHeader = React.forwardRef<
  HTMLTableSectionElement,
  React.HTMLAttributes<HTMLTableSectionElement>
>(({ className, ...props }, ref) => (
  <thead ref={ref} className={`[&_tr]:border-b ${className || ''}`} {...props} />
));
TableHeader.displayName = "TableHeader";

const TableBody = React.forwardRef<
  HTMLTableSectionElement,
  React.HTMLAttributes<HTMLTableSectionElement>
>(({ className, ...props }, ref) => (
  <tbody
    ref={ref}
    className={`[&_tr:last-child]:border-0 ${className || ''}`}
    {...props}
  />
));
TableBody.displayName = "TableBody";

const TableRow = React.forwardRef<
  HTMLTableRowElement,
  React.HTMLAttributes<HTMLTableRowElement>
>(({ className, ...props }, ref) => (
  <tr
    ref={ref}
    className={`border-b transition-colors hover:bg-muted/50 data-[state=selected]:bg-muted ${className || ''}`}
    {...props}
  />
));
TableRow.displayName = "TableRow";

const TableHead = React.forwardRef<
  HTMLTableCellElement,
  React.ThHTMLAttributes<HTMLTableCellElement>
>(({ className, ...props }, ref) => (
  <th
    ref={ref}
    className={`h-10 px-2 text-left align-middle font-medium text-muted-foreground [&:has([role=checkbox])]:pr-0 [&>[role=checkbox]]:translate-y-[2px] ${className || ''}`}
    {...props}
  />
));
TableHead.displayName = "TableHead";

const TableCell = React.forwardRef<
  HTMLTableCellElement,
  React.TdHTMLAttributes<HTMLTableCellElement>
>(({ className, ...props }, ref) => (
  <td
    ref={ref}
    className={`p-2 align-middle [&:has([role=checkbox])]:pr-0 [&>[role=checkbox]]:translate-y-[2px] ${className || ''}`}
    {...props}
  />
));
TableCell.displayName = "TableCell";

export function ResultsHistoryViewer() {
  // View states
  const [view, setView] = useState<'list' | 'details' | 'conversation'>('list');
  
  // Data states
  const [runs, setRuns] = useState<{ id: string; strategy: string; timestamp: string; benchmark: string }[]>([]);
  const [selectedRun, setSelectedRun] = useState<EvaluationResultResponse | null>(null);
  const [selectedLogId, setSelectedLogId] = useState<string | null>(null);
  
  // Loading states
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Fetch list of runs on component mount
  useEffect(() => {
    fetchRunsList();
  }, []);
  
  // Function to fetch list of evaluation runs
  const fetchRunsList = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const data = await getEvaluationRuns();
      setRuns(data.runs);
    } catch (err) {
      console.error('Error fetching runs:', err);
      setError(err instanceof Error ? err.message : 'Failed to load results history');
    } finally {
      setLoading(false);
    }
  };
  
  // Function to fetch details of a specific run
  const fetchRunDetails = async (runId: string) => {
    setLoading(true);
    setError(null);
    
    try {
      const data = await getEvaluationResults(runId);
      setSelectedRun(data);
      setView('details');
    } catch (err) {
      console.error('Error fetching run details:', err);
      setError(err instanceof Error ? err.message : 'Failed to load run details');
    } finally {
      setLoading(false);
    }
  };
  
  // Function to handle selecting a conversation to view
  const handleViewConversation = (logId: string) => {
    setSelectedLogId(logId);
    setView('conversation');
  };
  
  // Function to go back to the previous view
  const handleBack = () => {
    if (view === 'conversation') {
      setView('details');
    } else if (view === 'details') {
      setSelectedRun(null);
      setView('list');
    }
  };
  
  // Render loading state
  if (loading && view === 'list') {
    return (
      <Card className="bg-gray-900 border-gray-800">
        <CardContent className="pt-6 flex justify-center items-center h-64">
          <div className="text-center">
            <Loader2 className="h-8 w-8 animate-spin text-blue-500 mx-auto mb-4" />
            <p className="text-gray-400">Loading evaluation history...</p>
          </div>
        </CardContent>
      </Card>
    );
  }
  
  // Render error state
  if (error) {
    return (
      <Card className="bg-gray-900 border-gray-800">
        <CardContent className="pt-6">
          <div className="text-center p-6">
            <div className="text-red-500 mb-4">Error: {error}</div>
            <Button onClick={fetchRunsList}>Try Again</Button>
          </div>
        </CardContent>
      </Card>
    );
  }
  
  // Render the list of runs
  if (view === 'list') {
    return (
      <Card className="bg-gray-900 border-gray-800">
        <CardHeader>
          <CardTitle className="text-gray-100">Evaluation History</CardTitle>
          <CardDescription className="text-gray-400">
            Past benchmark evaluations and their results
          </CardDescription>
        </CardHeader>
        <CardContent>
          {runs.length === 0 ? (
            <div className="text-center py-10 text-gray-400">
              No evaluation runs found. Run a benchmark evaluation to see results here.
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow className="border-gray-700">
                  <TableHead className="text-gray-300">Run ID</TableHead>
                  <TableHead className="text-gray-300">Benchmark</TableHead>
                  <TableHead className="text-gray-300">Strategy</TableHead>
                  <TableHead className="text-gray-300">Timestamp</TableHead>
                  <TableHead className="text-gray-300">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {runs.map((run) => (
                  <TableRow key={run.id} className="border-gray-800 hover:bg-gray-800/50">
                    <TableCell className="text-gray-300 font-mono text-sm">{run.id.substring(0, 8)}...</TableCell>
                    <TableCell className="text-gray-300">{run.benchmark}</TableCell>
                    <TableCell className="text-gray-300">{run.strategy}</TableCell>
                    <TableCell className="text-gray-300">
                      {new Date(run.timestamp).toLocaleString()}
                    </TableCell>
                    <TableCell>
                      <Button 
                        variant="outline"
                        size="sm"
                        className="bg-gray-800 border-gray-700 hover:bg-gray-700"
                        onClick={() => fetchRunDetails(run.id)}
                      >
                        <FileText className="h-4 w-4 mr-2" />
                        View Details
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
          
          <div className="mt-4 text-right">
            <Button 
              onClick={fetchRunsList}
              variant="outline"
              className="bg-gray-800 border-gray-700 hover:bg-gray-700"
            >
              Refresh
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }
  
  // Render run details view
  if (view === 'details' && selectedRun) {
    return (
      <div className="space-y-4">
        <div className="flex items-center mb-4">
          <Button
            variant="outline"
            size="sm"
            className="bg-gray-800 border-gray-700 hover:bg-gray-700"
            onClick={handleBack}
          >
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to List
          </Button>
          
          <div className="ml-4">
            <h2 className="text-xl font-semibold text-gray-100">
              {selectedRun.benchmark} - {selectedRun.strategy}
            </h2>
            <p className="text-sm text-gray-400">
              {new Date(selectedRun.timestamp).toLocaleString()}
            </p>
          </div>
        </div>
        
        <ResultsTable 
          results={selectedRun.results}
          summary={selectedRun.summary}
          onSelectConversation={handleViewConversation}
        />
      </div>
    );
  }
  
  // Render conversation view
  if (view === 'conversation' && selectedLogId) {
    return (
      <div className="space-y-4">
        <Button
          variant="outline"
          size="sm"
          className="bg-gray-800 border-gray-700 hover:bg-gray-700 mb-4"
          onClick={handleBack}
        >
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back to Results
        </Button>
        
        <ConversationViewer logId={selectedLogId} />
      </div>
    );
  }
  
  // Fallback view
  return (
    <Card className="bg-gray-900 border-gray-800">
      <CardContent className="pt-6">
        <div className="text-center p-6">
          <div className="text-gray-400 mb-4">No data to display</div>
          <Button onClick={() => setView('list')}>Go to Results List</Button>
        </div>
      </CardContent>
    </Card>
  );
}