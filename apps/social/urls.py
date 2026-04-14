from django.urls import path

from .views import (
    CommentDestroyView,
    CommentListCreateView,
    CommentReplyListCreateView,
    CommentReportView,
    DonationCreateView,
    ProjectDonateView,
    ProjectReportView,
    RatingCreateView,
    ReportCreateView,
    UserDonationHistoryView,
)

urlpatterns = [
    path('donations/', DonationCreateView.as_view(), name='donation-create'),
    path('projects/<int:project_id>/donate/', ProjectDonateView.as_view(), name='project-donate'),
    path('projects/<int:project_id>/comments/', CommentListCreateView.as_view(), name='comment-list-create'),
    path('users/me/donations/', UserDonationHistoryView.as_view(), name='user-donations'),
    path('comments/<int:pk>/', CommentDestroyView.as_view(), name='comment-destroy'),
	path('comments/<int:pk>/replies/', CommentReplyListCreateView.as_view(), name='comment-replies'),
    # path('ratings/', RatingCreateView.as_view(), name='rating-create'),
    path('projects/<int:project_id>/rate/', RatingCreateView.as_view(), name='project-rate'),
    # path('reports/', ReportCreateView.as_view(), name='report-create'),
    path('projects/<int:project_id>/report/', ProjectReportView.as_view(), name='project-report'),
    path('comments/<int:pk>/report/', CommentReportView.as_view(), name='comment-report'),
    
]
