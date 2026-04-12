from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, generics, status
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.views import APIView

from core.permissions import IsProjectOwnerOrReadOnly

from .filters import ProjectFilter
from .models import Category, Project, Tag
from .serializers import (
    CategorySerializer,
    ProjectCreateUpdateSerializer,
    ProjectDetailSerializer,
    ProjectListSerializer,
    TagSerializer,
)


class ProjectListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ProjectFilter
    search_fields = ['title', 'tags__name']
    ordering_fields = ['created_at', 'average_rating', 'current_donations']

    def get_queryset(self):
        qs = Project.objects.select_related('category', 'owner').prefetch_related('tags', 'media')
        creator = self.request.query_params.get('creator')
        if creator == 'me' and self.request.user.is_authenticated:
            qs = qs.filter(owner=self.request.user)
        return qs

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ProjectCreateUpdateSerializer
        return ProjectListSerializer

    def perform_create(self, serializer):
        serializer.save()


class ProjectDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Project.objects.select_related('category', 'owner').prefetch_related('tags', 'media')
    permission_classes = [IsProjectOwnerOrReadOnly]

    def get_serializer_class(self):
        if self.request.method in ('PUT', 'PATCH'):
            return ProjectCreateUpdateSerializer
        return ProjectDetailSerializer


class CancelProjectView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            project = Project.objects.get(pk=pk, owner=request.user)
        except Project.DoesNotExist:
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)

        if not project.can_be_cancelled():
            return Response(
                {'detail': 'Cannot cancel: donations have reached 25% or more of the target.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        project.status = 'cancelled'
        project.save(update_fields=['status'])
        return Response({'detail': 'Project cancelled.'}, status=status.HTTP_200_OK)


class TagAutocompleteView(generics.ListAPIView):
    serializer_class = TagSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        q = self.request.query_params.get('q', '')
        return Tag.objects.filter(name__icontains=q)[:20]


class CategoryListView(generics.ListAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
