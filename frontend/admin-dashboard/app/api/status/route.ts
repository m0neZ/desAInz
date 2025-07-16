import { NextResponse } from 'next/server';

export async function GET() {
  const url = process.env.MONITORING_URL || 'http://localhost:8000';
  const res = await fetch(`${url}/overview`);
  const data = await res.json();
  return NextResponse.json(data);
}
