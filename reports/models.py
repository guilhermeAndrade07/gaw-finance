from django.db import models


class GeneratedReport(models.Model):
    REPORT_TYPES = [
        ('custom', 'Personalizado'),
    ]

    user = models.ForeignKey(
        'auth.User',
        on_delete=models.CASCADE,
        related_name='reports',
    )
    report_type = models.CharField(max_length=50, choices=REPORT_TYPES)
    generated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-generated_at']

    def __str__(self):
        return f'{self.get_report_type_display()} - {self.generated_at:%d/%m/%Y %H:%M}'
