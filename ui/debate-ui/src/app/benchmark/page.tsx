'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { ResultsTable } from '@/components/evaluation/ResultsTable';
import { ConversationViewer } from '@/components/evaluation/ConversationViewer';
import { EvaluationRun, RunDetails, getEvaluationRuns, getEvaluationRunDetails } from '@/app/api/evaluation';
import { Loader2 } from 'lucide-react';
import { toast, Toaster } from 'sonner';

export default function BenchmarkPage() {
  const [runs, setRuns] = useState<EvaluationRun[]>([]);
  const [selectedRunId, setSelectedRunId] = useState<string>('');
  const [runData, setRunData] = useState<RunDetails | null>(null);
  const [selectedLogId, setSelectedLogId] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  
  // Fetch available runs
  useEffect(() => {
    async function fetchRuns() {
      setLoading(true);
      try {
        const data = await getEvaluationRuns();
        setRuns(data);
        // If there are runs and none selected, select the first one
        if (data.length > 0 && !selectedRunId) {
          setSelectedRunId(data[0].id);
        }
      } catch (error) {
        console.error("Error loading runs:", error);
        toast.error("Error loading evaluation runs");
      } finally {
        setLoading(false);
      }
    }
    
    fetchRuns();
  }, []);
  
  // Fetch specific run data
  useEffect(() => {
    if (!selectedRunId) return;
    
    async function fetchRunData() {
      setLoading(true);
      try {
        const data = await getEvaluationRunDetails(selectedRunId);
        setRunData(data);
        setSelectedLogId(null); // Reset selected log
      } catch (error) {
        console.error("Error loading run data:", error);
        toast.error("Error loading evaluation details");
      } finally {
        setLoading(false);
      }
    }
    
    fetchRunData();
  }, [selectedRunId]);
  
  return (
    <div className="container mx-auto py-8 px-4">
      <Toaster richColors position="top-center" />
      
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-2xl font-bold text-gray-100">Benchmark Results</h1>
        <Button 
          onClick={() => window.location.href = "/eval"}
          className="bg-gray-800 border-gray-700 hover:bg-gray-700"
        >
          Run New Evaluation
        </Button>
      </div>
      
      <div className="mb-6">
        <Card className="bg-gray-900 border-gray-800">
          <CardHeader>
            <CardTitle className="text-gray-100">Select Evaluation Run</CardTitle>
            <CardDescription className="text-gray-400">
              View results from previous benchmark evaluations
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex gap-4">
              <Select value={selectedRunId} onValueChange={setSelectedRunId} disabled={loading}>
                <SelectTrigger className="w-[350px] bg-gray-800 border-gray-700 text-gray-200">
                  <SelectValue placeholder="Select a run" />
                </SelectTrigger>
                <SelectContent className="bg-gray-800 border-gray-700">
                  {runs.map((run) => (
                    <SelectItem 
                      key={run.id} 
                      value={run.id}
                      className="text-gray-200 focus:bg-gray-700 focus:text-gray-100"
                    >
                      {run.strategy} - {new Date(run.timestamp).toLocaleString()} ({run.benchmark})
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </CardContent>
        </Card>
      </div>
      
      {loading && (
        <div className="flex justify-center my-12">
          <Loader2 className="h-8 w-8 animate-spin text-blue-500" />
        </div>
      )}
      
      {!loading && runData && (
        <div className="grid grid-cols-1 gap-6">
          <ResultsTable 
            results={runData.results} 
            summary={runData.summary} 
            onSelectConversation={setSelectedLogId}
          />
          
          <ConversationViewer logId={selectedLogId} />
        </div>
      )}
      
      {!loading && runs.length === 0 && (
        <Card className="bg-gray-900 border-gray-800 mt-8">
          <CardContent className="p-12 text-center">
            <div className="text-lg text-gray-400 mb-4">No evaluation runs found</div>
            <Button onClick={() => window.location.href = "/eval"}>
              Run Your First Evaluation
            </Button>
          </CardContent>
        </Card>
      )}
    </div>
  );
}