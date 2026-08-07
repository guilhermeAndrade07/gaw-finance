from django.urls import path
from . import views


urlpatterns = [
    path('goals/', views.MonthlyGoalListView.as_view(), name='goal_list'),
    path('goals/create/', views.MonthlyGoalCreateView.as_view(), name='goal_create'),
    path('goals/<int:pk>/update/', views.MonthlyGoalUpdateView.as_view(), name='goal_update'),
    path('goals/<int:pk>/delete/', views.MonthlyGoalDeleteView.as_view(), name='goal_delete'),
    path('goals/dashboard/', views.MonthlyGoalDashboardView.as_view(), name='goal_dashboard'),

    path('api/goal-progress/', views.get_goal_progress, name='get_goal_progress'),

    path('api/v1/goals/', views.MonthlyGoalCreateListAPIView.as_view(), name='goal-create-list-api-view'),
    path('api/v1/goals/<int:pk>/', views.MonthlyGoalRetrieveUpdateDestroyAPIView.as_view(), name='goal-detail-api-view'),
]
