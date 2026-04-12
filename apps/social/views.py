from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response

from core.permissions import IsOwnerOrReadOnly

from .models import Comment, Donation, Rating, Report
from .serializers import (
    CommentSerializer,
    DonationSerializer,
    RatingSerializer,
    ReportSerializer,
)


class DonationCreateView(generics.CreateAPIView):
    serializer_class = DonationSerializer
    permission_classes = [IsAuthenticated]


class CommentListCreateView(generics.ListCreateAPIView):
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        project_id = self.kwargs['project_id']
        return Comment.objects.filter(
            project_id=project_id, parent__isnull=True
        ).select_related('user').prefetch_related('replies__user')


class CommentDestroyView(generics.DestroyAPIView):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]


class RatingCreateView(generics.CreateAPIView):
    serializer_class = RatingSerializer
    permission_classes = [IsAuthenticated]


class ReportCreateView(generics.CreateAPIView):
    serializer_class = ReportSerializer
    permission_classes = [IsAuthenticated]
