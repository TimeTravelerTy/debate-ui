'use client';
import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Button } from './ui/button';
import { ThemeToggle } from './ThemeToggle';

export function Navigation() {
  const pathname = usePathname();
  
  const isActive = (path: string) => {
    return pathname === path;
  };
  
  return (
    <div className="bg-gray-900 border-b border-gray-800">
      <div className="container mx-auto py-4 px-4">
        <div className="flex justify-between items-center">
          <div className="flex items-center gap-2">
            <span className="text-xl font-bold text-gray-100">Agent Debate Lab</span>
          </div>
          
          <div className="flex items-center gap-4">
            <nav className="flex items-center space-x-4 mr-4">
              <Link 
                href="/" 
                className={`text-sm font-medium transition-colors ${
                  isActive('/') 
                    ? 'text-white border-b-2 border-blue-500 py-1' 
                    : 'text-gray-400 hover:text-gray-100'
                }`}
              >
                Debate
              </Link>
              
              <Link 
                href="/evaluation" 
                className={`text-sm font-medium transition-colors ${
                  isActive('/evaluation') 
                    ? 'text-white border-b-2 border-blue-500 py-1' 
                    : 'text-gray-400 hover:text-gray-100'
                }`}
              >
                Benchmark Evaluation
              </Link>
            </nav>
            
            <ThemeToggle />
          </div>
        </div>
      </div>
    </div>
  );
}