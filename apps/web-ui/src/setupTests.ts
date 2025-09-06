import '@testing-library/jest-dom';

// Mock fetch globally
global.fetch = jest.fn();

// Mock sessionStorage
const sessionStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
};
global.sessionStorage = sessionStorageMock as any;

// Reset all mocks before each test
beforeEach(() => {
  jest.clearAllMocks();
});
