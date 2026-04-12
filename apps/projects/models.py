from django.conf import settings
from django.db import models
from django.utils import timezone

from core.models import TrackableModel


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Categories'

    def __str__(self):
        return self.name


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return f'#{self.name}'


class Project(TrackableModel):
    STATUS_CHOICES = (
        ('running', 'Running'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
    )

    title = models.CharField(max_length=255)
    details = models.TextField()
    total_target = models.DecimalField(max_digits=12, decimal_places=2)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='running')

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='projects'
    )
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    tags = models.ManyToManyField(Tag, related_name='projects', blank=True)

    # Denormalized fields — updated via Donation.save() and Rating.save()
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    current_donations = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    is_featured = models.BooleanField(default=False)

    @property
    def is_running(self):
        now = timezone.now()
        return (
            self.status == 'running'
            and self.start_time <= now <= self.end_time
        )

    def can_be_cancelled(self):
        """True only when donations are LESS THAN 25% of target (strict less-than)."""
        limit = self.total_target * 25 / 100
        return self.current_donations < limit

    def get_similar_projects(self):
        """Return up to 4 other projects sharing at least one tag."""
        return (
            Project.objects.filter(tags__in=self.tags.all())
            .exclude(id=self.id)
            .distinct()[:4]
        )

    def __str__(self):
        return self.title


class ProjectMedia(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='media')
    image = models.ImageField(upload_to='project_images/')
    is_cover = models.BooleanField(default=False)
    order = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', '-created_at']
        verbose_name_plural = 'Project Media'
