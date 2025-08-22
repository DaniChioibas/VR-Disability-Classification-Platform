from django.urls import path
from django.contrib.auth import views as auth_views
from .views import register_view, logout_view, dashboard_view
from . import views, api

urlpatterns = [
    path('', views.classifier_view, name='index'),
    path('documentation/', views.documentation_view, name='documentation'),
    path('explore-more/', views.explore_more_view, name='explore_more'),
    path('batch-analysis/', views.batch_analysis_view, name='batch_analysis'),  
    path('api/set-explore-session/', views.set_explore_session_api, name='set_explore_session_api'),  
    path('advanced-classification/', views.advanced_classification_view, name='advanced_classification'),
    path('api/predict/', api.predict_api, name='predict_api'),
    path('api/predict-extra/', api.predict_extra_api, name='predict_extra_api'),
    path('download-script/', views.download_script_view, name='download_script'),
    path('login/', auth_views.LoginView.as_view(template_name='classifier/login.html'), name='login'),
    path('logout/', logout_view, name='logout'),
    path('register/', register_view, name='register'),
    path('batch-explore/', views.batch_explore_view, name='batch_explore'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('sessions/new/', views.session_create_view, name='session_create'),
    path('sessions/<int:session_id>/', views.session_detail_view, name='session_detail'),
    path('sessions/<int:session_id>/delete/', views.session_delete_view, name='session_delete'),
    path('history/<int:history_id>/explore/', views.history_explore_view, name='history_explore'),
]
