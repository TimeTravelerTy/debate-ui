import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Loader2, FileText, BarChart, ArrowLeft } from "lucide-react";
import { ConversationViewer } from "./evaluation/ConversationViewer";
import { ResultsTable } from "./evaluation/ResultsTable";
import { StrategyComparisonView } from "./evaluation/StrategyComparisonView";
import { 
  getEvaluationRuns,
  getEvaluationResults,
  getConversationLog,
  BenchmarkResult,
  ResultsSummary,
  EvaluationResultResponse
} from "@/app/api/evaluation";

// Interface for comparison summary data
interface ComparisonRun {
  id: string;
  benchmark: string;
  timestamp: string;
  strategies: string[];
  question_count: number;
  has_evolution_metrics: boolean;
}

// Simple table components
const Table: React.FC<React.PropsWithChildren<{ className?: string }>> = ({ className, children }) => (
  <div className="w-full overflow-auto">
    <table className={`w-full caption-bottom text-sm ${className || ''}`}>
      {children}
    </table>
  </div>
);

const TableHeader: React.FC<React.PropsWithChildren<{ className?: string }>> = ({ className, children }) => (
  <thead className={`[&_tr]:border-b ${className || ''}`}>
    {children}
  </thead>
);

const TableBody: React.FC<React.PropsWithChildren<{ className?: string }>> = ({ className, children }) => (
  <tbody className={`[&_tr:last-child]:border-0 ${className || ''}`}>
    {children}
  </tbody>
);

const TableRow: React.FC<React.PropsWithChildren<{ className?: string }>> = ({ className, children }) => (
  <tr className={`border-b transition-colors hover:bg-muted/50 data-[state=selected]:bg-muted ${className || ''}`}>
    {children}
  </tr>
);

const TableHead: React.FC<React.PropsWithChildren<{ className?: string }>> = ({ className, children }) => (
  <th className={`h-10 px-2 text-left align-middle font-medium text-muted-foreground [&:has([role=checkbox])]:pr-0 [&>[role=checkbox]]:translate-y-[2px] ${className || ''}`}>
    {children}
  </th>
);

const TableCell: React.FC<React.PropsWithChildren<{ className?: string }>> = ({ className, children }) => (
  <td className={`p-2 align-middle [&:has([role=checkbox])]:pr-0 [&>[role=checkbox]]:translate-y-[2px] ${className || ''}`}>
    {children}
  </td>
);

// Update the getComparisonList function with better error handling
async function getComparisonList(): Promise<{ comparisons: ComparisonRun[] }> {
  try {
    console.log("Fetching comparison list from /api/comparison/list");
    const response = await fetch('/api/comparison/list');
    
    console.log("Response status:", response.status);
    
    if (!response.ok) {
      const errorText = await response.text();
      console.error("Error response:", errorText);
      throw new Error(`Failed to fetch comparison list: ${response.status} ${response.statusText}`);
    }
    
    const data = await response.json();
    console.log("Received comparison data:", data);
    return data;
  } catch (error) {
    console.error('Error fetching comparison list:', error);
    // Return empty result instead of throwing to prevent component crash
    return { comparisons: [] };
  }
}

export const ResultsHistoryViewer: React.FC = () => {
  // View states
  const [mainView, setMainView] = useState<'runs' | 'comparisons'>('runs');
  const [detailsView, setDetailsView] = useState<'list' | 'details' | 'conversation'>('list');
  const [detailsTab, setDetailsTab] = useState<'results' | 'evolution'>('results');
  
  // Data states
  const [runs, setRuns] = useState<{ id: string; strategy: string; timestamp: string; benchmark: string }[]>([]);
  const [comparisons, setComparisons] = useState<ComparisonRun[]>([]);
  const [selectedRun, setSelectedRun] = useState<EvaluationResultResponse | null>(null);
  const [selectedComparisonId, setSelectedComparisonId] = useState<string | null>(null);
  const [selectedLogId, setSelectedLogId] = useState<string | null>(null);
  
  // Loading states
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Fetch list of runs and comparisons on component mount
  useEffect(() => {
    fetchData();
  }, []);
  
  // Function to fetch all required data
  const fetchData = async () => {
    setLoading(true);
    setError(null);
    
    try {
      // Fetch evaluation runs
      const runsData = await getEvaluationRuns();
      setRuns(runsData.runs);
      
      // Fetch comparisons
      try {
        const comparisonsData = await getComparisonList();
        setComparisons(comparisonsData.comparisons || []);
      } catch (err) {
        console.error('Error fetching comparisons:', err);
        // Continue with runs data only
      }
    } catch (err) {
      console.error('Error fetching data:', err);
      setError(err instanceof Error ? err.message : 'Failed to load evaluation history');
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
      setDetailsView('details');
      setDetailsTab('results'); // Default to results tab
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
    setDetailsView('conversation');
  };
  
  // Function to view a comparison
  const handleViewComparison = (comparisonId: string) => {
    setSelectedComparisonId(comparisonId);
    setDetailsView('details');
  };
  
  // Function to go back to the previous view
  const handleBack = () => {
    if (detailsView === 'conversation') {
      setDetailsView('details');
    } else if (detailsView === 'details') {
      setSelectedRun(null);
      setSelectedComparisonId(null);
      setDetailsView('list');
    }
  };
  
  // Render loading state
  if (loading && detailsView === 'list') {
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
  if (error && detailsView === 'list') {
    return (
      <Card className="bg-gray-900 border-gray-800">
        <CardContent className="pt-6">
          <div className="text-center p-6">
            <div className="text-red-500 mb-4">Error: {error}</div>
            <Button onClick={fetchData}>Try Again</Button>
          </div>
        </CardContent>
      </Card>
    );
  }
  
  // Render the conversation view
  if (detailsView === 'conversation' && selectedLogId) {
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
  
  // Render the details view for a specific run or comparison
  if (detailsView === 'details') {
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
            {selectedRun ? (
              <h2 className="text-xl font-semibold text-gray-100">
                {selectedRun.benchmark} - {selectedRun.strategy}
              </h2>
            ) : selectedComparisonId ? (
              <h2 className="text-xl font-semibold text-gray-100">
                Strategy Comparison
              </h2>
            ) : null}
            <p className="text-sm text-gray-400">
              {selectedRun ? new Date(selectedRun.timestamp).toLocaleString() : ''}
            </p>
          </div>
        </div>
        
        {selectedRun && (
          <Tabs value={detailsTab} onValueChange={(value) => setDetailsTab(value as 'results' | 'evolution')}>
            <TabsList className="bg-gray-800 border-gray-700">
              <TabsTrigger 
                value="results" 
                className="data-[state=active]:bg-gray-700 text-gray-300"
              >
                Results Table
              </TabsTrigger>
              <TabsTrigger 
                value="evolution" 
                className="data-[state=active]:bg-gray-700 text-gray-300"
              >
                Evolution Analysis
              </TabsTrigger>
            </TabsList>
            
            <TabsContent value="results">
              <ResultsTable 
                results={selectedRun.results}
                summary={selectedRun.summary}
                onSelectConversation={handleViewConversation}
              />
            </TabsContent>
            
            <TabsContent value="evolution">
              {/* Evolution analysis component would go here */}
              <Card className="bg-gray-900 border-gray-800">
                <CardContent className="p-6 text-center text-gray-400">
                  Evolution analysis views are available in strategy comparison reports.
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
        )}
        
        {selectedComparisonId && <StrategyComparisonView comparisonId={selectedComparisonId} />}
      </div>
    );
  }
  
  // Render the main view with tabs for runs and comparisons
  return (
    <Card className="bg-gray-900 border-gray-800">
      <CardHeader>
        <CardTitle className="text-gray-100">Evaluation Results</CardTitle>
        <CardDescription className="text-gray-400">
          View and compare benchmark evaluation results
        </CardDescription>
      </CardHeader>
      <CardContent>
        <Tabs value={mainView} onValueChange={(value) => setMainView(value as 'runs' | 'comparisons')}>
          <TabsList className="bg-gray-800 mb-4">
            <TabsTrigger 
              value="runs" 
              className="data-[state=active]:bg-gray-700 text-gray-300"
            >
              Individual Runs
            </TabsTrigger>
            <TabsTrigger 
              value="comparisons" 
              className="data-[state=active]:bg-gray-700 text-gray-300"
            >
              Strategy Comparisons
            </TabsTrigger>
          </TabsList>
          
          {/* Individual Runs Tab */}
          <TabsContent value="runs">
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
                onClick={fetchData}
                variant="outline"
                className="bg-gray-800 border-gray-700 hover:bg-gray-700"
              >
                Refresh
              </Button>
            </div>
          </TabsContent>
          
          {/* Strategy Comparisons Tab */}
          <TabsContent value="comparisons">
            {comparisons.length === 0 ? (
              <div className="text-center py-10 text-gray-400">
                No comparison reports found. Run a parallel benchmark evaluation from the terminal to see results here.
              </div>
            ) : (
              <div className="space-y-4">
                {comparisons.map((comparison) => (
                  <div 
                    key={comparison.id}
                    className="p-4 rounded-md bg-gray-800 border border-gray-700 hover:bg-gray-750 transition-colors"
                  >
                    <div className="flex justify-between items-start">
                      <div>
                        <h3 className="text-lg font-medium text-gray-200">{comparison.benchmark} Comparison</h3>
                        <div className="text-sm text-gray-400 mt-1">
                          {new Date(comparison.timestamp).toLocaleString()}
                        </div>
                        <div className="text-sm text-gray-400 mt-2">
                          <span className="text-gray-300">{comparison.question_count}</span> questions &bull; 
                          <span className="text-gray-300 ml-2">{comparison.strategies.length}</span> strategies
                          {comparison.has_evolution_metrics && (
                            <span className="ml-2 px-1.5 py-0.5 bg-blue-900/50 text-blue-300 text-xs rounded-full border border-blue-800/50">
                              Evolution Metrics
                            </span>
                          )}
                        </div>
                        <div className="flex flex-wrap gap-2 mt-2">
                          {comparison.strategies.map(strategy => (
                            <span 
                              key={strategy} 
                              className="px-2 py-1 bg-gray-700 text-gray-300 text-xs rounded-full"
                            >
                              {strategy}
                            </span>
                          ))}
                        </div>
                      </div>
                      <Button 
                        variant="outline"
                        size="sm"
                        className="bg-gray-800 border-gray-700 hover:bg-gray-700"
                        onClick={() => handleViewComparison(comparison.id)}
                      >
                        <BarChart className="h-4 w-4 mr-2" />
                        View Comparison
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            )}
            
            <div className="mt-4 text-right">
              <Button 
                onClick={fetchData}
                variant="outline"
                className="bg-gray-800 border-gray-700 hover:bg-gray-700"
              >
                Refresh
              </Button>
            </div>
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
}