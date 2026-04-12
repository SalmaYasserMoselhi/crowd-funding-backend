from django.urls import path

from .views import (
    CancelProjectView,
    CategoryListView,
    ProjectDetailView,
    ProjectListCreateView,
    TagAutocompleteView,
)

urlpatterns = [
    path('', ProjectListCreateView.as_view(), name='project-list-create'),
    path('<int:pk>/', ProjectDetailView.as_view(), name='project-detail'),
    path('<int:pk>/cancel/', CancelProjectView.as_view(), name='project-cancel'),
    path('tags/', TagAutocompleteView.as_view(), name='tag-autocomplete'),
    path('categories/', CategoryListView.as_view(), name='category-list'),
]
