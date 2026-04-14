from django.db.models import Q
from django.utils import timezone
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.projects.models import Category, Project
from .serializers import CategorySerializer, ProjectCardSerializer


def running_projects():
    """Projects that are active right now — not cancelled/completed, within date range."""
    now = timezone.now()
    return (
        Project.objects.filter(
            status='running',
            start_time__lte=now,
            end_time__gte=now,
        )
        .select_related('category')
        .prefetch_related('media', 'tags')
    )


class HomepageView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        qs = running_projects()
        ctx = {'request': request}

        return Response({
            'top5_rated': ProjectCardSerializer(
                qs.order_by('-average_rating')[:5], many=True, context=ctx
            ).data,
            'latest5': ProjectCardSerializer(
                qs.order_by('-created_at')[:5], many=True, context=ctx
            ).data,
            'featured5': ProjectCardSerializer(
                qs.filter(is_featured=True)[:5], many=True, context=ctx
            ).data,
            'categories': CategorySerializer(Category.objects.all(), many=True).data,
        })


class SearchView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        q = request.query_params.get('q', '').strip()
        if not q:
            return Response({'count': 0, 'results': []})

        qs = (
            Project.objects.filter(
                Q(title__icontains=q) | Q(tags__name__icontains=q)
            )
            .select_related('category')
            .prefetch_related('media', 'tags')
            .distinct()
        )

        ctx = {'request': request}
        return Response({
            'count': qs.count(),
            'results': ProjectCardSerializer(qs, many=True, context=ctx).data,
        })


class CategoryListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        categories = Category.objects.all()
        return Response(CategorySerializer(categories, many=True).data)


class CategoryProjectsView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, slug):
        try:
            category = Category.objects.get(slug=slug)
        except Category.DoesNotExist:
            return Response({'detail': 'Category not found.'}, status=404)

        qs = (
            Project.objects.filter(category=category)
            .select_related('category')
            .prefetch_related('media', 'tags')
            .order_by('-created_at')
        )

        ctx = {'request': request}
        return Response({
            'category': CategorySerializer(category).data,
            'projects': ProjectCardSerializer(qs, many=True, context=ctx).data,
        })
