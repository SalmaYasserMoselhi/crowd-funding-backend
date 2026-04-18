from rest_framework import serializers

from apps.social.models import Rating

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
        fields = ['id', 'image', 'is_cover', 'order', 'created_at']


class ProjectListSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    cover_image = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = [
            'id',
            'title',
            'total_target',
            'current_amount',
            'current_donations',
            'average_rating',
            'status',
            'is_featured',
            'is_cancelled',
            'category',
            'cover_image',
            'start_time',
            'end_time',
            'created_at',
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
    funded_percentage = serializers.SerializerMethodField()
    is_running = serializers.ReadOnlyField()
    user_rating = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = [
            'id',
            'title',
            'details',
            'total_target',
            'current_amount',
            'current_donations',
            'average_rating',
            'user_rating',
            'funded_percentage',
            'is_running',
            'status',
            'is_featured',
            'is_cancelled',
            'category',
            'tags',
            'media',
            'owner',
            'similar_projects',
            'start_time',
            'end_time',
            'created_at',
            'updated_at',
        ]

    def get_owner(self, obj):
        return {
            'id': obj.owner.id,
            'first_name': obj.owner.first_name,
            'last_name': obj.owner.last_name,
            'email': obj.owner.email,
        }

    def get_similar_projects(self, obj):
        similar = obj.get_similar_projects()
        return ProjectListSerializer(similar, many=True, context=self.context).data

    def get_funded_percentage(self, obj):
        return obj.funded_percentage

    def get_user_rating(self, obj):
        user_ratings = getattr(obj, 'user_specific_rating', [])
        if user_ratings:
            return user_ratings[0].value
        
        request = self.context.get('request')
        if request and request.user.is_authenticated and not hasattr(obj, 'user_specific_rating'):
            rating = Rating.objects.filter(project=obj, user=request.user).first()
            return rating.value if rating else None
            
        return None

class ProjectCreateUpdateSerializer(serializers.ModelSerializer):
    tag_names = serializers.ListField(
        child=serializers.CharField(max_length=50),
        write_only=True,
        required=False,
    )
    uploaded_images = serializers.ListField(
        child=serializers.ImageField(),
        write_only=True,
        required=False,
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

    def validate(self, attrs):
        start_time = attrs.get('start_time')
        end_time = attrs.get('end_time')

        if start_time and end_time and end_time <= start_time:
            raise serializers.ValidationError({'end_time': 'End time must be after start time.'})

        return attrs

    def validate_total_target(self, value):
        if value <= 0:
            raise serializers.ValidationError('Total target must be a positive amount.')
        return value

    def create(self, validated_data):
        tag_names = validated_data.pop('tag_names', [])
        images = validated_data.pop('uploaded_images', [])
        validated_data['owner'] = self.context['request'].user

        project = Project.objects.create(**validated_data)

        for name in tag_names:
            cleaned_name = name.lower().strip()
            if cleaned_name:
                tag, _ = Tag.objects.get_or_create(name=cleaned_name)
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
                cleaned_name = name.lower().strip()
                if cleaned_name:
                    tag, _ = Tag.objects.get_or_create(name=cleaned_name)
                    instance.tags.add(tag)

        for idx, img in enumerate(images):
            ProjectMedia.objects.create(
                project=instance,
                image=img,
                order=instance.media.count() + idx,
            )

        return instance
