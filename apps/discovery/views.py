from django.utils import timezone
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.projects.models import Category, Project
from apps.projects.serializers import CategorySerializer, ProjectListSerializer


class HomepageView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        now = timezone.now()
        running_qs = Project.objects.filter(
            status='running',
            start_time__lte=now,
            end_time__gte=now,
        ).prefetch_related('media', 'tags').select_related('category')

        top_rated = running_qs.order_by('-average_rating')[:5]
        latest = running_qs.order_by('-created_at')[:5]
        featured = running_qs.filter(is_featured=True)[:5]
        categories = Category.objects.all()

        ctx = {'request': request}
        return Response({
            'top_rated': ProjectListSerializer(top_rated, many=True, context=ctx).data,
            'latest': ProjectListSerializer(latest, many=True, context=ctx).data,
            'featured': ProjectListSerializer(featured, many=True, context=ctx).data,
            'categories': CategorySerializer(categories, many=True).data,
        })
