import React, { useState } from 'react';
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";

// Sample problems for quick selection
const sampleProblems = [
  {
    title: "Ice Cubes Problem",
    text: "Beth places four whole ice cubes in a frying pan at the start of the first minute, then five at the start of the second minute and some more at the start of the third minute, but none in the fourth minute. If the average number of ice cubes per minute placed in the pan while it was frying a crispy egg was five, how many whole ice cubes can be found in the pan at the end of the third minute? Answer should be realistic and account for real-world conditions."
  },
  {
    title: "Probability Puzzle",
    text: "Alice and Bob play a game where they take turns rolling a fair six-sided die. The first person to roll a 6 wins. Alice goes first. What is the probability that Alice wins the game?"
  },
  {
    title: "Ethical Dilemma",
    text: "A self-driving car faces an unavoidable accident and must choose between hitting a group of five pedestrians who crossed against the light or swerving into a wall, which would likely kill the single passenger. What ethical framework should guide this decision and why?"
  }
];

interface ProblemFormProps {
  onSubmit: (problem: string) => void;
  isLoading: boolean;
}

export function ProblemForm({ onSubmit, isLoading }: ProblemFormProps) {
  const [problem, setProblem] = useState('');
  const [showSamples, setShowSamples] = useState(false);

  const handleSubmit = () => {
    if (problem.trim()) {
      onSubmit(problem.trim());
    }
  };

  const handleSampleClick = (sampleText: string) => {
    setProblem(sampleText);
    setShowSamples(false);
  };

  return (
    <Card className="mb-6 bg-gray-900 border-gray-800">
      <CardHeader>
        <CardTitle className="text-gray-100">Problem Input</CardTitle>
      </CardHeader>
      <CardContent>
        <Textarea
          placeholder="Enter a problem for the agents to solve..."
          className="min-h-32 bg-gray-800 border-gray-700 text-gray-100"
          value={problem}
          onChange={(e) => setProblem(e.target.value)}
        />
        <div className="mt-2 text-right">
          <Button variant="link" onClick={() => setShowSamples(!showSamples)}>
            {showSamples ? 'Hide Samples' : 'Show Sample Problems'}
          </Button>
        </div>
        
        {showSamples && (
          <div className="mt-2 space-y-2">
            {sampleProblems.map((sample, index) => (
              <div 
                key={index}
                className="p-2 rounded border border-gray-700 bg-gray-800 hover:bg-gray-700 cursor-pointer"
                onClick={() => handleSampleClick(sample.text)}
              >
                <div className="font-medium text-gray-200">{sample.title}</div>
                <div className="text-sm text-gray-400 truncate">{sample.text.substring(0, 100)}...</div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
      <CardFooter>
        <Button 
          className="w-full" 
          onClick={handleSubmit} 
          disabled={!problem.trim() || isLoading}
        >
          {isLoading ? 'Processing...' : 'Run Agents'}
        </Button>
      </CardFooter>
    </Card>
  );
}