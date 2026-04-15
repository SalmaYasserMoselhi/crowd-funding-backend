from django.db import migrations, models
from django.utils.text import slugify


def populate_slugs(apps, schema_editor):
    Category = apps.get_model('projects', 'Category')
    for category in Category.objects.all():
        category.slug = slugify(category.name)
        category.save(update_fields=['slug'])


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0001_initial'),
    ]

    operations = [
        # Step 1 — add the field as optional so the migration runs cleanly
        #           even if there are existing rows in the table.
        migrations.AddField(
            model_name='category',
            name='slug',
            field=models.SlugField(max_length=120, blank=True, default=''),
            preserve_default=False,
        ),
        # Step 2 — fill slugs for any existing categories
        migrations.RunPython(populate_slugs, reverse_code=migrations.RunPython.noop),
        # Step 3 — now it's safe to enforce uniqueness
        migrations.AlterField(
            model_name='category',
            name='slug',
            field=models.SlugField(max_length=120, unique=True),
        ),
    ]
