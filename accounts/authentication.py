from django.contrib.auth.backends import BaseBackend
from django.contrib.auth import get_user_model

User = get_user_model()

class MatriculationNumberAuthBackend(BaseBackend):
    """
    Custom authentication backend that allows students to log in 
    using their matriculation number and password.
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            # Attempt to fetch a user by matriculation number
            user = User.objects.get(matriculation_number=username)
            if user.check_password(password) and user.user_type == 'student':
                return user
        except User.DoesNotExist:
            return None
        return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None