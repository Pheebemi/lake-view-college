from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path, include, reverse_lazy
from django.conf import settings
from django.conf.urls.static import static
from accounts import views as acc_views
from accounts import exam_officer_views, app_manager_views

urlpatterns = [
    # Short login URLs (no prefix)
    path('login/', acc_views.student_login, name='student_login'),
    path('staff/', acc_views.staff_login, name='staff_login'),
    path('exam/', exam_officer_views.exam_officer_login, name='exam_officer_login'),
    path('manager/', app_manager_views.app_manager_login, name='app_manager_login'),

    # Forgot password (shared across every login type -- one User table)
    path('forgot-password/', auth_views.PasswordResetView.as_view(
        template_name='accounts/password_reset_form.html',
        email_template_name='accounts/password_reset_email.html',
        subject_template_name='accounts/password_reset_subject.txt',
        success_url=reverse_lazy('password_reset_done'),
    ), name='password_reset'),
    path('forgot-password/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='accounts/password_reset_done.html',
    ), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='accounts/password_reset_confirm.html',
        success_url=reverse_lazy('password_reset_complete'),
    ), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(
        template_name='accounts/password_reset_complete.html',
    ), name='password_reset_complete'),

    path('api/accounts/', include('accounts.api_urls', namespace='accounts_api')),
    path('accounts/', include('accounts.urls', namespace='accounts')),
    path('dashboard/', include('dashboard.urls', namespace='dashboard')),
    path("", include('core.urls', namespace='core')),
    # path("__reload__/", include("django_browser_reload.urls")),
    path('admin/', admin.site.urls),
]

# Serve static and media when web server (cPanel) doesn't have a place to configure them
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
else:
    # Production: Django serves static/media if cPanel Setup Python App has no static path
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)