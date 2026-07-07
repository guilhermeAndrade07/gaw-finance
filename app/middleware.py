class FinanceAutoTasksMiddleware:
    """
    Dispara tarefas financeiras automaticas em cada requisicao autenticada:

    - generate_signature_charges: gera cobrancas de assinaturas ativas no
      cartao de credito quando o dia de cobranca e atingido.

    As funcoes sao idempotentes (controladas por last_generated_month/year),
    entao roda-las a cada requisicao e seguro e barato. Os imports sao feitos
    dentro do metodo para evitar importacoes circulares no startup do Django.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if hasattr(request, 'user') and getattr(request.user, 'is_authenticated', False):
            try:
                from signatures.services import generate_signature_charges
                from payment.services import close_past_invoices
                generate_signature_charges()
                close_past_invoices()
            except Exception:
                import logging
                logging.getLogger(__name__).exception(
                    'Erro ao executar tarefas financeiras automaticas'
                )
        return self.get_response(request)
