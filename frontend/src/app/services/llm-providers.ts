export interface LlmProvider {
  id: string;
  labelKey: string;
  baseUrl: string;
  requiresKey: boolean;
  keyPlaceholder: string;
  docs?: string;
  /** Built-in default provider (localhost Ollama). Cannot be deleted or disconnected. */
  readonly default?: boolean;
  /** URL where an access token / API key for this provider can be generated. */
  tokenUrl?: string;
}

export const LLM_PROVIDERS: LlmProvider[] = [
  {
    id: 'ollama',
    labelKey: 'llm.provider.ollama',
    baseUrl: 'http://localhost:11434',
    requiresKey: false,
    keyPlaceholder: '',
    default: false,
  },
  {
    id: 'openrouter',
    labelKey: 'llm.provider.openrouter',
    baseUrl: 'https://openrouter.ai/api/v1',
    requiresKey: true,
    keyPlaceholder: 'sk-or-...',
    tokenUrl: 'https://openrouter.ai/settings/keys',
  },
  {
    id: 'openai',
    labelKey: 'llm.provider.openai',
    baseUrl: 'https://api.openai.com/v1',
    requiresKey: true,
    keyPlaceholder: 'sk-...',
    tokenUrl: 'https://platform.openai.com/api-keys',
  },
  {
    id: 'groq',
    labelKey: 'llm.provider.groq',
    baseUrl: 'https://api.groq.com/openai/v1',
    requiresKey: true,
    keyPlaceholder: 'gsk_...',
    tokenUrl: 'https://console.groq.com/keys',
  },
  {
    id: 'together',
    labelKey: 'llm.provider.together',
    baseUrl: 'https://api.together.xyz/v1',
    requiresKey: true,
    keyPlaceholder: 'sk-...',
    tokenUrl: 'https://api.together.ai/settings/api-keys',
  },
  {
    id: 'custom',
    labelKey: 'llm.provider.custom',
    baseUrl: '',
    requiresKey: false,
    keyPlaceholder: '',
  },
  {
    id: 'devidham',
    labelKey: 'llm.provider.devidham',
    baseUrl: 'https://dev.idh.am/v1',
    requiresKey: true,
    keyPlaceholder: 'token',
    default: true,
  },
];

export const DEFAULT_PROVIDER = 'ollama';

export function getProvider(providerId: string | null | undefined): LlmProvider {
  const id = providerId || DEFAULT_PROVIDER;
  return LLM_PROVIDERS.find(p => p.id === id) || LLM_PROVIDERS.find(p => p.id === DEFAULT_PROVIDER)!;
}

/** Resolve the effective endpoint for a provider given a stored endpoint. */
export function providerEndpoint(providerId: string | null | undefined, storedEndpoint: string | null | undefined): string {
  const id = providerId || DEFAULT_PROVIDER;
  if (id !== 'custom') {
    const p = getProvider(id);
    if (storedEndpoint) return storedEndpoint;
    return p.baseUrl;
  }
  return storedEndpoint || '';
}

/** True if the endpoint looks like it belongs to the given preset provider. */
export function endpointMatchesProvider(providerId: string, endpoint: string | null | undefined): boolean {
  const b = getProvider(providerId).baseUrl;
  if (!b) return false;
  return (endpoint || '').startsWith(b);
}