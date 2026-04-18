from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from django.db.models import Prefetch

from rest_framework import filters, generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from core.pagination import StandardResultsPagination
from core.permissions import IsProjectOwnerOrReadOnly

from .filters import ProjectFilter
from .models import Category, Project, ProjectMedia, Tag
from apps.social.models import Rating
from .serializers import (
    CategorySerializer,
    ProjectCreateUpdateSerializer,
    ProjectDetailSerializer,
    ProjectListSerializer,
    ProjectMediaSerializer,
    TagSerializer,
)

    
class ProjectListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = StandardResultsPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ProjectFilter
    search_fields = ['title', 'tags__name']
    ordering_fields = ['created_at', 'average_rating', 'current_donations', 'total_target']

    def get_queryset(self):
        return Project.objects.select_related('category', 'owner').prefetch_related('tags', 'media')

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ProjectCreateUpdateSerializer
        return ProjectListSerializer

    def perform_create(self, serializer):
        serializer.save()

class ProjectDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsProjectOwnerOrReadOnly]

    def get_queryset(self):
        queryset = Project.objects.select_related('category', 'owner').prefetch_related('tags', 'media')
        
        user = self.request.user
        if user.is_authenticated:
            return queryset.prefetch_related(
                Prefetch(
                    'ratings',
                    queryset=Rating.objects.filter(user=user),
                    to_attr='user_specific_rating'
                )
            )
        return queryset

    def get_serializer_class(self):
        if self.request.method in ('PUT', 'PATCH'):
            return ProjectCreateUpdateSerializer
        return ProjectDetailSerializer

class CancelProjectView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            project = Project.objects.get(pk=pk)
        except Project.DoesNotExist:
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)

        if project.owner != request.user:
            return Response({'detail': 'Forbidden.'}, status=status.HTTP_403_FORBIDDEN)

        if project.is_cancelled:
            return Response({'detail': 'Project is already cancelled.'}, status=status.HTTP_400_BAD_REQUEST)

        if not project.can_be_cancelled():
            return Response(
                {'detail': 'Cannot cancel: donations have reached 25% or more of the target.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        project.status = 'cancelled'
        project.is_cancelled = True
        project.save(update_fields=['status', 'is_cancelled'])
        return Response({'detail': 'Project cancelled.'}, status=status.HTTP_200_OK)

class TagAutocompleteView(generics.ListAPIView):
    serializer_class = TagSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        q = self.request.query_params.get('q', '')
        return Tag.objects.filter(name__icontains=q)[:20]

class TagListView(generics.ListAPIView):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [AllowAny]

class CategoryListView(generics.ListAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]
    pagination_class = None

class ProjectImageUploadView(APIView):
    """
    POST /projects/{id}/images/
    Accepts multipart form with key `images` (list of files).
    Only the project owner can upload images.
    """
    
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, pk):
        try:
            project = Project.objects.get(pk=pk, owner=request.user)
        except Project.DoesNotExist:
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)

        images = request.FILES.getlist('images')
        if not images:
            return Response({'detail': 'No images uploaded.'}, status=status.HTTP_400_BAD_REQUEST)

        media_objects = []
        start_order = project.media.count()
        has_cover = project.media.filter(is_cover=True).exists()
        for img in images:
            media = ProjectMedia(
                project=project,
                image=img,
                order=start_order,
                is_cover=(not has_cover and start_order == 0),
            )
            media.save()
            media_objects.append(media)
            start_order += 1

        serializer = ProjectMediaSerializer(media_objects, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class SimilarProjectsView(generics.ListAPIView):
    serializer_class = ProjectListSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        project = get_object_or_404(Project, pk=self.kwargs.get('pk'))
        return project.get_similar_projects()

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)