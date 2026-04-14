from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from apps.projects.models import Project
from core.permissions import IsOwnerOrReadOnly

from .models import Comment, Donation, Rating, Report
from .serializers import (
    CommentReplySerializer,
    CommentSerializer,
    DonationSerializer,
    DonationResponseSerializer,
    RatingSerializer,
    RatingUpsertSerializer,
    ReportSerializer,
    ReportUpsertSerializer,
    UserDonationHistorySerializer,
)

class ProjectDonateView(generics.CreateAPIView):
    serializer_class = DonationSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        project = get_object_or_404(Project, pk=self.kwargs.get('project_id'))
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        donation = serializer.save(
            user=self.request.user,
            project=project
        )
        
        response_serializer = DonationResponseSerializer(donation)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

class DonationCreateView(generics.CreateAPIView):
    serializer_class = DonationSerializer
    permission_classes = [IsAuthenticated]


class UserDonationHistoryView(generics.ListAPIView):
    serializer_class = UserDonationHistorySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Donation.objects.filter(
            user=self.request.user
        ).select_related('project').order_by('-created_at')


class CommentListCreateView(generics.ListCreateAPIView):
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['project'] = get_object_or_404(Project, pk=self.kwargs.get('project_id'))
        return context

    def get_queryset(self):
        project_id = self.kwargs['project_id']
        return Comment.objects.filter(
            project_id=project_id, parent__isnull=True
        ).select_related('user').prefetch_related('replies__user')


class CommentReplyListCreateView(generics.ListCreateAPIView):
    serializer_class = CommentReplySerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        return Comment.objects.filter(
            parent_id=self.kwargs.get('pk')
        ).select_related('user').order_by('created_at')

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['parent_comment'] = get_object_or_404(Comment, pk=self.kwargs.get('pk'))
        return context


class CommentDestroyView(generics.DestroyAPIView):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]


class RatingCreateView(generics.CreateAPIView):
    serializer_class = RatingUpsertSerializer
    permission_classes = [IsAuthenticated]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['project'] = get_object_or_404(Project, pk=self.kwargs.get('project_id'))
        return context

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        return response

class ReportCreateView(generics.CreateAPIView):
    serializer_class = ReportSerializer
    permission_classes = [IsAuthenticated]

class ProjectReportView(generics.CreateAPIView):
    serializer_class = ReportUpsertSerializer
    permission_classes = [IsAuthenticated]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['project'] = get_object_or_404(Project, pk=self.kwargs.get('project_id'))
        return context

class CommentReportView(generics.CreateAPIView):
    serializer_class = ReportUpsertSerializer
    permission_classes = [IsAuthenticated]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['comment'] = get_object_or_404(Comment, pk=self.kwargs.get('pk'))
        return context