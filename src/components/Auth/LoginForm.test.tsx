import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import LoginForm from './LoginForm';
import * as useAuthHook from '../../hooks/useAuth';

// Mock the useAuth hook
jest.mock('../../hooks/useAuth');
const mockUseAuth = useAuthHook as jest.Mocked<typeof useAuthHook>;

describe('LoginForm', () => {
  const mockLogin = jest.fn();
  const mockRegister = jest.fn();

  beforeEach(() => {
    mockUseAuth.useAuth.mockReturnValue({
      login: mockLogin,
      register: mockRegister,
      isLoading: false,
      error: null,
      user: null,
      logout: jest.fn(),
    });
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  test('renders login form by default', () => {
    render(<LoginForm />);
    
    expect(screen.getByText('Sign in to Websets')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Email address')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Password')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument();
    expect(screen.getByText("Don't have an account? Sign up")).toBeInTheDocument();
  });

  test('switches to registration mode', async () => {
    const user = userEvent.setup();
    render(<LoginForm />);
    
    await user.click(screen.getByText("Don't have an account? Sign up"));
    
    expect(screen.getByText('Create your account')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Full name')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /create account/i })).toBeInTheDocument();
    expect(screen.getByText('Already have an account? Sign in')).toBeInTheDocument();
  });

  test('submits login form with correct data', async () => {
    const user = userEvent.setup();
    render(<LoginForm />);
    
    await user.type(screen.getByPlaceholderText('Email address'), 'test@example.com');
    await user.type(screen.getByPlaceholderText('Password'), 'password123');
    await user.click(screen.getByRole('button', { name: /sign in/i }));
    
    await waitFor(() => {
      expect(mockLogin).toHaveBeenCalledWith('test@example.com', 'password123');
    });
  });

  test('submits registration form with correct data', async () => {
    const user = userEvent.setup();
    render(<LoginForm />);
    
    // Switch to registration mode
    await user.click(screen.getByText("Don't have an account? Sign up"));
    
    // Fill out the form
    await user.type(screen.getByPlaceholderText('Full name'), 'Test User');
    await user.type(screen.getByPlaceholderText('Email address'), 'test@example.com');
    await user.type(screen.getByPlaceholderText('Password'), 'password123');
    await user.click(screen.getByRole('button', { name: /create account/i }));
    
    await waitFor(() => {
      expect(mockRegister).toHaveBeenCalledWith('test@example.com', 'password123', 'Test User');
    });
  });

  test('displays error message when provided', () => {
    mockUseAuth.useAuth.mockReturnValue({
      login: mockLogin,
      register: mockRegister,
      isLoading: false,
      error: 'Invalid credentials',
      user: null,
      logout: jest.fn(),
    });
    
    render(<LoginForm />);
    
    expect(screen.getByText('Error')).toBeInTheDocument();
    expect(screen.getByText('Invalid credentials')).toBeInTheDocument();
  });

  test('shows loading state during submission', () => {
    mockUseAuth.useAuth.mockReturnValue({
      login: mockLogin,
      register: mockRegister,
      isLoading: true,
      error: null,
      user: null,
      logout: jest.fn(),
    });
    
    render(<LoginForm />);
    
    expect(screen.getByText('Signing in...')).toBeInTheDocument();
    expect(screen.getByRole('button')).toBeDisabled();
  });

  test('shows registration loading state', () => {
    mockUseAuth.useAuth.mockReturnValue({
      login: mockLogin,
      register: mockRegister,
      isLoading: true,
      error: null,
      user: null,
      logout: jest.fn(),
    });
    
    render(<LoginForm />);
    
    // Switch to registration mode first
    fireEvent.click(screen.getByText("Don't have an account? Sign up"));
    
    expect(screen.getByText('Creating account...')).toBeInTheDocument();
    expect(screen.getByRole('button')).toBeDisabled();
  });

  test('form validation works correctly', async () => {
    const user = userEvent.setup();
    render(<LoginForm />);
    
    // Try to submit empty form
    await user.click(screen.getByRole('button', { name: /sign in/i }));
    
    // HTML5 validation should prevent submission
    expect(mockLogin).not.toHaveBeenCalled();
  });

  test('switches back from registration to login', async () => {
    const user = userEvent.setup();
    render(<LoginForm />);
    
    // Switch to registration
    await user.click(screen.getByText("Don't have an account? Sign up"));
    expect(screen.getByText('Create your account')).toBeInTheDocument();
    
    // Switch back to login
    await user.click(screen.getByText('Already have an account? Sign in'));
    expect(screen.getByText('Sign in to Websets')).toBeInTheDocument();
    expect(screen.queryByPlaceholderText('Full name')).not.toBeInTheDocument();
  });
});