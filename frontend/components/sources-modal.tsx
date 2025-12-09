'use client';

import { X, ExternalLink } from 'lucide-react';

interface Source {
  name: string;
  url: string;
  description: string;
}

interface SourcesModalProps {
  isOpen: boolean;
  onClose: () => void;
}

const NEWS_SOURCES: Source[] = [
  {
    name: 'Cointelegraph',
    url: 'https://cointelegraph.com',
    description: 'Breaking news and analysis on blockchain, cryptocurrency, and Bitcoin'
  },
  {
    name: 'Decrypt',
    url: 'https://decrypt.co',
    description: 'Demystifying cryptocurrency and blockchain'
  },
  {
    name: 'CoinDesk',
    url: 'https://www.coindesk.com',
    description: 'Leader in cryptocurrency news and information'
  },
  {
    name: 'Bitcoin Magazine',
    url: 'https://bitcoinmagazine.com',
    description: 'The oldest and most established source of Bitcoin news'
  },
  {
    name: 'Crypto Briefing',
    url: 'https://cryptobriefing.com',
    description: 'Research-driven analysis and commentary on blockchain'
  },
  {
    name: 'Reuters Crypto',
    url: 'https://www.reuters.com/technology/cryptocurrency',
    description: 'Cryptocurrency coverage from Reuters news agency'
  },
  {
    name: 'Bloomberg Markets',
    url: 'https://www.bloomberg.com/markets',
    description: 'Financial markets news including cryptocurrency'
  },
  {
    name: 'Financial Times',
    url: 'https://www.ft.com/cryptofinance',
    description: 'Cryptocurrencies and blockchain coverage'
  },
  {
    name: 'The Block',
    url: 'https://www.theblock.co',
    description: 'Leading source for crypto news and research'
  },
  {
    name: 'CryptoSlate',
    url: 'https://cryptoslate.com',
    description: 'Cryptocurrency news, analysis, and research'
  },
  {
    name: 'Google News (Bitcoin)',
    url: 'https://news.google.com/search?q=Bitcoin',
    description: 'Aggregated Bitcoin news from various sources'
  }
];

const REDDIT_SOURCES: Source[] = [
  {
    name: 'r/cryptocurrency',
    url: 'https://reddit.com/r/cryptocurrency',
    description: 'General cryptocurrency discussion and news'
  },
  {
    name: 'r/bitcoin',
    url: 'https://reddit.com/r/bitcoin',
    description: 'Bitcoin-specific discussion and community'
  },
  {
    name: 'r/CryptoMarkets',
    url: 'https://reddit.com/r/CryptoMarkets',
    description: 'Cryptocurrency market discussion and analysis'
  },
  {
    name: 'r/BitcoinMarkets',
    url: 'https://reddit.com/r/BitcoinMarkets',
    description: 'Bitcoin trading and market discussion'
  },
  {
    name: 'r/ethtrader',
    url: 'https://reddit.com/r/ethtrader',
    description: 'Ethereum trading community (Bitcoin mentions)'
  },
  {
    name: 'r/CryptoCurrencyTrading',
    url: 'https://reddit.com/r/CryptoCurrencyTrading',
    description: 'Cryptocurrency trading strategies'
  },
  {
    name: 'r/defi',
    url: 'https://reddit.com/r/defi',
    description: 'Decentralized finance discussion (Bitcoin context)'
  },
  {
    name: 'r/cryptotechnology',
    url: 'https://reddit.com/r/cryptotechnology',
    description: 'Technical cryptocurrency discussion'
  }
];

export function SourcesModal({ isOpen, onClose }: SourcesModalProps) {
  if (!isOpen) return null;

  return (
    <>
      {/* Backdrop */}
      <div 
        className="fixed inset-0 bg-black/50 backdrop-blur-sm z-40"
        onClick={onClose}
      />
      
      {/* Modal */}
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
        <div className="bg-background border rounded-lg shadow-2xl max-w-4xl w-full max-h-[80vh] overflow-hidden">
          {/* Header */}
          <div className="flex items-center justify-between p-6 border-b">
            <div>
              <h2 className="text-2xl font-bold">Data Sources</h2>
              <p className="text-sm text-muted-foreground mt-1">
                We analyze sentiment from {NEWS_SOURCES.length} news outlets and {REDDIT_SOURCES.length} Reddit communities
              </p>
            </div>
            <button
              onClick={onClose}
              className="p-2 hover:bg-accent rounded-lg transition-colors"
              aria-label="Close"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
          
          {/* Content */}
          <div className="overflow-y-auto max-h-[calc(80vh-120px)] p-6">
            {/* News Sources */}
            <div className="mb-8">
              <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                📰 News Outlets
                <span className="text-sm font-normal text-muted-foreground">({NEWS_SOURCES.length})</span>
              </h3>
              <div className="grid md:grid-cols-2 gap-3">
                {NEWS_SOURCES.map((source) => (
                  <a
                    key={source.name}
                    href={source.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="block p-4 border rounded-lg hover:bg-accent transition-colors group"
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <h4 className="font-medium group-hover:text-primary transition-colors flex items-center gap-2">
                          {source.name}
                          <ExternalLink className="w-3 h-3" />
                        </h4>
                        <p className="text-sm text-muted-foreground mt-1">
                          {source.description}
                        </p>
                      </div>
                    </div>
                  </a>
                ))}
              </div>
            </div>
            
            {/* Reddit Sources */}
            <div>
              <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                💬 Reddit Communities
                <span className="text-sm font-normal text-muted-foreground">({REDDIT_SOURCES.length})</span>
              </h3>
              <div className="grid md:grid-cols-2 gap-3">
                {REDDIT_SOURCES.map((source) => (
                  <a
                    key={source.name}
                    href={source.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="block p-4 border rounded-lg hover:bg-accent transition-colors group"
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <h4 className="font-medium group-hover:text-primary transition-colors flex items-center gap-2">
                          {source.name}
                          <ExternalLink className="w-3 h-3" />
                        </h4>
                        <p className="text-sm text-muted-foreground mt-1">
                          {source.description}
                        </p>
                      </div>
                    </div>
                  </a>
                ))}
              </div>
            </div>
            
            {/* Info Footer */}
            <div className="mt-8 p-4 bg-muted/50 rounded-lg">
              <p className="text-sm text-muted-foreground">
                <strong>Note:</strong> Reddit posts are filtered to only include Bitcoin-related content using keywords: 
                bitcoin, btc, sats, satoshi, lightning network, taproot, segwit, halving, mining, hash rate, and difficulty.
              </p>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
