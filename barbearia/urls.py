from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

# Teste rápido para verificar se o backend está rodando
from django.http import JsonResponse
def health_check(request):
    return JsonResponse({"status": "ok"}, status=200)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('agendamentos.urls')),  # Garante que agendamentos está incluído corretamente
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),  # Endpoint para obter o token JWT
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),  # Endpoint para refresh do token JWT
    path('health/', health_check, name='health_check'),  # Rota para testar se o servidor está rodando
]
