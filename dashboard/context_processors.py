from .models import Notification

def notifications_processor(request):
    """
    Context processor to make notifications available globally
    """
    if request.user.is_authenticated:
        notifications = Notification.objects.filter(user=request.user, is_read=False)
        return {'notifications': notifications}
    return {'notifications': []} 