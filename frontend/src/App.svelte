<script lang="ts">
  import { translateDocument } from './lib/api';

  const languages = [
    'English',
    'French',
    'Spanish',
    'German',
    'Italian',
    'Portuguese',
  ];

  let file: File | null = null;
  let targetLanguage = 'English';
  let isSubmitting = false;
  let error: string | null = null;
  let translatedText = '';
  let translatedFilename = '';

  const version = __APP_VERSION__ ?? '0.0.0';

  const handleFileChange = (event: Event) => {
    const target = event.currentTarget as HTMLInputElement;
    file = target.files?.[0] ?? null;
    translatedText = '';
    translatedFilename = '';
    error = null;
  };

  const handleSubmit = async (event: Event) => {
    event.preventDefault();
    if (!file) {
      error = 'Veuillez sélectionner un document à traduire.';
      return;
    }
    isSubmitting = true;
    error = null;

    try {
      const response = await translateDocument(file, targetLanguage);
      translatedText = response.translated_text;
      translatedFilename = response.filename;
    } catch (err) {
      error = err instanceof Error ? err.message : 'Une erreur inconnue est survenue.';
    } finally {
      isSubmitting = false;
    }
  };

  const downloadTranslation = () => {
    if (!translatedText) return;
    const blob = new Blob([translatedText], { type: file?.type || 'text/plain' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = translatedFilename || file?.name || 'translation.txt';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(link.href);
  };
</script>

<main>
  <header>
    <h1>TranslateDoc</h1>
    <p>Traduisez vos documents tout en conservant leur format.</p>
  </header>

  <form class="card" on:submit|preventDefault={handleSubmit}>
    <label class="field">
      <span>Document</span>
      <input name="document" type="file" accept=".txt,.md,.markdown,.rst,.html,.htm,.json,.yml,.yaml" on:change={handleFileChange} />
    </label>

    <label class="field">
      <span>Langue cible</span>
      <select bind:value={targetLanguage}>
        {#each languages as language}
          <option value={language}>{language}</option>
        {/each}
      </select>
    </label>

    <button class="primary" type="submit" disabled={isSubmitting}>
      {#if isSubmitting}
        Traduction en cours…
      {:else}
        Traduire
      {/if}
    </button>
  </form>

  {#if error}
    <p class="error" role="alert">{error}</p>
  {/if}

  {#if translatedText}
    <section class="result card">
      <div class="result__header">
        <h2>Traduction</h2>
        <button type="button" on:click={downloadTranslation}>Télécharger</button>
      </div>
      <p class="filename">{translatedFilename}</p>
      <textarea readonly rows="12" bind:value={translatedText}></textarea>
    </section>
  {/if}

  <footer>
    <small>Version {version}</small>
  </footer>
</main>

<style>
  :global(body) {
    margin: 0;
    font-family: 'Inter', system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    background: #0f172a;
    color: #f8fafc;
    min-height: 100vh;
  }

  main {
    max-width: 960px;
    margin: 0 auto;
    padding: 2rem 1.5rem 4rem;
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
  }

  header {
    text-align: center;
  }

  h1 {
    margin-bottom: 0.5rem;
  }

  .card {
    background: rgba(15, 23, 42, 0.7);
    border: 1px solid rgba(148, 163, 184, 0.2);
    border-radius: 1rem;
    padding: 1.5rem;
    display: flex;
    flex-direction: column;
    gap: 1rem;
    box-shadow: 0 10px 30px rgba(15, 23, 42, 0.3);
  }

  .field {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .field span {
    font-weight: 600;
  }

  input[type='file'],
  select,
  textarea {
    padding: 0.75rem;
    border-radius: 0.75rem;
    border: 1px solid rgba(148, 163, 184, 0.3);
    background: rgba(15, 23, 42, 0.6);
    color: inherit;
  }

  textarea {
    resize: vertical;
    min-height: 240px;
  }

  button {
    align-self: flex-start;
    padding: 0.75rem 1.5rem;
    border-radius: 999px;
    border: none;
    cursor: pointer;
    font-weight: 600;
  }

  button.primary {
    background: linear-gradient(135deg, #6366f1, #8b5cf6);
    color: #f8fafc;
  }

  button:disabled {
    opacity: 0.5;
    cursor: wait;
  }

  .error {
    background: rgba(239, 68, 68, 0.15);
    color: #fca5a5;
    padding: 1rem;
    border-radius: 0.75rem;
  }

  .result__header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 1rem;
  }

  .result button {
    background: rgba(99, 102, 241, 0.15);
    color: #c7d2fe;
    border: 1px solid rgba(99, 102, 241, 0.35);
  }

  .filename {
    font-family: 'JetBrains Mono', 'Fira Code', monospace;
    opacity: 0.7;
  }

  footer {
    margin-top: auto;
    text-align: center;
    opacity: 0.6;
  }
</style>
