from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView  # Corrigir a importação

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('agendamentos.urls')),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),  # Rota para obter o token
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),  # Rota para refresh do token
]
