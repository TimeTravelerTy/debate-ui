'use client';

import React from 'react';
import { ResultsHistoryViewer } from '@/components/ResultsHistoryViewer';

export default function EvaluationHistoryPage() {
  return (
    <main className="container mx-auto py-8 px-4">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-100 mb-2">Evaluation History</h1>
        <p className="text-gray-400">
          Browse past benchmark evaluations and compare agent performance
        </p>
      </div>
      
      <ResultsHistoryViewer />
    </main>
  );
}