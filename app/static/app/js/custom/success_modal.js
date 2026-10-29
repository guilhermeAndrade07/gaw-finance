// Modal de sucesso (usado por components/_success_modal.html).
// Externo por causa do CSP do app: script-src 'self' bloqueia scripts inline.
document.addEventListener('DOMContentLoaded', function () {
  const params = new URLSearchParams(window.location.search);
  if (params.get('created') !== '1') return;

  const el = document.getElementById('successModal');
  if (!el) {
    console.error('[success-modal] Modal não encontrado no DOM.');
    return;
  }

  let opened = false;
  if (window.bootstrap && window.bootstrap.Modal) {
    new window.bootstrap.Modal(el).show();
    opened = true;
  } else if (window.jQuery) {
    window.jQuery(el).modal('show');
    opened = true;
  } else {
    console.error('[success-modal] Nenhum mecanismo de modal disponível (bootstrap/jQuery).');
  }

  if (opened) {
    console.info('[success-modal] Modal aberto.');
  }

  params.delete('created');
  const query = params.toString();
  window.history.replaceState({}, document.title, window.location.pathname + (query ? '?' + query : ''));
});
