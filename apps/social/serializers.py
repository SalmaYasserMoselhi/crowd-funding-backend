from rest_framework import serializers

from apps.projects.models import Project

from .models import Comment, Donation, Rating, Report
from django.shortcuts import get_object_or_404

class DonationResponseSerializer(serializers.ModelSerializer):
    funded_pct = serializers.SerializerMethodField()

    class Meta:
        model = Donation
        fields = ['id', 'amount', 'project', 'created_at', 'funded_pct']

    def get_funded_pct(self, obj):
        project = obj.project
        if project.total_target > 0:
            return (project.current_donations / project.total_target) * 100
        return 0

class DonationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Donation
        fields = ['id', 'amount', 'project', 'created_at']
        read_only_fields = ['created_at', 'project']

    def validate(self, attrs):
        user = self.context['request'].user
        project_id = self.context['view'].kwargs.get('project_id')
        from apps.projects.models import Project
        project = get_object_or_404(Project, pk=project_id)

        if project.owner == user:
            raise serializers.ValidationError("Owners cannot donate to their own projects.")
        
        return attrs

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)

class UserDonationHistorySerializer(serializers.ModelSerializer):
    project_title = serializers.CharField(source='project.title', read_only=True)

    class Meta:
        model = Donation
        fields = ['id', 'project_title', 'amount', 'created_at']
        read_only_fields = ['id', 'project_title', 'amount', 'created_at']

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
        validated_data['project'] = self.context['project']
        return super().create(validated_data)


class CommentReplySerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = ['id', 'content', 'user', 'created_at']
        read_only_fields = ['id', 'user', 'created_at']

    def get_user(self, obj):
        return {
            'id': obj.user.id,
            'first_name': obj.user.first_name,
            'last_name': obj.user.last_name,
        }

    def create(self, validated_data):
        parent_comment = self.context['parent_comment']
        validated_data['user'] = self.context['request'].user
        validated_data['parent'] = parent_comment
        validated_data['project'] = parent_comment.project
        return super().create(validated_data)


class RatingUpsertSerializer(serializers.ModelSerializer):
    new_project_average = serializers.FloatField(source='project.average_rating', read_only=True)
    user_rating = serializers.IntegerField(source='value', read_only=True)

    class Meta:
        model = Rating
        fields = ['id', 'value', 'user_rating', 'new_project_average']

    def validate(self, attrs):
        user = self.context['request'].user
        project = self.context['project']

        if project.owner == user:
            raise serializers.ValidationError("Owners cannot rate their own projects.")
        
        return attrs

    def create(self, validated_data):
        user = self.context['request'].user
        project:Project = self.context['project']
        
        rating, created = Rating.objects.update_or_create(
            user=user,
            project=project,
            defaults={'value': validated_data['value']},
        )

        project.refresh_from_db()
        rating.refresh_from_db()
        return rating

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

class ReportUpsertSerializer(serializers.ModelSerializer):
    class Meta:
        model = Report
        fields = ['id', 'reason', 'created_at']
        read_only_fields = ['id', 'created_at']

    def create(self, validated_data):
        user = self.context['request'].user
        target_project = self.context.get('project')
        target_comment = self.context.get('comment')

        if target_project:
            report, created = Report.objects.get_or_create(
                reporter=user,
                project=target_project,
                report_type='project',
                defaults={'reason': validated_data['reason']}
            )
        else:
            report, created = Report.objects.get_or_create(
                reporter=user,
                comment=target_comment,
                report_type='comment',
                defaults={'reason': validated_data['reason']}
            )
            
        return report

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
