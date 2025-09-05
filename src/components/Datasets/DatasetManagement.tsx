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
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { 
  Database, 
  Search, 
  Filter,
  Download,
  Eye,
  MoreHorizontal,
  Plus,
  BarChart3,
  Calendar,
  FileText,
  Layers
} from 'lucide-react';

interface Dataset {
  id: string;
  name: string;
  description: string;
  recordCount: number;
  sourceCount: number;
  size: string;
  createdAt: string;
  updatedAt: string;
  status: 'active' | 'processing' | 'archived';
  jobId: string;
  schema: Record<string, string>;
}

const DatasetManagement: React.FC = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');

  const datasets: Dataset[] = [
    {
      id: 'ds-001',
      name: 'E-commerce Product Catalog',
      description: 'Comprehensive product information from major e-commerce platforms including prices, descriptions, reviews, and specifications',
      recordCount: 125430,
      sourceCount: 15,
      size: '2.4 GB',
      createdAt: '2024-01-15T14:30:00Z',
      updatedAt: '2024-01-15T16:45:00Z',
      status: 'active',
      jobId: 'job-001',
      schema: {
        'product_name': 'string',
        'price': 'number',
        'description': 'text',
        'rating': 'number',
        'reviews_count': 'number',
        'category': 'string',
        'brand': 'string',
        'availability': 'boolean'
      }
    },
    {
      id: 'ds-002',
      name: 'Technology News Articles',
      description: 'Latest technology news and articles from leading tech publications and blogs',
      recordCount: 89320,
      sourceCount: 8,
      size: '1.8 GB',
      createdAt: '2024-01-15T09:15:00Z',
      updatedAt: '2024-01-15T11:45:00Z',
      status: 'active',
      jobId: 'job-002',
      schema: {
        'title': 'string',
        'content': 'text',
        'author': 'string',
        'published_date': 'datetime',
        'category': 'string',
        'tags': 'array',
        'read_time': 'number'
      }
    },
    {
      id: 'ds-003',
      name: 'Social Media Sentiment Data',
      description: 'Social media posts and comments with sentiment analysis and engagement metrics',
      recordCount: 0,
      sourceCount: 0,
      size: '0 MB',
      createdAt: '2024-01-15T18:00:00Z',
      updatedAt: '2024-01-15T18:00:00Z',
      status: 'processing',
      jobId: 'job-003',
      schema: {
        'post_text': 'text',
        'sentiment_score': 'number',
        'engagement_rate': 'number',
        'platform': 'string',
        'timestamp': 'datetime',
        'user_followers': 'number'
      }
    },
    {
      id: 'ds-004',
      name: 'Financial Market Data',
      description: 'Historical and real-time financial market data including stocks, bonds, and commodities',
      recordCount: 342100,
      sourceCount: 5,
      size: '890 MB',
      createdAt: '2024-01-10T08:00:00Z',
      updatedAt: '2024-01-14T16:20:00Z',
      status: 'archived',
      jobId: 'job-004',
      schema: {
        'symbol': 'string',
        'price': 'number',
        'volume': 'number',
        'market_cap': 'number',
        'timestamp': 'datetime',
        'exchange': 'string'
      }
    }
  ];

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'bg-green-100 text-green-800';
      case 'processing': return 'bg-blue-100 text-blue-800';
      case 'archived': return 'bg-gray-100 text-gray-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  const filteredDatasets = datasets.filter(dataset => {
    const matchesSearch = dataset.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         dataset.description.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = statusFilter === 'all' || dataset.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  const totalRecords = datasets.reduce((sum, ds) => sum + ds.recordCount, 0);
  const totalSize = datasets.reduce((sum, ds) => {
    const sizeValue = parseFloat(ds.size.split(' ')[0]);
    const unit = ds.size.split(' ')[1];
    return sum + (unit === 'GB' ? sizeValue * 1024 : sizeValue);
  }, 0);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Datasets</h1>
          <p className="text-muted-foreground">
            Manage and explore your extracted data collections
          </p>
        </div>
        <Button>
          <Plus className="h-4 w-4 mr-2" />
          Create Dataset
        </Button>
      </div>

      {/* Stats Cards */}
      <div className="grid gap-4 grid-cols-1 sm:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Datasets</CardTitle>
            <Database className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{datasets.length}</div>
            <p className="text-xs text-muted-foreground">
              {datasets.filter(d => d.status === 'active').length} active
            </p>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Records</CardTitle>
            <FileText className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{totalRecords.toLocaleString()}</div>
            <p className="text-xs text-muted-foreground">
              Across all datasets
            </p>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Storage Used</CardTitle>
            <Layers className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{(totalSize / 1024).toFixed(1)} GB</div>
            <p className="text-xs text-muted-foreground">
              Total data size
            </p>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Data Sources</CardTitle>
            <BarChart3 className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {datasets.reduce((sum, ds) => sum + ds.sourceCount, 0)}
            </div>
            <p className="text-xs text-muted-foreground">
              Unique sources
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Dataset Management */}
      <Card>
        <CardHeader>
          <CardTitle>Dataset Collection</CardTitle>
          <CardDescription>
            Browse, analyze, and manage your data extraction results
          </CardDescription>
        </CardHeader>
        <CardContent>
          {/* Filters and Search */}
          <div className="flex flex-col sm:flex-row items-start sm:items-center space-y-4 sm:space-y-0 sm:space-x-4 mb-6">
            <div className="flex-1 w-full sm:w-auto">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search datasets..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>
            
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="px-3 py-2 border border-input bg-background rounded-md text-sm"
            >
              <option value="all">All Status</option>
              <option value="active">Active</option>
              <option value="processing">Processing</option>
              <option value="archived">Archived</option>
            </select>
            
            <div className="flex space-x-2 w-full sm:w-auto">
              <Button variant="outline" className="flex-1 sm:flex-none">
                <Filter className="h-4 w-4 mr-2" />
                Filters
              </Button>
              
              <Button variant="outline" className="flex-1 sm:flex-none">
                <Download className="h-4 w-4 mr-2" />
                Export
              </Button>
            </div>
          </div>

          {/* Datasets Table */}
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Dataset Name</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Records</TableHead>
                <TableHead>Sources</TableHead>
                <TableHead>Size</TableHead>
                <TableHead>Created</TableHead>
                <TableHead>Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredDatasets.map((dataset) => (
                <TableRow key={dataset.id}>
                  <TableCell>
                    <div>
                      <div className="font-medium">{dataset.name}</div>
                      <div className="text-sm text-muted-foreground truncate max-w-xs">
                        {dataset.description}
                      </div>
                    </div>
                  </TableCell>
                  
                  <TableCell>
                    <Badge className={getStatusColor(dataset.status)}>
                      {dataset.status.charAt(0).toUpperCase() + dataset.status.slice(1)}
                    </Badge>
                  </TableCell>
                  
                  <TableCell>
                    <div className="text-sm">
                      <div className="font-medium">{dataset.recordCount.toLocaleString()}</div>
                      <div className="text-muted-foreground">records</div>
                    </div>
                  </TableCell>
                  
                  <TableCell>
                    <div className="text-sm">
                      <div className="font-medium">{dataset.sourceCount}</div>
                      <div className="text-muted-foreground">sources</div>
                    </div>
                  </TableCell>
                  
                  <TableCell>
                    <div className="text-sm font-medium">{dataset.size}</div>
                  </TableCell>
                  
                  <TableCell>
                    <div className="text-sm">
                      <div>{formatDate(dataset.createdAt)}</div>
                      <div className="text-muted-foreground flex items-center">
                        <Calendar className="h-3 w-3 mr-1" />
                        Updated {formatDate(dataset.updatedAt)}
                      </div>
                    </div>
                  </TableCell>
                  
                  <TableCell>
                    <div className="flex items-center space-x-2">
                      <Button variant="ghost" size="sm">
                        <Eye className="h-4 w-4" />
                      </Button>
                      <Button variant="ghost" size="sm">
                        <Download className="h-4 w-4" />
                      </Button>
                      <Button variant="ghost" size="sm">
                        <MoreHorizontal className="h-4 w-4" />
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Schema Preview */}
      <Card>
        <CardHeader>
          <CardTitle>Dataset Schemas</CardTitle>
          <CardDescription>
            Data structure and field definitions for your datasets
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 grid-cols-1 lg:grid-cols-2">
            {filteredDatasets.slice(0, 2).map((dataset) => (
              <Card key={dataset.id} className="border-2">
                <CardHeader className="pb-3">
                  <CardTitle className="text-lg">{dataset.name}</CardTitle>
                  <Badge className={getStatusColor(dataset.status)} variant="outline">
                    {dataset.recordCount.toLocaleString()} records
                  </Badge>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    {Object.entries(dataset.schema).map(([field, type]) => (
                      <div key={field} className="flex items-center justify-between py-1">
                        <span className="text-sm font-mono">{field}</span>
                        <Badge variant="secondary" className="text-xs">
                          {type}
                        </Badge>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default DatasetManagement;
