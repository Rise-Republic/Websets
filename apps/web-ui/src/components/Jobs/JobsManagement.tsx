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
  Play, 
  Pause, 
  Square, 
  Eye, 
  MoreHorizontal,
  Plus,
  Search,
  Filter,
  Download,
  RefreshCw
} from 'lucide-react';

interface Job {
  id: string;
  name: string;
  status: 'running' | 'completed' | 'pending' | 'error' | 'paused';
  progress: number;
  startTime: string;
  endTime?: string;
  recordsExtracted: number;
  totalUrls: number;
  crawledUrls: number;
  prompt: string;
}

const JobsManagement: React.FC = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');

  const jobs: Job[] = [
    {
      id: 'job-001',
      name: 'E-commerce Product Scraping',
      status: 'running',
      progress: 75,
      startTime: '2024-01-15 14:30:00',
      recordsExtracted: 12450,
      totalUrls: 500,
      crawledUrls: 375,
      prompt: 'Extract product information from major e-commerce websites including prices, descriptions, and reviews'
    },
    {
      id: 'job-002',
      name: 'News Articles Collection',
      status: 'completed',
      progress: 100,
      startTime: '2024-01-15 09:15:00',
      endTime: '2024-01-15 11:45:00',
      recordsExtracted: 8932,
      totalUrls: 200,
      crawledUrls: 200,
      prompt: 'Collect latest news articles from technology news websites'
    },
    {
      id: 'job-003',
      name: 'Social Media Analytics',
      status: 'pending',
      progress: 0,
      startTime: '2024-01-15 18:00:00',
      recordsExtracted: 0,
      totalUrls: 1000,
      crawledUrls: 0,
      prompt: 'Analyze social media posts for sentiment and engagement metrics'
    },
    {
      id: 'job-004',
      name: 'Financial Data Mining',
      status: 'error',
      progress: 45,
      startTime: '2024-01-14 16:20:00',
      recordsExtracted: 3421,
      totalUrls: 300,
      crawledUrls: 135,
      prompt: 'Extract financial data and market indicators from financial websites'
    },
    {
      id: 'job-005',
      name: 'Real Estate Listings',
      status: 'paused',
      progress: 60,
      startTime: '2024-01-15 12:00:00',
      recordsExtracted: 7890,
      totalUrls: 800,
      crawledUrls: 480,
      prompt: 'Collect real estate property listings with prices and details'
    }
  ];

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'running': return 'bg-blue-100 text-blue-800';
      case 'completed': return 'bg-green-100 text-green-800';
      case 'pending': return 'bg-yellow-100 text-yellow-800';
      case 'error': return 'bg-red-100 text-red-800';
      case 'paused': return 'bg-gray-100 text-gray-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getActionButton = (job: Job) => {
    switch (job.status) {
      case 'running':
        return (
          <Button variant="outline" size="sm">
            <Pause className="h-4 w-4" />
          </Button>
        );
      case 'paused':
        return (
          <Button variant="outline" size="sm">
            <Play className="h-4 w-4" />
          </Button>
        );
      case 'pending':
        return (
          <Button variant="outline" size="sm">
            <Play className="h-4 w-4" />
          </Button>
        );
      case 'error':
        return (
          <Button variant="outline" size="sm">
            <RefreshCw className="h-4 w-4" />
          </Button>
        );
      default:
        return (
          <Button variant="outline" size="sm">
            <Eye className="h-4 w-4" />
          </Button>
        );
    }
  };

  const filteredJobs = jobs.filter(job => {
    const matchesSearch = job.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         job.prompt.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = statusFilter === 'all' || job.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Jobs</h1>
          <p className="text-muted-foreground">
            Manage and monitor your data extraction jobs
          </p>
        </div>
        <Button>
          <Plus className="h-4 w-4 mr-2" />
          Create New Job
        </Button>
      </div>

      {/* Stats Cards */}
      <div className="grid gap-4 grid-cols-1 sm:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Jobs</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{jobs.length}</div>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Running</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-blue-600">
              {jobs.filter(j => j.status === 'running').length}
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Completed</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">
              {jobs.filter(j => j.status === 'completed').length}
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Records</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {jobs.reduce((sum, job) => sum + job.recordsExtracted, 0).toLocaleString()}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filters and Search */}
      <Card>
        <CardHeader>
          <CardTitle>Job Management</CardTitle>
          <CardDescription>
            View, monitor, and control your data extraction jobs
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col sm:flex-row items-start sm:items-center space-y-4 sm:space-y-0 sm:space-x-4 mb-6">
            <div className="flex-1 w-full sm:w-auto">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search jobs..."
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
              <option value="running">Running</option>
              <option value="completed">Completed</option>
              <option value="pending">Pending</option>
              <option value="paused">Paused</option>
              <option value="error">Error</option>
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

          {/* Jobs Table */}
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Job Name</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Progress</TableHead>
                <TableHead>Records</TableHead>
                <TableHead>URLs</TableHead>
                <TableHead>Started</TableHead>
                <TableHead>Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredJobs.map((job) => (
                <TableRow key={job.id}>
                  <TableCell>
                    <div>
                      <div className="font-medium">{job.name}</div>
                      <div className="text-sm text-muted-foreground truncate max-w-xs">
                        {job.prompt}
                      </div>
                    </div>
                  </TableCell>
                  
                  <TableCell>
                    <Badge className={getStatusColor(job.status)}>
                      {job.status.charAt(0).toUpperCase() + job.status.slice(1)}
                    </Badge>
                  </TableCell>
                  
                  <TableCell>
                    <div className="w-full">
                      <div className="flex items-center justify-between text-sm mb-1">
                        <span>{job.progress}%</span>
                      </div>
                      <div className="w-full bg-secondary rounded-full h-2">
                        <div 
                          className="bg-primary h-2 rounded-full transition-all duration-300" 
                          style={{ width: `${job.progress}%` }}
                        />
                      </div>
                    </div>
                  </TableCell>
                  
                  <TableCell>
                    <div className="text-sm">
                      <div className="font-medium">{job.recordsExtracted.toLocaleString()}</div>
                    </div>
                  </TableCell>
                  
                  <TableCell>
                    <div className="text-sm">
                      <div>{job.crawledUrls}/{job.totalUrls}</div>
                      <div className="text-muted-foreground">
                        {Math.round((job.crawledUrls / job.totalUrls) * 100)}% crawled
                      </div>
                    </div>
                  </TableCell>
                  
                  <TableCell>
                    <div className="text-sm">
                      {new Date(job.startTime).toLocaleDateString()}
                      <div className="text-muted-foreground">
                        {new Date(job.startTime).toLocaleTimeString()}
                      </div>
                    </div>
                  </TableCell>
                  
                  <TableCell>
                    <div className="flex items-center space-x-2">
                      {getActionButton(job)}
                      <Button variant="ghost" size="sm">
                        <Eye className="h-4 w-4" />
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
    </div>
  );
};

export default JobsManagement;
