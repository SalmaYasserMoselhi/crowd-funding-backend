from django.urls import path

from .views import CategoryListView, CategoryProjectsView, HomepageView, SearchView

urlpatterns = [
    path('homepage/', HomepageView.as_view(), name='homepage'),
    path('search/', SearchView.as_view(), name='search'),
    path('categories/', CategoryListView.as_view(), name='category-list'),
    path('categories/<slug:slug>/projects/', CategoryProjectsView.as_view(), name='category-projects'),
]
