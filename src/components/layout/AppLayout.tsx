import React, { useState } from 'react';
import { Outlet } from 'react-router-dom';
import { 
  LayoutDashboard, 
  Briefcase, 
  Database, 
  Search, 
  Settings, 
  Users, 
  BarChart3,
  LogOut,
  Bell,
  User,
  Menu,
  X
} from 'lucide-react';
import { 
  Sidebar, 
  SidebarHeader, 
  SidebarContent, 
  SidebarNav, 
  SidebarNavItem, 
  SidebarFooter 
} from '@/components/ui/sidebar';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';

const AppLayout: React.FC = () => {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  return (
    <div className="flex h-screen bg-background">
      {/* Mobile Menu Overlay */}
      {isMobileMenuOpen && (
        <div 
          className="fixed inset-0 z-50 bg-black/50 lg:hidden" 
          onClick={() => setIsMobileMenuOpen(false)}
        />
      )}

      {/* Sidebar */}
      <Sidebar className={`
        fixed lg:static inset-y-0 left-0 z-50 w-64 transform transition-transform duration-300 ease-in-out
        ${isMobileMenuOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
      `}>
        <SidebarHeader>
          <div className="flex items-center gap-2">
            <div className="h-8 w-8 rounded-lg bg-primary flex items-center justify-center">
              <span className="text-primary-foreground font-bold text-sm">WS</span>
            </div>
            <div>
              <h1 className="font-semibold text-lg">WebSets</h1>
              <p className="text-xs text-muted-foreground">Enterprise Platform</p>
            </div>
          </div>
        </SidebarHeader>

        <SidebarContent>
          <SidebarNav>
            <SidebarNavItem 
              href="/dashboard" 
              active={location.pathname === '/dashboard'}
              icon={<LayoutDashboard />}
            >
              Dashboard
            </SidebarNavItem>
            
            <SidebarNavItem 
              href="/jobs" 
              active={location.pathname.startsWith('/jobs')}
              icon={<Briefcase />}
            >
              <div className="flex items-center justify-between w-full">
                <span>Jobs</span>
                <Badge variant="secondary" className="ml-auto">3</Badge>
              </div>
            </SidebarNavItem>
            
            <SidebarNavItem 
              href="/datasets" 
              active={location.pathname.startsWith('/datasets')}
              icon={<Database />}
            >
              Datasets
            </SidebarNavItem>
            
            <SidebarNavItem 
              href="/search" 
              active={location.pathname.startsWith('/search')}
              icon={<Search />}
            >
              Search
            </SidebarNavItem>
            
            <SidebarNavItem 
              href="/analytics" 
              active={location.pathname.startsWith('/analytics')}
              icon={<BarChart3 />}
            >
              Analytics
            </SidebarNavItem>
            
            <div className="my-4 border-t" />
            
            <SidebarNavItem 
              href="/users" 
              active={location.pathname.startsWith('/users')}
              icon={<Users />}
            >
              Users
            </SidebarNavItem>
            
            <SidebarNavItem 
              href="/settings" 
              active={location.pathname.startsWith('/settings')}
              icon={<Settings />}
            >
              Settings
            </SidebarNavItem>
          </SidebarNav>
        </SidebarContent>

        <SidebarFooter>
          <div className="lg:hidden mb-4">
            <Button 
              variant="ghost" 
              size="icon"
              className="absolute top-4 right-4"
              onClick={() => setIsMobileMenuOpen(false)}
            >
              <X className="h-5 w-5" />
            </Button>
          </div>
          <div className="flex items-center gap-3 mb-3">
            <div className="h-8 w-8 rounded-full bg-muted flex items-center justify-center">
              <User className="h-4 w-4" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium truncate">John Doe</p>
              <p className="text-xs text-muted-foreground truncate">john@company.com</p>
            </div>
          </div>
          <Button variant="ghost" size="sm" className="w-full justify-start">
            <LogOut className="h-4 w-4 mr-2" />
            Sign Out
          </Button>
        </SidebarFooter>
      </Sidebar>

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Top Navigation */}
        <header className="h-16 border-b bg-background flex items-center justify-between px-4 lg:px-6">
          <div className="flex items-center gap-4">
            <Button 
              variant="ghost" 
              size="icon"
              className="lg:hidden"
              onClick={() => setIsMobileMenuOpen(true)}
            >
              <Menu className="h-5 w-5" />
            </Button>
            <h2 className="text-xl font-semibold hidden sm:block">Dashboard</h2>
          </div>
          
          <div className="flex items-center gap-2 lg:gap-4">
            <Button variant="ghost" size="icon">
              <Bell className="h-4 w-4" />
            </Button>
            <div className="flex items-center gap-2">
              <div className="h-8 w-8 rounded-full bg-primary flex items-center justify-center">
                <User className="h-4 w-4 text-primary-foreground" />
              </div>
              <span className="text-sm font-medium hidden sm:inline">John Doe</span>
            </div>
          </div>
        </header>

        {/* Page Content */}
        <main className="flex-1 overflow-auto p-4 lg:p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
};

export default AppLayout;
