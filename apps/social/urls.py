from django.urls import path

from .views import (
    CommentDestroyView,
    CommentListCreateView,
    DonationCreateView,
    RatingCreateView,
    ReportCreateView,
)

urlpatterns = [
    path('donations/', DonationCreateView.as_view(), name='donation-create'),
    path('projects/<int:project_id>/comments/', CommentListCreateView.as_view(), name='comment-list-create'),
    path('comments/<int:pk>/', CommentDestroyView.as_view(), name='comment-destroy'),
    path('ratings/', RatingCreateView.as_view(), name='rating-create'),
    path('reports/', ReportCreateView.as_view(), name='report-create'),
]
