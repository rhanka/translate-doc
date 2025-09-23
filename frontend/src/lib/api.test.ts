import { beforeEach, afterEach, describe, expect, it, vi } from 'vitest';

import { translateDocument } from './api';

const mockFile = new File(['hello'], 'example.md', { type: 'text/markdown' });

describe('translateDocument', () => {
  const originalFetch = globalThis.fetch;

  beforeEach(() => {
    vi.resetAllMocks();
  });

  afterEach(() => {
    globalThis.fetch = originalFetch;
  });

  it('returns the translated document when the API call is successful', async () => {
    const responsePayload = {
      filename: 'example.french.md',
      translated_text: 'bonjour',
    };

    const mockResponse = {
      ok: true,
      json: vi.fn().mockResolvedValue(responsePayload),
    } as unknown as Response;

    globalThis.fetch = vi.fn().mockResolvedValue(mockResponse);

    const result = await translateDocument(mockFile, 'French');

    expect(globalThis.fetch).toHaveBeenCalled();
    expect(mockResponse.json).toHaveBeenCalledTimes(1);
    expect(result).toEqual(responsePayload);
  });

  it('throws an error when the API returns an error payload', async () => {
    const mockResponse = {
      ok: false,
      json: vi.fn().mockResolvedValue({ detail: 'bad request' }),
    } as unknown as Response;

    globalThis.fetch = vi.fn().mockResolvedValue(mockResponse);

    await expect(translateDocument(mockFile, 'French')).rejects.toThrow('bad request');
    expect(mockResponse.json).toHaveBeenCalledTimes(1);
  });

  it('throws a generic error when the error response is not JSON', async () => {
    const mockResponse = {
      ok: false,
      json: vi.fn().mockRejectedValue(new Error('no json')),
    } as unknown as Response;

    globalThis.fetch = vi.fn().mockResolvedValue(mockResponse);

    await expect(translateDocument(mockFile, 'French')).rejects.toThrow('La traduction a échoué.');
    expect(mockResponse.json).toHaveBeenCalledTimes(1);
  });
});
