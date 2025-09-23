export interface TranslationResponse {
  filename: string;
  translated_text: string;
}

const DEFAULT_API_BASE_URL = 'http://localhost:8000';
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? DEFAULT_API_BASE_URL;

export async function translateDocument(file: File, targetLanguage: string): Promise<TranslationResponse> {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('target_language', targetLanguage);

  const response = await fetch(`${API_BASE_URL}/translate`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    let detail = 'La traduction a échoué.';
    try {
      const payload = (await response.json()) as { detail?: string };
      if (payload.detail) {
        detail = payload.detail;
      }
    } catch (error) {
      // Ignore JSON parsing errors and surface the generic message
    }
    throw new Error(detail);
  }

  const data = (await response.json()) as TranslationResponse;
  if (!data.filename || !data.translated_text) {
    throw new Error("La réponse du serveur est incomplète.");
  }
  return data;
}
