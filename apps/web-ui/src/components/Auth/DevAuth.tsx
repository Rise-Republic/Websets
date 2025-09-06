import React, { useState } from 'react';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';

interface DevAuthProps {
  onLogin: (user: { id: string; email: string; full_name: string }) => void;
}

export const DevAuth: React.FC<DevAuthProps> = ({ onLogin }) => {
  const [email, setEmail] = useState('dev@websets.com');
  const [name, setName] = useState('Development User');

  const handleDevLogin = () => {
    const devUser = {
      id: 'dev-user-1',
      email,
      full_name: name,
    };
    onLogin(devUser);
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>Development Authentication</CardTitle>
          <CardDescription>
            WorkOS is not configured. Use development login for testing.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1">
              Email
            </label>
            <Input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="Enter email"
            />
          </div>
          <div>
            <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-1">
              Full Name
            </label>
            <Input
              id="name"
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Enter full name"
            />
          </div>
          <Button onClick={handleDevLogin} className="w-full">
            Login (Development)
          </Button>
        </CardContent>
      </Card>
    </div>
  );
};
