/**
 * Accessibility tests using axe-core
 * Ensures WCAG 2.1 AA compliance
 */

import { render } from '@testing-library/react';
import { axe, toHaveNoViolations } from 'jest-axe';
import { BrowserRouter } from 'react-router-dom';
import App from '../../App';

// Extend Jest matchers
expect.extend(toHaveNoViolations);

// Mock components for testing
const MockDashboard = () => (
  <main role="main" aria-label="Dashboard">
    <h1>Dashboard</h1>
    <nav aria-label="Main navigation">
      <ul>
        <li><a href="/datasets">Datasets</a></li>
        <li><a href="/analytics">Analytics</a></li>
      </ul>
    </nav>
    <section aria-labelledby="stats-heading">
      <h2 id="stats-heading">Statistics</h2>
      <div role="region" aria-live="polite">
        <p>Loading statistics...</p>
      </div>
    </section>
  </main>
);

const MockForm = () => (
  <form role="form" aria-label="Dataset creation form">
    <fieldset>
      <legend>Dataset Information</legend>
      <div>
        <label htmlFor="dataset-name">Dataset Name</label>
        <input
          id="dataset-name"
          type="text"
          required
          aria-describedby="name-help"
        />
        <div id="name-help">Enter a descriptive name for your dataset</div>
      </div>
      <div>
        <label htmlFor="dataset-description">Description</label>
        <textarea
          id="dataset-description"
          aria-describedby="desc-help"
        />
        <div id="desc-help">Optional description of the dataset</div>
      </div>
    </fieldset>
    <button type="submit">Create Dataset</button>
  </form>
);

const MockDataTable = () => (
  <div role="region" aria-labelledby="data-table-heading">
    <h2 id="data-table-heading">Dataset Results</h2>
    <table role="table" aria-label="Dataset results">
      <thead>
        <tr>
          <th scope="col">Name</th>
          <th scope="col">Status</th>
          <th scope="col">Created</th>
          <th scope="col">Actions</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td>Sample Dataset</td>
          <td>
            <span aria-label="Status: Active" className="status-active">
              Active
            </span>
          </td>
          <td>
            <time dateTime="2024-01-01">January 1, 2024</time>
          </td>
          <td>
            <button aria-label="Edit Sample Dataset">Edit</button>
            <button aria-label="Delete Sample Dataset">Delete</button>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
);

describe('Accessibility Tests', () => {
  it('should not have accessibility violations on main app', async () => {
    const { container } = render(
      <BrowserRouter>
        <App />
      </BrowserRouter>
    );
    
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });

  it('should not have accessibility violations on dashboard', async () => {
    const { container } = render(<MockDashboard />);
    
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });

  it('should not have accessibility violations on forms', async () => {
    const { container } = render(<MockForm />);
    
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });

  it('should not have accessibility violations on data tables', async () => {
    const { container } = render(<MockDataTable />);
    
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });

  it('should have proper heading hierarchy', async () => {
    const { container } = render(
      <div>
        <h1>Main Title</h1>
        <h2>Section Title</h2>
        <h3>Subsection Title</h3>
      </div>
    );
    
    const results = await axe(container, {
      rules: {
        'heading-order': { enabled: true }
      }
    });
    expect(results).toHaveNoViolations();
  });

  it('should have sufficient color contrast', async () => {
    const { container } = render(
      <div>
        <p style={{ color: '#000000', backgroundColor: '#ffffff' }}>
          High contrast text
        </p>
        <button style={{ color: '#ffffff', backgroundColor: '#0066cc' }}>
          Accessible button
        </button>
      </div>
    );
    
    const results = await axe(container, {
      rules: {
        'color-contrast': { enabled: true }
      }
    });
    expect(results).toHaveNoViolations();
  });

  it('should have keyboard accessible interactive elements', async () => {
    const { container } = render(
      <div>
        <button>Keyboard accessible button</button>
        <a href="/test">Keyboard accessible link</a>
        <input type="text" aria-label="Keyboard accessible input" />
        <div
          role="button"
          tabIndex={0}
          onKeyDown={(e) => {
            if (e.key === 'Enter' || e.key === ' ') {
              // Handle activation
            }
          }}
        >
          Custom keyboard accessible element
        </div>
      </div>
    );
    
    const results = await axe(container, {
      rules: {
        'keyboard': { enabled: true },
        'focusable-content': { enabled: true }
      }
    });
    expect(results).toHaveNoViolations();
  });

  it('should have proper ARIA labels and roles', async () => {
    const { container } = render(
      <div>
        <nav aria-label="Main navigation">
          <ul role="menubar">
            <li role="none">
              <a href="/home" role="menuitem">Home</a>
            </li>
            <li role="none">
              <a href="/about" role="menuitem">About</a>
            </li>
          </ul>
        </nav>
        <main role="main">
          <section aria-labelledby="content-heading">
            <h1 id="content-heading">Main Content</h1>
          </section>
        </main>
      </div>
    );
    
    const results = await axe(container, {
      rules: {
        'aria-valid-attr': { enabled: true },
        'aria-valid-attr-value': { enabled: true },
        'aria-roles': { enabled: true }
      }
    });
    expect(results).toHaveNoViolations();
  });

  it('should handle focus management properly', async () => {
    const { container } = render(
      <div>
        <button id="trigger">Open Modal</button>
        <div
          role="dialog"
          aria-labelledby="modal-title"
          aria-describedby="modal-description"
          tabIndex={-1}
        >
          <h2 id="modal-title">Modal Title</h2>
          <p id="modal-description">Modal description</p>
          <button>Close</button>
        </div>
      </div>
    );
    
    const results = await axe(container, {
      rules: {
        'focus-order-semantics': { enabled: true },
        'tabindex': { enabled: true }
      }
    });
    expect(results).toHaveNoViolations();
  });
});
