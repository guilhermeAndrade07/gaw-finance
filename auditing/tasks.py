from celery import shared_task


@shared_task(
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={'max_retries': 3},
    acks_late=True,
    reject_on_worker_lost=True,
)
def prune_audit_events():
    from auditing.models import AuditEvent
    from django.utils import timezone

    from django.conf import settings

    retention_days = getattr(settings, 'AUDIT_RETENTION_DAYS', 365)
    cutoff = timezone.now() - timezone.timedelta(days=retention_days)
    deleted_total = 0
    batch_size = 1000

    while True:
        ids = list(
            AuditEvent.objects.filter(
                created_at__lt=cutoff,
            ).values_list('pk', flat=True)[:batch_size]
        )
        if not ids:
            break

        deleted, _ = AuditEvent.objects.filter(pk__in=ids).delete()
        deleted_total += deleted

    return {
        'deleted': deleted_total,
        'retention_days': retention_days,
        'cutoff': cutoff.isoformat(),
    }
