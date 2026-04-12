from rest_framework import serializers

from .models import Comment, Donation, Rating, Report


class DonationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Donation
        fields = ['id', 'amount', 'project', 'created_at']
        read_only_fields = ['created_at']

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class CommentSerializer(serializers.ModelSerializer):
    replies = serializers.SerializerMethodField()
    user = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = ['id', 'content', 'user', 'parent', 'replies', 'created_at']
        read_only_fields = ['created_at']

    def get_user(self, obj):
        return {
            'id': obj.user.id,
            'first_name': obj.user.first_name,
            'last_name': obj.user.last_name,
        }

    def get_replies(self, obj):
        if obj.parent is not None:
            return []
        return CommentSerializer(
            obj.replies.all(), many=True, context=self.context
        ).data

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class RatingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rating
        fields = ['id', 'project', 'value', 'created_at']
        read_only_fields = ['created_at']

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        rating, _ = Rating.objects.update_or_create(
            user=validated_data['user'],
            project=validated_data['project'],
            defaults={'value': validated_data['value']},
        )
        return rating


class ReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Report
        fields = ['id', 'report_type', 'reason', 'project', 'comment', 'created_at']
        read_only_fields = ['created_at']

    def validate(self, attrs):
        report_type = attrs.get('report_type')
        project = attrs.get('project')
        comment = attrs.get('comment')

        if report_type == 'project' and not project:
            raise serializers.ValidationError('Project report must link to a project.')
        if report_type == 'comment' and not comment:
            raise serializers.ValidationError('Comment report must link to a comment.')
        if project and comment:
            raise serializers.ValidationError(
                'A single report cannot target both a project and a comment.'
            )
        return attrs

    def create(self, validated_data):
        validated_data['reporter'] = self.context['request'].user
        return super().create(validated_data)
