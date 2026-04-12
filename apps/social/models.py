from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Avg, Sum

from core.models import TrackableModel


class Donation(models.Model):
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='donations'
    )
    project = models.ForeignKey(
        'projects.Project', on_delete=models.CASCADE, related_name='donations'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        total = (
            Donation.objects.filter(project=self.project).aggregate(Sum('amount'))[
                'amount__sum'
            ]
            or 0
        )
        self.project.current_donations = total
        self.project.save(update_fields=['current_donations'])


class Comment(TrackableModel):
    content = models.TextField()
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    project = models.ForeignKey(
        'projects.Project', on_delete=models.CASCADE, related_name='comments'
    )
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='replies',
    )

    def __str__(self):
        return f'Comment by {self.user.first_name} on {self.project.title}'


class Rating(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    project = models.ForeignKey(
        'projects.Project', on_delete=models.CASCADE, related_name='ratings'
    )
    value = models.PositiveSmallIntegerField(choices=[(i, i) for i in range(1, 6)])
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'project')

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        avg = (
            Rating.objects.filter(project=self.project).aggregate(Avg('value'))[
                'value__avg'
            ]
            or 0
        )
        self.project.average_rating = avg
        self.project.save(update_fields=['average_rating'])


class Report(models.Model):
    REPORT_TYPES = (
        ('project', 'Project'),
        ('comment', 'Comment'),
    )

    report_type = models.CharField(max_length=10, choices=REPORT_TYPES)
    reason = models.TextField()
    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE
    )
    project = models.ForeignKey(
        'projects.Project',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='reports',
    )
    comment = models.ForeignKey(
        Comment,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='reports',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        if self.report_type == 'project' and not self.project:
            raise ValidationError('Project report must link to a project.')
        if self.report_type == 'comment' and not self.comment:
            raise ValidationError('Comment report must link to a comment.')
        if self.project and self.comment:
            raise ValidationError(
                'A single report cannot target both a project and a comment.'
            )

    def __str__(self):
        return f'Report ({self.report_type}) by {self.reporter.email}'
