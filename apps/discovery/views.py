from django.db.models import Q, Prefetch
from django.utils import timezone
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.projects.models import Category, Project, ProjectMedia
from core.pagination import StandardResultsPagination
from .serializers import CategorySerializer, ProjectCardSerializer


CARD_FIELDS = (
    'id', 'title', 'total_target', 'current_donations',
    'average_rating', 'category__name',
)

MEDIA_PREFETCH = Prefetch(
    'media',
    queryset=ProjectMedia.objects.order_by('-is_cover', 'order', '-created_at'),
)

def _base_qs():
    return (
        Project.objects
        .select_related('category')
        .prefetch_related(MEDIA_PREFETCH)
        .only(*CARD_FIELDS)
    )

def running_projects():
    now = timezone.now()
    return _base_qs().filter(
        status='running',
        is_cancelled=False,
        start_time__lte=now,
        end_time__gte=now,
    )


class HomepageView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        running_qs = running_projects()
        ctx = {'request': request}

        top5_rated = list(running_qs.order_by('-average_rating')[:5])
        latest5 = list(_base_qs().filter(is_cancelled=False).order_by('-created_at')[:5])
        featured5 = list(running_qs.filter(is_featured=True).order_by('-created_at')[:5])
        categories = Category.objects.all()

        return Response({
            'top5_rated': ProjectCardSerializer(top5_rated, many=True, context=ctx).data,
            'latest5': ProjectCardSerializer(latest5, many=True, context=ctx).data,
            'featured5': ProjectCardSerializer(featured5, many=True, context=ctx).data,
            'categories': CategorySerializer(categories, many=True).data,
        })


class SearchView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        q = request.query_params.get('q', '').strip()
        if not q:
            return Response({'count': 0, 'next': None, 'previous': None, 'results': []})

        qs = (
            _base_qs()
            .filter(Q(title__icontains=q) | Q(tags__name__icontains=q))
            .distinct()
            .order_by('-created_at')
        )

        paginator = StandardResultsPagination()
        page = paginator.paginate_queryset(qs, request)
        data = ProjectCardSerializer(page, many=True, context={'request': request}).data
        return paginator.get_paginated_response(data)


class CategoryListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        return Response(
            CategorySerializer(Category.objects.all(), many=True).data
        )


class CategoryProjectsView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, slug):
        try:
            category = Category.objects.get(slug=slug)
        except Category.DoesNotExist:
            return Response({'error': 'Category not found.'}, status=404)

        qs = _base_qs().filter(category=category, is_cancelled=False).order_by('-created_at')

        paginator = StandardResultsPagination()
        page = paginator.paginate_queryset(qs, request)
        data = ProjectCardSerializer(page, many=True, context={'request': request}).data
        return paginator.get_paginated_response(data)
