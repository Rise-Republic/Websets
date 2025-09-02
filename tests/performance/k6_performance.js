/**
 * K6 Performance Tests with SLA Thresholds
 * Comprehensive load testing for WebSet Miner API
 */

import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend, Counter } from 'k6/metrics';

// Custom metrics
const errorRate = new Rate('errors');
const apiLatency = new Trend('api_latency');
const requestCount = new Counter('requests_total');

// Test configuration
export const options = {
  stages: [
    { duration: '2m', target: 10 }, // Ramp up
    { duration: '5m', target: 50 }, // Stay at 50 users
    { duration: '2m', target: 100 }, // Ramp to 100 users
    { duration: '5m', target: 100 }, // Stay at 100 users
    { duration: '2m', target: 0 }, // Ramp down
  ],
  thresholds: {
    // SLA Requirements
    http_req_duration: ['p(95)<500', 'p(99)<1000'], // 95% < 500ms, 99% < 1s
    http_req_failed: ['rate<0.01'], // Error rate < 1%
    errors: ['rate<0.01'],
    api_latency: ['p(95)<500'],
    requests_total: ['count>1000'], // Minimum request volume
    
    // Specific endpoint thresholds
    'http_req_duration{endpoint:health}': ['p(95)<100'],
    'http_req_duration{endpoint:search}': ['p(95)<800'],
    'http_req_duration{endpoint:datasets}': ['p(95)<600'],
    'http_req_duration{endpoint:analytics}': ['p(95)<1000'],
  },
  ext: {
    loadimpact: {
      projectID: 3596970,
      name: 'WebSet Miner Performance Test'
    }
  }
};

// Test data
const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';
const AUTH_TOKEN = __ENV.AUTH_TOKEN || 'test-token';

const testDatasets = [
  { name: 'E-commerce Sites', urls: ['https://example-shop.com'] },
  { name: 'News Articles', urls: ['https://news-site.com'] },
  { name: 'Tech Blogs', urls: ['https://tech-blog.com'] }
];

const searchQueries = [
  'web scraping tools',
  'data extraction methods',
  'automation frameworks',
  'machine learning datasets',
  'api integration patterns'
];

export function setup() {
  // Setup phase - create test data
  console.log('Setting up performance test data...');
  
  const headers = {
    'Authorization': `Bearer ${AUTH_TOKEN}`,
    'Content-Type': 'application/json'
  };

  // Create test datasets
  testDatasets.forEach(dataset => {
    const response = http.post(`${BASE_URL}/v1/datasets`, JSON.stringify(dataset), {
      headers,
      tags: { endpoint: 'setup' }
    });
    check(response, {
      'setup dataset created': (r) => r.status === 201 || r.status === 409
    });
  });

  return { authToken: AUTH_TOKEN };
}

export default function(data) {
  const headers = {
    'Authorization': `Bearer ${data.authToken}`,
    'Content-Type': 'application/json'
  };

  // Test scenario weights
  const scenario = Math.random();
  
  if (scenario < 0.3) {
    // 30% - Health checks and light operations
    testHealthEndpoints(headers);
  } else if (scenario < 0.6) {
    // 30% - Search operations
    testSearchOperations(headers);
  } else if (scenario < 0.85) {
    // 25% - Dataset operations
    testDatasetOperations(headers);
  } else {
    // 15% - Analytics and heavy operations
    testAnalyticsOperations(headers);
  }

  sleep(1); // Think time between requests
}

function testHealthEndpoints(headers) {
  // Health check
  const healthResponse = http.get(`${BASE_URL}/health`, {
    tags: { endpoint: 'health' }
  });
  
  const healthCheck = check(healthResponse, {
    'health status is 200': (r) => r.status === 200,
    'health response time < 100ms': (r) => r.timings.duration < 100,
    'health has status field': (r) => r.json('status') !== undefined
  });

  errorRate.add(!healthCheck);
  apiLatency.add(healthResponse.timings.duration);
  requestCount.add(1);

  // API info
  const infoResponse = http.get(`${BASE_URL}/`, {
    tags: { endpoint: 'info' }
  });
  
  check(infoResponse, {
    'info status is 200': (r) => r.status === 200,
    'info response time < 200ms': (r) => r.timings.duration < 200
  });
}

function testSearchOperations(headers) {
  const query = searchQueries[Math.floor(Math.random() * searchQueries.length)];
  
  const searchPayload = {
    query: query,
    limit: 20,
    filters: {
      status: 'active'
    }
  };

  const searchResponse = http.post(
    `${BASE_URL}/v1/search`,
    JSON.stringify(searchPayload),
    { headers, tags: { endpoint: 'search' } }
  );

  const searchCheck = check(searchResponse, {
    'search status is 200': (r) => r.status === 200,
    'search response time < 800ms': (r) => r.timings.duration < 800,
    'search has results': (r) => {
      const body = r.json();
      return body && Array.isArray(body.results);
    },
    'search results have required fields': (r) => {
      const body = r.json();
      if (body && body.results && body.results.length > 0) {
        const result = body.results[0];
        return result.id !== undefined && result.title !== undefined;
      }
      return true; // Empty results are valid
    }
  });

  errorRate.add(!searchCheck);
  apiLatency.add(searchResponse.timings.duration);
  requestCount.add(1);
}

function testDatasetOperations(headers) {
  // List datasets
  const listResponse = http.get(`${BASE_URL}/v1/datasets`, {
    headers,
    tags: { endpoint: 'datasets' }
  });

  const listCheck = check(listResponse, {
    'datasets list status is 200': (r) => r.status === 200,
    'datasets response time < 600ms': (r) => r.timings.duration < 600,
    'datasets has pagination': (r) => {
      const body = r.json();
      return body && typeof body.total === 'number';
    }
  });

  errorRate.add(!listCheck);
  apiLatency.add(listResponse.timings.duration);
  requestCount.add(1);

  // Get specific dataset (if any exist)
  const datasets = listResponse.json();
  if (datasets && datasets.datasets && datasets.datasets.length > 0) {
    const datasetId = datasets.datasets[0].id;
    
    const detailResponse = http.get(`${BASE_URL}/v1/datasets/${datasetId}`, {
      headers,
      tags: { endpoint: 'dataset_detail' }
    });

    check(detailResponse, {
      'dataset detail status is 200': (r) => r.status === 200,
      'dataset detail response time < 400ms': (r) => r.timings.duration < 400
    });

    requestCount.add(1);
  }
}

function testAnalyticsOperations(headers) {
  const analyticsResponse = http.get(`${BASE_URL}/v1/analytics`, {
    headers,
    tags: { endpoint: 'analytics' }
  });

  const analyticsCheck = check(analyticsResponse, {
    'analytics status is 200': (r) => r.status === 200,
    'analytics response time < 1000ms': (r) => r.timings.duration < 1000,
    'analytics has metrics': (r) => {
      const body = r.json();
      return body && body.metrics !== undefined;
    }
  });

  errorRate.add(!analyticsCheck);
  apiLatency.add(analyticsResponse.timings.duration);
  requestCount.add(1);

  // System metrics
  const metricsResponse = http.get(`${BASE_URL}/metrics`, {
    headers,
    tags: { endpoint: 'system_metrics' }
  });

  check(metricsResponse, {
    'system metrics accessible': (r) => r.status === 200 || r.status === 404,
    'metrics response time < 500ms': (r) => r.timings.duration < 500
  });

  requestCount.add(1);
}

export function teardown(data) {
  console.log('Performance test completed');
  console.log(`Total requests: ${requestCount.count}`);
  console.log(`Error rate: ${(errorRate.rate * 100).toFixed(2)}%`);
  console.log(`Average latency: ${apiLatency.avg.toFixed(2)}ms`);
  console.log(`95th percentile latency: ${apiLatency.p(95).toFixed(2)}ms`);
}

// Smoke test configuration for quick validation
export const smokeTest = {
  executor: 'constant-vus',
  vus: 1,
  duration: '1m',
  thresholds: {
    http_req_duration: ['p(95)<1000'],
    http_req_failed: ['rate<0.05'],
  }
};

// Stress test configuration for capacity planning
export const stressTest = {
  stages: [
    { duration: '5m', target: 100 },
    { duration: '10m', target: 200 },
    { duration: '5m', target: 300 },
    { duration: '10m', target: 400 },
    { duration: '5m', target: 0 },
  ],
  thresholds: {
    http_req_duration: ['p(95)<2000'],
    http_req_failed: ['rate<0.05'],
  }
};
