from django.urls import path

from .views import (
    CancelProjectView,
    CategoryListView,
    ProjectDetailView,
    ProjectImageUploadView,
    ProjectListCreateView,
    SimilarProjectsView,
    TagAutocompleteView,
    TagListView,
)

app_name = "projects"

urlpatterns = [
    path('', ProjectListCreateView.as_view(), name='project-list-create'),
    path('<int:pk>/', ProjectDetailView.as_view(), name='project-detail'),
    path('<int:pk>/cancel/', CancelProjectView.as_view(), name='project-cancel'),
    path('<int:pk>/similar/', SimilarProjectsView.as_view(), name='project-similar'),
    path('<int:pk>/images/', ProjectImageUploadView.as_view(), name='project-image-upload'),
    path('tags/', TagAutocompleteView.as_view(), name='tag-autocomplete'),
    path('tags/list/', TagListView.as_view(), name='tag-list'),
    path('categories/', CategoryListView.as_view(), name='category-list'),
]
