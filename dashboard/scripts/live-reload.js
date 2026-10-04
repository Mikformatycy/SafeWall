// Development only. The standalone file preview never includes this script.
(() => {
  const loader = document.currentScript;
  const markupVersion = loader.dataset.markup;
  let stylesVersion = loader.dataset.styles;

  function replaceStyles(version) {
    return new Promise((resolve, reject) => {
      const current = document.querySelector('link[rel="stylesheet"][href^="/styles.css"]');
      if (!current) { window.location.reload(); resolve(); return; }
      const next = current.cloneNode();
      next.href = `/styles.css?v=${encodeURIComponent(version)}`;
      const timeout = setTimeout(() => { next.remove(); reject(new Error('CSS timeout')); }, 4000);
      next.onload = () => {
        clearTimeout(timeout);
        current.remove();
        stylesVersion = version;
        resolve();
      };
      next.onerror = () => {
        clearTimeout(timeout);
        next.remove();
        reject(new Error('CSS unavailable'));
      };
      current.after(next);
    });
  }

  async function poll() {
    try {
      if (document.hidden) return;
      const response = await fetch('/__dev/revision', { cache: 'no-store', signal: AbortSignal.timeout(4000) });
      if (!response.ok) return;
      const revision = await response.json();
      if (typeof revision.markup !== 'string' || typeof revision.styles !== 'string') return;
      if (revision.markup !== markupVersion) {
        window.location.reload();
        return;
      }
      if (revision.styles !== stylesVersion) await replaceStyles(revision.styles);
    } catch {
      // Preserve the page during a save or server restart; retry on the next poll.
    } finally {
      setTimeout(poll, 1000);
    }
  }
  setTimeout(poll, 1000);
})();
