/**
 * Feature Flags Framework
 * Lightweight runtime feature toggles for safe deployments
 */

export interface FeatureFlag {
  key: string;
  enabled: boolean;
  description: string;
  environment?: string[];
  rolloutPercentage?: number;
}

export interface FeatureFlagConfig {
  [key: string]: FeatureFlag;
}

// Default feature flags configuration
const defaultFlags: FeatureFlagConfig = {
  'new-dashboard': {
    key: 'new-dashboard',
    enabled: false,
    description: 'Enable new dashboard UI components',
    environment: ['development', 'staging'],
    rolloutPercentage: 0,
  },
  'enhanced-search': {
    key: 'enhanced-search',
    enabled: true,
    description: 'Enable enhanced search functionality',
    environment: ['development', 'staging', 'production'],
    rolloutPercentage: 100,
  },
  'ai-suggestions': {
    key: 'ai-suggestions',
    enabled: false,
    description: 'Enable AI-powered content suggestions',
    environment: ['development'],
    rolloutPercentage: 0,
  },
  'bulk-operations': {
    key: 'bulk-operations',
    enabled: true,
    description: 'Enable bulk data operations',
    environment: ['development', 'staging', 'production'],
    rolloutPercentage: 100,
  },
  'real-time-updates': {
    key: 'real-time-updates',
    enabled: false,
    description: 'Enable real-time WebSocket updates',
    environment: ['development', 'staging'],
    rolloutPercentage: 25,
  },
};

class FeatureFlagManager {
  private flags: FeatureFlagConfig;
  private environment: string;
  private userId?: string;

  constructor() {
    this.environment = import.meta.env.VITE_ENVIRONMENT || 'development';
    this.flags = this.loadFlags();
  }

  private loadFlags(): FeatureFlagConfig {
    try {
      // Try to load from environment variables first
      const envFlags = import.meta.env.VITE_FEATURE_FLAGS;
      if (envFlags) {
        return { ...defaultFlags, ...JSON.parse(envFlags) };
      }
      
      // Fallback to localStorage for development
      const storedFlags = localStorage.getItem('featureFlags');
      if (storedFlags) {
        return { ...defaultFlags, ...JSON.parse(storedFlags) };
      }
    } catch (error) {
      console.warn('Failed to load feature flags from storage:', error);
    }
    
    return defaultFlags;
  }

  /**
   * Check if a feature flag is enabled
   */
  isEnabled(flagKey: string): boolean {
    const flag = this.flags[flagKey];
    if (!flag) {
      console.warn(`Feature flag '${flagKey}' not found`);
      return false;
    }

    // Check environment restriction
    if (flag.environment && !flag.environment.includes(this.environment)) {
      return false;
    }

    // Check base enabled state
    if (!flag.enabled) {
      return false;
    }

    // Check rollout percentage
    if (flag.rolloutPercentage !== undefined && flag.rolloutPercentage < 100) {
      return this.isInRollout(flagKey, flag.rolloutPercentage);
    }

    return true;
  }

  /**
   * Determine if user is in rollout percentage
   */
  private isInRollout(flagKey: string, percentage: number): boolean {
    if (percentage === 0) return false;
    if (percentage === 100) return true;

    // Use deterministic hash based on flag key and user identifier
    const identifier = this.userId || 'anonymous';
    const hash = this.simpleHash(`${flagKey}-${identifier}`);
    return (hash % 100) < percentage;
  }

  /**
   * Simple hash function for rollout determination
   */
  private simpleHash(str: string): number {
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
      const char = str.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash; // Convert to 32-bit integer
    }
    return Math.abs(hash);
  }

  /**
   * Set user ID for personalized rollouts
   */
  setUserId(userId: string): void {
    this.userId = userId;
  }

  /**
   * Get all feature flags (for admin/debug purposes)
   */
  getAllFlags(): FeatureFlagConfig {
    return { ...this.flags };
  }

  /**
   * Override a feature flag (for development/testing)
   */
  override(flagKey: string, enabled: boolean): void {
    if (this.environment === 'development') {
      this.flags[flagKey] = {
        ...this.flags[flagKey],
        enabled,
      };
      localStorage.setItem('featureFlags', JSON.stringify(this.flags));
    } else {
      console.warn('Feature flag overrides only allowed in development');
    }
  }

  /**
   * Reset all overrides
   */
  resetOverrides(): void {
    if (this.environment === 'development') {
      localStorage.removeItem('featureFlags');
      this.flags = defaultFlags;
    }
  }
}

// Global feature flag manager instance
export const featureFlags = new FeatureFlagManager();

/**
 * React hook for feature flags
 */
export function useFeatureFlag(flagKey: string): boolean {
  return featureFlags.isEnabled(flagKey);
}

/**
 * Higher-order component for feature flag gating
 */
export function withFeatureFlag<P extends object>(
  flagKey: string,
  Component: React.ComponentType<P>,
  FallbackComponent?: React.ComponentType<P>
) {
  return function FeatureFlaggedComponent(props: P) {
    const isEnabled = useFeatureFlag(flagKey);
    
    if (isEnabled) {
      return <Component {...props} />;
    }
    
    if (FallbackComponent) {
      return <FallbackComponent {...props} />;
    }
    
    return null;
  };
}

/**
 * Feature flag development panel component
 */
export function FeatureFlagDebugPanel(): JSX.Element | null {
  if (featureFlags.getAllFlags()['new-dashboard']?.environment?.includes('production')) {
    return null;
  }

  const flags = featureFlags.getAllFlags();

  if (import.meta.env.MODE === 'production') {
    return null;
  }

  return (
    <div className="fixed bottom-4 right-4 bg-gray-900 text-white p-4 rounded-lg shadow-lg max-w-sm">
      <h3 className="text-sm font-bold mb-2">Feature Flags (Dev)</h3>
      <div className="space-y-1 text-xs">
        {Object.entries(flags).map(([key, flag]) => (
          <div key={key} className="flex items-center justify-between">
            <span className="truncate">{key}</span>
            <button
              onClick={() => featureFlags.override(key, !flag.enabled)}
              className={`ml-2 px-2 py-1 rounded text-xs ${
                featureFlags.isEnabled(key)
                  ? 'bg-green-600 hover:bg-green-700'
                  : 'bg-red-600 hover:bg-red-700'
              }`}
            >
              {featureFlags.isEnabled(key) ? 'ON' : 'OFF'}
            </button>
          </div>
        ))}
      </div>
      <button
        onClick={() => featureFlags.resetOverrides()}
        className="mt-2 text-xs text-blue-400 hover:text-blue-300"
      >
        Reset All
      </button>
    </div>
  );
}
