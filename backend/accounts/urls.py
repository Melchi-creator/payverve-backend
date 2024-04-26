from django.urls import path

from .views import (
    AuthCreateNewUserView,
    AuthLoginExisitingUserView, UserPasswordResetView, RetrieveUpdateDestroyExistingUser,
)

urlpatterns = [
    path('auth/sign-up/', AuthCreateNewUserView.as_view(), name='auth-create-user'),
    path('auth/sign-in/', AuthLoginExisitingUserView.as_view(), name='auth-login-user'),
    path('auth/reset-password/', UserPasswordResetView.as_view(), name='auth-reset-password'),
    path('auth/user/<int:pk>/', RetrieveUpdateDestroyExistingUser.as_view(), name='auth-login-user'),
]
