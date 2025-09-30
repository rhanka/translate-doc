<script>
  import { onDestroy, onMount } from 'svelte';

  const API_BASE = (import.meta.env.VITE_BACKEND_URL || '').replace(/\/$/, '');

  let file = null;
  let currentJob = null;
  let jobs = [];
  let errorMessage = '';
  let pollingTimer = null;
  let isSubmitting = false;

  const formatProgress = (progress) => `${Math.round(progress * 100)}%`;

  const apiUrl = (path) => `${API_BASE}${path}`;

  async function refreshJobs() {
    try {
      const response = await fetch(apiUrl('/api/jobs'));
      if (!response.ok) {
        throw new Error('Impossible de récupérer les traductions en cours');
      }
      jobs = await response.json();
    } catch (error) {
      console.error(error);
    }
  }

  function stopPolling() {
    if (pollingTimer) {
      clearInterval(pollingTimer);
      pollingTimer = null;
    }
  }

  async function pollJob(jobId) {
    stopPolling();
    pollingTimer = setInterval(async () => {
      try {
        const response = await fetch(apiUrl(`/api/jobs/${jobId}`));
        if (!response.ok) {
          throw new Error('Impossible de suivre la traduction');
        }
        currentJob = await response.json();
        if (currentJob.status === 'completed' || currentJob.status === 'failed') {
          stopPolling();
          await refreshJobs();
        }
      } catch (error) {
        console.error(error);
        stopPolling();
      }
    }, 1500);
  }

  async function submit(event) {
    event.preventDefault();
    errorMessage = '';
    if (!file) {
      errorMessage = 'Veuillez sélectionner un fichier (.txt, .md, .docx, .pptx).';
      return;
    }
    try {
      isSubmitting = true;
      const formData = new FormData();
      formData.append('file', file);
      const response = await fetch(apiUrl('/api/jobs'), {
        method: 'POST',
        body: formData,
      });
      if (!response.ok) {
        throw new Error('La traduction a échoué.');
      }
      currentJob = await response.json();
      file = null;
      await refreshJobs();
      pollJob(currentJob.id);
    } catch (error) {
      errorMessage = error.message;
      console.error(error);
    } finally {
      isSubmitting = false;
    }
  }

  function handleFileChange(event) {
    const selected = event.target.files?.[0];
    file = selected || null;
  }

  onMount(refreshJobs);
  onDestroy(stopPolling);
</script>

<main class="page">
  <section class="hero">
    <div>
      <h1>Translate Doc</h1>
      <p>
        Téléversez vos documents texte, DOCX ou PPTX pour les traduire en anglais tout en conservant leur mise en forme.
      </p>
    </div>
  </section>

  <section class="card">
    <form on:submit|preventDefault={submit} class="upload-form">
      <label class="file-input">
        <span>Choisir un fichier</span>
        <input type="file" on:change={handleFileChange} accept=".txt,.md,.docx,.pptx" />
      </label>
      {#if file}
        <p class="filename">{file.name}</p>
      {/if}
      <button class="primary" type="submit" disabled={isSubmitting}>
        {#if isSubmitting}
          Envoi...
        {:else}
          Traduire en anglais
        {/if}
      </button>
      {#if errorMessage}
        <p class="error">{errorMessage}</p>
      {/if}
    </form>
  </section>

  {#if currentJob}
    <section class="card">
      <h2>Progression en temps réel</h2>
      <div class="progress">
        <div
          class="progress-bar"
          style={`width: ${formatProgress(currentJob.progress || 0)};`}
          aria-valuemin="0"
          aria-valuemax="1"
          role="progressbar"
        ></div>
      </div>
      <p class="status">
        <strong>Statut :</strong> {currentJob.status}
      </p>
      {#if currentJob.message}
        <p class="message">{currentJob.message}</p>
      {/if}
      {#if currentJob.status === 'completed'}
        <a class="primary" href={apiUrl(currentJob.result_url)} download> Télécharger la traduction anglaise </a>
      {:else if currentJob.status === 'failed'}
        <p class="error">Une erreur est survenue pendant la traduction.</p>
      {/if}
    </section>
  {/if}

  <section class="card">
    <h2>Historique récent</h2>
    {#if jobs.length === 0}
      <p>Aucun travail de traduction pour le moment.</p>
    {:else}
      <table>
        <thead>
          <tr>
            <th>Fichier</th>
            <th>Statut</th>
            <th>Progression</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {#each jobs as job}
            <tr>
              <td>{job.filename}</td>
              <td class={`status-${job.status}`}>{job.status}</td>
              <td>{formatProgress(job.progress || 0)}</td>
              <td>
                {#if job.status === 'completed'}
                  <a href={apiUrl(job.result_url)} download>Télécharger</a>
                {/if}
              </td>
            </tr>
          {/each}
        </tbody>
      </table>
    {/if}
  </section>
</main>

<style>
  .page {
    max-width: 960px;
    margin: 0 auto;
    padding: 2rem 1.5rem 4rem;
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
  }

  .hero {
    background: linear-gradient(135deg, rgba(56, 189, 248, 0.3), rgba(14, 116, 144, 0.3));
    border-radius: 16px;
    padding: 2.5rem;
    box-shadow: 0 20px 40px rgba(15, 23, 42, 0.4);
  }

  .hero h1 {
    margin: 0 0 0.75rem;
    font-size: 2.5rem;
  }

  .card {
    background: rgba(15, 23, 42, 0.8);
    border-radius: 16px;
    padding: 1.75rem;
    box-shadow: 0 16px 30px rgba(2, 6, 23, 0.45);
    border: 1px solid rgba(148, 163, 184, 0.1);
  }

  .upload-form {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .file-input {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    padding: 0.75rem 1.5rem;
    background: rgba(30, 64, 175, 0.25);
    border-radius: 12px;
    border: 1px dashed rgba(96, 165, 250, 0.4);
    color: #e2e8f0;
    transition: background 0.2s ease, border 0.2s ease;
    cursor: pointer;
  }

  .file-input:hover {
    background: rgba(59, 130, 246, 0.25);
    border-color: rgba(96, 165, 250, 0.8);
  }

  .file-input input {
    display: none;
  }

  .filename {
    font-size: 0.9rem;
    color: rgba(226, 232, 240, 0.7);
  }

  .primary {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    background: linear-gradient(135deg, #38bdf8, #0ea5e9);
    border: none;
    border-radius: 12px;
    padding: 0.75rem 1.5rem;
    color: #0f172a;
    font-weight: 600;
    text-decoration: none;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
  }

  .primary:hover {
    transform: translateY(-1px);
    box-shadow: 0 10px 18px rgba(14, 165, 233, 0.35);
  }

  .primary:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .progress {
    width: 100%;
    height: 12px;
    background: rgba(148, 163, 184, 0.2);
    border-radius: 999px;
    overflow: hidden;
    margin: 1rem 0;
  }

  .progress-bar {
    height: 100%;
    background: linear-gradient(135deg, #38bdf8, #0ea5e9);
    transition: width 0.3s ease;
  }

  .status {
    margin: 0.5rem 0;
  }

  .message {
    color: rgba(226, 232, 240, 0.8);
  }

  .error {
    color: #fca5a5;
  }

  table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.95rem;
  }

  th,
  td {
    text-align: left;
    padding: 0.75rem 0.5rem;
    border-bottom: 1px solid rgba(148, 163, 184, 0.15);
  }

  .status-completed {
    color: #4ade80;
  }

  .status-processing {
    color: #fbbf24;
  }

  .status-failed {
    color: #f87171;
  }

  @media (max-width: 640px) {
    .hero {
      padding: 2rem;
    }

    table {
      font-size: 0.85rem;
    }
  }
</style>
