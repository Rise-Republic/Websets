import React, { useState } from 'react';
import { 
  Card, 
  CardContent, 
  CardDescription, 
  CardHeader, 
  CardTitle 
} from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { 
  Search, 
  Filter, 
  SlidersHorizontal,
  Download,
  BookmarkPlus,
  ExternalLink,
  Clock,
  Database,
  Zap
} from 'lucide-react';

interface SearchResult {
  id: string;
  title: string;
  content: string;
  source: string;
  url: string;
  similarity: number;
  timestamp: string;
  dataset: string;
  metadata: Record<string, any>;
}

const SearchInterface: React.FC = () => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [selectedFilters, setSelectedFilters] = useState<string[]>([]);

  const mockResults: SearchResult[] = [
    {
      id: '1',
      title: 'Advanced Machine Learning Techniques for Data Mining',
      content: 'This comprehensive guide explores cutting-edge machine learning algorithms and their applications in large-scale data mining operations. The document covers neural networks, deep learning architectures, and ensemble methods...',
      source: 'TechResearch.com',
      url: 'https://techresearch.com/ml-techniques',
      similarity: 0.95,
      timestamp: '2024-01-15T10:30:00Z',
      dataset: 'Tech Articles',
      metadata: {
        author: 'Dr. Sarah Chen',
        category: 'Machine Learning',
        readTime: '12 min'
      }
    },
    {
      id: '2',
      title: 'Enterprise Data Architecture Best Practices',
      content: 'Building scalable data architectures for enterprise applications requires careful consideration of performance, security, and maintainability. This article discusses modern approaches to data modeling...',
      source: 'Enterprise Weekly',
      url: 'https://enterpriseweekly.com/data-architecture',
      similarity: 0.87,
      timestamp: '2024-01-14T15:45:00Z',
      dataset: 'Business Articles',
      metadata: {
        author: 'Michael Rodriguez',
        category: 'Data Architecture',
        readTime: '8 min'
      }
    },
    {
      id: '3',
      title: 'Real-time Analytics with Vector Databases',
      content: 'Vector databases are revolutionizing how we handle similarity search and real-time analytics. This technical deep-dive examines the latest developments in vector search technology...',
      source: 'DataScience Today',
      url: 'https://datasciencetoday.com/vector-databases',
      similarity: 0.82,
      timestamp: '2024-01-13T09:20:00Z',
      dataset: 'Technical Papers',
      metadata: {
        author: 'Alex Thompson',
        category: 'Database Technology',
        readTime: '15 min'
      }
    }
  ];

  const handleSearch = async () => {
    if (!query.trim()) return;
    
    setIsSearching(true);
    
    // Simulate API call
    setTimeout(() => {
      setResults(mockResults);
      setIsSearching(false);
    }, 1500);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSearch();
    }
  };

  const getSimilarityColor = (similarity: number) => {
    if (similarity >= 0.9) return 'bg-green-100 text-green-800';
    if (similarity >= 0.8) return 'bg-blue-100 text-blue-800';
    if (similarity >= 0.7) return 'bg-yellow-100 text-yellow-800';
    return 'bg-gray-100 text-gray-800';
  };

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight">Search</h1>
          <p className="text-muted-foreground text-sm sm:text-base">
            Find relevant information across all your datasets using AI-powered semantic search
          </p>
        </div>
      </div>

      {/* Search Interface */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Zap className="h-5 w-5" />
            <span>Semantic Search</span>
          </CardTitle>
          <CardDescription>
            Search across millions of records using natural language queries
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col sm:flex-row gap-4 mb-6">
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-muted-foreground" />
                <Input
                  placeholder="Search for anything..."
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  onKeyPress={handleKeyPress}
                  className="pl-12 h-12 text-base sm:text-lg"
                />
              </div>
            </div>
            <Button 
              onClick={handleSearch} 
              disabled={isSearching || !query.trim()}
              className="h-12 px-6 sm:px-8 w-full sm:w-auto"
            >
              {isSearching ? (
                <div className="flex items-center space-x-2">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white" />
                  <span>Searching...</span>
                </div>
              ) : (
                <div className="flex items-center space-x-2">
                  <Search className="h-4 w-4" />
                  <span>Search</span>
                </div>
              )}
            </Button>
          </div>

          {/* Search Filters */}
          <div className="flex flex-col sm:flex-row sm:items-center gap-4 mb-6">
            <div className="flex gap-2">
              <Button variant="outline" size="sm">
                <Filter className="h-4 w-4 mr-2" />
                Filters
              </Button>
              <Button variant="outline" size="sm">
                <SlidersHorizontal className="h-4 w-4 mr-2" />
                Advanced
              </Button>
            </div>
            <div className="flex flex-wrap gap-2">
              <Badge variant="secondary">All Datasets</Badge>
              <Badge variant="outline">Last 30 days</Badge>
              <Badge variant="outline">Similarity &gt; 80%</Badge>
            </div>
          </div>

          {/* Search Stats */}
          {results.length > 0 && (
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6 p-4 bg-muted/50 rounded-lg">
              <div className="flex flex-col sm:flex-row sm:items-center gap-2 sm:gap-6">
                <div className="text-sm">
                  <span className="font-medium">{results.length}</span> results found
                </div>
                <div className="text-sm text-muted-foreground">
                  Search completed in 0.24 seconds
                </div>
              </div>
              <div className="flex flex-col sm:flex-row gap-2">
                <Button variant="outline" size="sm" className="w-full sm:w-auto">
                  <Download className="h-4 w-4 mr-2" />
                  Export Results
                </Button>
                <Button variant="outline" size="sm" className="w-full sm:w-auto">
                  <BookmarkPlus className="h-4 w-4 mr-2" />
                  Save Search
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Search Results */}
      {results.length > 0 && (
        <div className="space-y-4">
          {results.map((result) => (
            <Card key={result.id} className="hover:shadow-md transition-shadow">
              <CardContent className="p-4 sm:p-6">
                <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-3 mb-3">
                  <div className="flex-1">
                    <h3 className="text-base sm:text-lg font-semibold mb-2 hover:text-primary cursor-pointer">
                      {result.title}
                    </h3>
                    <div className="flex flex-col sm:flex-row sm:items-center gap-2 sm:gap-4 text-sm text-muted-foreground mb-3">
                      <div className="flex items-center space-x-1">
                        <Database className="h-4 w-4" />
                        <span>{result.dataset}</span>
                      </div>
                      <div className="flex items-center space-x-1">
                        <Clock className="h-4 w-4" />
                        <span>{formatTimestamp(result.timestamp)}</span>
                      </div>
                      <span>by {result.metadata.author}</span>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2 self-start">
                    <Badge className={getSimilarityColor(result.similarity)}>
                      {Math.round(result.similarity * 100)}% match
                    </Badge>
                  </div>
                </div>

                <p className="text-muted-foreground mb-4 leading-relaxed">
                  {result.content}
                </p>

                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                  <div className="flex flex-col sm:flex-row sm:items-center gap-2 sm:gap-4">
                    <Badge variant="outline">{result.metadata.category}</Badge>
                    <span className="text-sm text-muted-foreground">
                      {result.metadata.readTime} read
                    </span>
                  </div>
                  
                  <div className="flex items-center space-x-2">
                    <Button variant="ghost" size="sm">
                      <BookmarkPlus className="h-4 w-4" />
                    </Button>
                    <Button variant="outline" size="sm" className="flex-1 sm:flex-none">
                      <ExternalLink className="h-4 w-4 mr-2" />
                      <span className="hidden sm:inline">View Source</span>
                      <span className="sm:hidden">View</span>
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Empty State */}
      {results.length === 0 && !isSearching && (
        <Card>
          <CardContent className="p-12 text-center">
            <Search className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
            <h3 className="text-lg font-semibold mb-2">Start Your Search</h3>
            <p className="text-muted-foreground mb-6 max-w-md mx-auto">
              Use natural language to search across all your datasets. 
              Try queries like "customer feedback analysis" or "financial trends 2024"
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:flex lg:flex-wrap lg:justify-center gap-2">
              <Badge variant="outline" className="cursor-pointer hover:bg-accent text-center">
                machine learning trends
              </Badge>
              <Badge variant="outline" className="cursor-pointer hover:bg-accent text-center">
                data architecture best practices
              </Badge>
              <Badge variant="outline" className="cursor-pointer hover:bg-accent text-center">
                customer sentiment analysis
              </Badge>
              <Badge variant="outline" className="cursor-pointer hover:bg-accent text-center">
                market research insights
              </Badge>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default SearchInterface;
