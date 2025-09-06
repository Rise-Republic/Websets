import React from 'react';
import { 
  Card, 
  CardContent, 
  CardDescription, 
  CardHeader, 
  CardTitle 
} from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { 
  BarChart3, 
  TrendingUp, 
  Database, 
  Activity,
  Users,
  Clock,
  CheckCircle,
  AlertCircle,
  Plus
} from 'lucide-react';

const EnterpriseOverview: React.FC = () => {
  const stats = [
    {
      title: "Active Jobs",
      value: "12",
      change: "+2.5%",
      trend: "up",
      icon: <Activity className="h-4 w-4" />
    },
    {
      title: "Total Datasets",
      value: "847",
      change: "+12.3%",
      trend: "up",
      icon: <Database className="h-4 w-4" />
    },
    {
      title: "Data Records",
      value: "2.4M",
      change: "+8.1%",
      trend: "up",
      icon: <BarChart3 className="h-4 w-4" />
    },
    {
      title: "Active Users",
      value: "156",
      change: "+4.2%",
      trend: "up",
      icon: <Users className="h-4 w-4" />
    }
  ];

  const recentJobs = [
    {
      id: "job-001",
      name: "E-commerce Product Scraping",
      status: "running",
      progress: 75,
      startTime: "2 hours ago",
      recordsExtracted: 12450
    },
    {
      id: "job-002", 
      name: "News Articles Collection",
      status: "completed",
      progress: 100,
      startTime: "5 hours ago",
      recordsExtracted: 8932
    },
    {
      id: "job-003",
      name: "Social Media Analytics",
      status: "pending",
      progress: 0,
      startTime: "Scheduled for 6 PM",
      recordsExtracted: 0
    },
    {
      id: "job-004",
      name: "Financial Data Mining",
      status: "error",
      progress: 45,
      startTime: "1 day ago",
      recordsExtracted: 3421
    }
  ];

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'running': return 'bg-blue-500';
      case 'completed': return 'bg-green-500';
      case 'pending': return 'bg-yellow-500';
      case 'error': return 'bg-red-500';
      default: return 'bg-gray-500';
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'running': return <Badge className="bg-blue-100 text-blue-800">Running</Badge>;
      case 'completed': return <Badge className="bg-green-100 text-green-800">Completed</Badge>;
      case 'pending': return <Badge className="bg-yellow-100 text-yellow-800">Pending</Badge>;
      case 'error': return <Badge variant="destructive">Error</Badge>;
      default: return <Badge variant="secondary">Unknown</Badge>;
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
          <p className="text-muted-foreground">
            Welcome back! Here's what's happening with your data extraction platform.
          </p>
        </div>
        <Button>
          <Plus className="h-4 w-4 mr-2" />
          New Job
        </Button>
      </div>

      {/* Stats Grid */}
      <div className="grid gap-4 grid-cols-1 sm:grid-cols-2 lg:grid-cols-4">
        {stats.map((stat, index) => (
          <Card key={index}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">
                {stat.title}
              </CardTitle>
              {stat.icon}
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stat.value}</div>
              <p className="text-xs text-muted-foreground flex items-center">
                <TrendingUp className="h-3 w-3 mr-1 text-green-500" />
                {stat.change} from last month
              </p>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        {/* Recent Jobs */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Recent Jobs</CardTitle>
            <CardDescription>
              Your latest data extraction jobs and their status
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {recentJobs.map((job) => (
                <div key={job.id} className="flex items-center space-x-4">
                  <div className={`h-2 w-2 rounded-full ${getStatusColor(job.status)}`} />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium truncate">{job.name}</p>
                    <div className="flex items-center space-x-2 text-xs text-muted-foreground">
                      <Clock className="h-3 w-3" />
                      <span>{job.startTime}</span>
                      <span>•</span>
                      <span>{job.recordsExtracted.toLocaleString()} records</span>
                    </div>
                    {job.status === 'running' && (
                      <div className="mt-1">
                        <div className="w-full bg-secondary rounded-full h-1">
                          <div 
                            className="bg-primary h-1 rounded-full transition-all duration-300" 
                            style={{ width: `${job.progress}%` }}
                          />
                        </div>
                      </div>
                    )}
                  </div>
                  <div className="flex items-center space-x-2">
                    {getStatusBadge(job.status)}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* System Health */}
        <Card>
          <CardHeader>
            <CardTitle>System Health</CardTitle>
            <CardDescription>
              Current status of all platform services
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <CheckCircle className="h-4 w-4 text-green-500" />
                  <span className="text-sm">API Gateway</span>
                </div>
                <Badge className="bg-green-100 text-green-800">Healthy</Badge>
              </div>
              
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <CheckCircle className="h-4 w-4 text-green-500" />
                  <span className="text-sm">Database</span>
                </div>
                <Badge className="bg-green-100 text-green-800">Healthy</Badge>
              </div>
              
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <CheckCircle className="h-4 w-4 text-green-500" />
                  <span className="text-sm">Vector Search</span>
                </div>
                <Badge className="bg-green-100 text-green-800">Healthy</Badge>
              </div>
              
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <AlertCircle className="h-4 w-4 text-yellow-500" />
                  <span className="text-sm">Background Workers</span>
                </div>
                <Badge className="bg-yellow-100 text-yellow-800">Degraded</Badge>
              </div>
              
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <CheckCircle className="h-4 w-4 text-green-500" />
                  <span className="text-sm">Object Storage</span>
                </div>
                <Badge className="bg-green-100 text-green-800">Healthy</Badge>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Quick Actions */}
      <Card>
        <CardHeader>
          <CardTitle>Quick Actions</CardTitle>
          <CardDescription>
            Common tasks and shortcuts for your workflow
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-3">
            <Button variant="outline" className="h-20 flex-col">
              <Plus className="h-6 w-6 mb-2" />
              Create New Job
            </Button>
            <Button variant="outline" className="h-20 flex-col">
              <Database className="h-6 w-6 mb-2" />
              Browse Datasets
            </Button>
            <Button variant="outline" className="h-20 flex-col">
              <BarChart3 className="h-6 w-6 mb-2" />
              View Analytics
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default EnterpriseOverview;
