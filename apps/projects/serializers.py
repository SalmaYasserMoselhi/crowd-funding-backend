from rest_framework import serializers

from .models import Category, Project, ProjectMedia, Tag


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name']


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'description', 'created_at']


class ProjectMediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectMedia
        fields = ['id', 'image', 'is_cover', 'order']


class ProjectListSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    cover_image = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = [
            'id',
            'title',
            'total_target',
            'current_donations',
            'average_rating',
            'status',
            'is_featured',
            'category',
            'cover_image',
            'start_time',
            'end_time',
        ]

    def get_cover_image(self, obj):
        cover = obj.media.filter(is_cover=True).first() or obj.media.first()
        if cover:
            request = self.context.get('request')
            return request.build_absolute_uri(cover.image.url) if request else cover.image.url
        return None


class ProjectDetailSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)
    category = CategorySerializer(read_only=True)
    media = ProjectMediaSerializer(many=True, read_only=True)
    owner = serializers.SerializerMethodField()
    similar_projects = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = [
            'id',
            'title',
            'details',
            'total_target',
            'current_donations',
            'average_rating',
            'status',
            'is_featured',
            'category',
            'tags',
            'media',
            'owner',
            'similar_projects',
            'start_time',
            'end_time',
            'created_at',
        ]

    def get_owner(self, obj):
        return {
            'id': obj.owner.id,
            'first_name': obj.owner.first_name,
            'last_name': obj.owner.last_name,
        }

    def get_similar_projects(self, obj):
        similar = obj.get_similar_projects()
        return ProjectListSerializer(similar, many=True, context=self.context).data


class ProjectCreateUpdateSerializer(serializers.ModelSerializer):
    tag_names = serializers.ListField(
        child=serializers.CharField(max_length=50), write_only=True, required=False
    )
    uploaded_images = serializers.ListField(
        child=serializers.ImageField(), write_only=True, required=False
    )

    class Meta:
        model = Project
        fields = [
            'title',
            'details',
            'category',
            'total_target',
            'start_time',
            'end_time',
            'tag_names',
            'uploaded_images',
        ]

    def create(self, validated_data):
        tag_names = validated_data.pop('tag_names', [])
        images = validated_data.pop('uploaded_images', [])
        validated_data['owner'] = self.context['request'].user

        project = Project.objects.create(**validated_data)

        for name in tag_names:
            tag, _ = Tag.objects.get_or_create(name=name.lower())
            project.tags.add(tag)

        for idx, img in enumerate(images):
            ProjectMedia.objects.create(
                project=project,
                image=img,
                order=idx,
                is_cover=(idx == 0),
            )

        return project

    def update(self, instance, validated_data):
        tag_names = validated_data.pop('tag_names', None)
        images = validated_data.pop('uploaded_images', [])

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if tag_names is not None:
            instance.tags.clear()
            for name in tag_names:
                tag, _ = Tag.objects.get_or_create(name=name.lower())
                instance.tags.add(tag)

        for idx, img in enumerate(images):
            ProjectMedia.objects.create(
                project=instance,
                image=img,
                order=instance.media.count() + idx,
            )

        return instance
