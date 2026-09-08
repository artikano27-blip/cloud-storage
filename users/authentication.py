from rest_framework.authentication import SessionAuthentication


class CsrfExemptSessionAuthentication(SessionAuthentication):
    def enforce_csrf(self, request):
        return  # Пропускаем проверку CSRF-токена

    def authenticate_header(self, request):
        return 'Session'

class EnforcedSessionAuthentication(SessionAuthentication):

    def authenticate(self, request):
        # Принудительно требуем CSRF-токен ДО проверки пользователя
        self.enforce_csrf(request)
        return super().authenticate(request)