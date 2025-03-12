import { NextRequest } from 'next/server';

// Backend API URL
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5001';

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const debateId = searchParams.get('debateId');
  
  if (!debateId) {
    return new Response(
      JSON.stringify({ error: 'Missing debate ID' }),
      {
        status: 400,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  }
  
  try {
    // Create proxy to the backend SSE endpoint
    const backendUrl = `${API_URL}/api/stream/${debateId}`;
    console.log(`Connecting to backend SSE endpoint: ${backendUrl}`);
    
    const response = await fetch(backendUrl, {
      method: 'GET',
      headers: {
        'Accept': 'text/event-stream',
        'Cache-Control': 'no-cache',
      },
    });
    
    if (!response.ok) {
      console.error(`Backend SSE connection failed: ${response.status} ${response.statusText}`);
      return new Response(
        JSON.stringify({ 
          error: 'Failed to connect to backend stream',
          status: response.status,
          statusText: response.statusText
        }),
        {
          status: response.status,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }
    
    if (!response.body) {
      console.error('Backend SSE response has no body');
      return new Response(
        JSON.stringify({ error: 'Backend SSE response has no body' }),
        {
          status: 500,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }
    
    console.log('Successfully connected to backend SSE');
    
    // Create a TransformStream to avoid buffering
    const { readable, writable } = new TransformStream();
    response.body.pipeTo(writable);
    
    return new Response(readable, {
      headers: {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache, no-transform',
        'Connection': 'keep-alive',
        'X-Accel-Buffering': 'no', // Disable buffering in Nginx
      },
    });
  } catch (error) {
    console.error('Error proxying stream to backend:', error);
    return new Response(
      JSON.stringify({ error: 'Internal server error', details: String(error) }),
      {
        status: 500,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  }
}

// Need to export this configuration for streaming responses
export const dynamic = 'force-dynamic';
