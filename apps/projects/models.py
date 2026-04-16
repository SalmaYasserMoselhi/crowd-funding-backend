from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.text import slugify

from django.utils.text import slugify

from core.models import TrackableModel


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            while Category.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f'{base_slug}-{counter}'
                counter += 1
            self.slug = slug
        return super().save(*args, **kwargs)


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)

    class Meta:
        ordering = ['name']

    def save(self, *args, **kwargs):
        self.name = self.name.lower().strip()
        return super().save(*args, **kwargs)

    def __str__(self):
        return f'#{self.name}'


class ProjectStatus(models.TextChoices):
    RUNNING = 'running', 'Running'
    ACTIVE = 'active', 'Active'
    CANCELLED = 'cancelled', 'Cancelled'
    COMPLETED = 'completed', 'Completed'

class Project(TrackableModel):
    title = models.CharField(max_length=255)
    details = models.TextField()
    
    total_target = models.DecimalField(max_digits=12, decimal_places=2)
    current_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)

    start_time = models.DateTimeField()
    end_time = models.DateTimeField()

    status = models.CharField(max_length=20, choices=ProjectStatus.choices, default=ProjectStatus.ACTIVE)
    is_featured = models.BooleanField(default=False)
    is_cancelled = models.BooleanField(default=False)

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='projects'
    )

    tags = models.ManyToManyField(Tag, related_name='projects', blank=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='projects')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    current_donations = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)

    @property
    def is_running(self):
        now = timezone.now()
        return (
            not self.is_cancelled
            and self.start_time <= now <= self.end_time
        )

    @property
    def funded_percentage(self):
        if self.total_target <= 0:
            return 0
        return round((float(self.current_donations) / float(self.total_target)) * 100, 2)

    def clean(self):
        if self.start_time and self.end_time:
            if self.end_time <= self.start_time:
                raise ValidationError(
                    {"end_time": "End time must be after start time."}
                )
        if self.total_target is not None and self.total_target <= 0:
            raise ValidationError(
                {"total_target": "Total target must be a positive amount."}
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

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=["-created_at"]),
            models.Index(fields=["category", "-created_at"]),
            models.Index(fields=["is_featured", "-created_at"]),
            models.Index(fields=["is_cancelled", "start_time", "end_time"]),
        ]
    def __str__(self):
        return self.title

    class Meta:
        indexes = [
            models.Index(
                fields=['status', '-average_rating'],
                name='idx_running_top_rated',
            ),
            models.Index(
                fields=['status', 'is_featured', '-created_at'],
                name='idx_featured',
            ),
            models.Index(
                fields=['category', '-created_at'],
                name='idx_category_latest',
            ),
        ]


class ProjectMedia(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='media')
    image = models.ImageField(upload_to='project_images/')
    is_cover = models.BooleanField(default=False)
    order = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', '-created_at']
        verbose_name_plural = 'Project Media'
    
    def __str__(self):
        return f'Media for {self.project.title} (Cover: {self.is_cover})'
