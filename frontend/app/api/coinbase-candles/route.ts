import { NextResponse } from 'next/server';

export async function GET(request: Request) {
    const { searchParams } = new URL(request.url);
    const start = searchParams.get('start');
    const end = searchParams.get('end');
    const granularity = searchParams.get('granularity');

    if (!start || !end || !granularity) {
        return NextResponse.json({ error: 'Missing required query parameters' }, { status: 400 });
    }

    const url = `https://api.coinbase.com/api/v3/brokerage/market/products/BTC-USD/candles?start=${start}&end=${end}&granularity=${granularity}`;

    try {
        const response = await fetch(url, { cache: 'no-store' });
        
        if (!response.ok) {
            return NextResponse.json(
                { error: `Coinbase API responded with status: ${response.status}` },
                { status: response.status }
            );
        }

        const data = await response.json();
        return NextResponse.json(data);
        
    } catch (error) {
        console.error("Coinbase proxy error:", error);
        return NextResponse.json(
            { error: 'Failed to fetch data from Coinbase' },
            { status: 500 }
        );
    }
}
