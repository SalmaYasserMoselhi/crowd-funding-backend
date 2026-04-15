from rest_framework import serializers

from apps.projects.models import Category, Project


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'description', 'created_at']


class ProjectCardSerializer(serializers.ModelSerializer):
    """
    Serializer matching CONTRACT #7 — ProjectCardProps interface:
    { id, title, image, funded_pct, avg_rating, category }
    """
    image = serializers.SerializerMethodField()
    funded_pct = serializers.SerializerMethodField()
    avg_rating = serializers.SerializerMethodField()
    category = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = Project
        fields = ['id', 'title', 'image', 'funded_pct', 'avg_rating', 'category']

    def get_image(self, obj):
        cover = obj.media.filter(is_cover=True).first() or obj.media.first()
        if cover:
            request = self.context.get('request')
            return request.build_absolute_uri(cover.image.url) if request else cover.image.url
        return None

    def get_funded_pct(self, obj):
        if obj.total_target <= 0:
            return 0
        return round(float(obj.current_donations) / float(obj.total_target) * 100)

    def get_avg_rating(self, obj):
        return round(float(obj.average_rating), 1)
