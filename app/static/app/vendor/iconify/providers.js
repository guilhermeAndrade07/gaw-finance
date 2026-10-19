// Iconify offline: aponta o provider padrao (chave "" - usada por icones "mdi:*")
// para os icon data servidos localmente. Arquivo externo p/ respeitar CSP 'self'.
window.IconifyProviders = { "": { resources: ["/static/app/vendor/iconify"] } };
