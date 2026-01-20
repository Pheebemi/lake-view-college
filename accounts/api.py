from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User as DjangoUser
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from .models import (
    User, Faculty, Department, Course, StudentProfile,
    StaffProfile, CourseRegistration, PaymentTransaction
)
from .serializers import (
    UserSerializer, FacultySerializer, DepartmentSerializer,
    CourseSerializer, StudentProfileSerializer, StaffProfileSerializer,
    CourseRegistrationSerializer, PaymentTransactionSerializer,
    LoginSerializer
)


class LoginView(APIView):
    """API view for user login"""
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            username = serializer.validated_data['username']
            password = serializer.validated_data['password']

            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)
                token, created = Token.objects.get_or_create(user=user)
                return Response({
                    'token': token.key,
                    'user': UserSerializer(user).data,
                    'message': 'Login successful'
                })
            return Response(
                {'error': 'Invalid credentials'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):
    """API view for user logout"""

    def post(self, request):
        logout(request)
        return Response({'message': 'Logout successful'})


class UserProfileView(APIView):
    """API view for getting current user profile"""

    def get(self, request):
        user = request.user
        serializer = UserSerializer(user)
        return Response(serializer.data)


class StudentProfileView(APIView):
    """API view for student profile"""

    def get(self, request):
        try:
            student_profile = request.user.studentprofile
            serializer = StudentProfileSerializer(student_profile)
            return Response(serializer.data)
        except StudentProfile.DoesNotExist:
            return Response(
                {'error': 'Student profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )


class StaffProfileView(APIView):
    """API view for staff profile"""

    def get(self, request):
        try:
            staff_profile = request.user.staffprofile
            serializer = StaffProfileSerializer(staff_profile)
            return Response(serializer.data)
        except StaffProfile.DoesNotExist:
            return Response(
                {'error': 'Staff profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )


class FacultyListView(generics.ListAPIView):
    """API view for listing all faculties"""
    queryset = Faculty.objects.all()
    serializer_class = FacultySerializer
    permission_classes = [permissions.AllowAny]


class DepartmentListView(generics.ListAPIView):
    """API view for listing all departments"""
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = [permissions.AllowAny]


class CourseListView(generics.ListAPIView):
    """API view for listing courses"""
    queryset = Course.objects.filter(is_active=True)
    serializer_class = CourseSerializer
    permission_classes = [permissions.AllowAny]


class StudentCoursesView(APIView):
    """API view for student's registered courses"""

    def get(self, request):
        try:
            student_profile = request.user.studentprofile
            registrations = CourseRegistration.objects.filter(
                student=student_profile,
                status='registered'
            ).select_related('course')
            courses = [reg.course for reg in registrations]
            serializer = CourseSerializer(courses, many=True)
            return Response(serializer.data)
        except StudentProfile.DoesNotExist:
            return Response(
                {'error': 'Student profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )


class CourseRegistrationView(APIView):
    """API view for course registration"""

    def post(self, request):
        try:
            student_profile = request.user.studentprofile
            course_id = request.data.get('course_id')

            if not course_id:
                return Response(
                    {'error': 'Course ID is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            course = Course.objects.get(id=course_id, is_active=True)

            # Check if already registered
            existing_registration = CourseRegistration.objects.filter(
                student=student_profile,
                course=course
            ).first()

            if existing_registration:
                return Response(
                    {'error': 'Already registered for this course'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Create registration
            registration = CourseRegistration.objects.create(
                student=student_profile,
                course=course
            )

            serializer = CourseRegistrationSerializer(registration)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except Course.DoesNotExist:
            return Response(
                {'error': 'Course not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except StudentProfile.DoesNotExist:
            return Response(
                {'error': 'Student profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )


class PaymentHistoryView(APIView):
    """API view for student's payment history"""

    def get(self, request):
        try:
            student_profile = request.user.studentprofile
            payments = PaymentTransaction.objects.filter(
                student=student_profile
            ).order_by('-payment_date')
            serializer = PaymentTransactionSerializer(payments, many=True)
            return Response(serializer.data)
        except StudentProfile.DoesNotExist:
            return Response(
                {'error': 'Student profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def dashboard_stats(request):
    """API endpoint for dashboard statistics"""
    user = request.user

    if user.user_type == 'student':
        try:
            student_profile = user.studentprofile
            registered_courses = CourseRegistration.objects.filter(
                student=student_profile,
                status='registered'
            ).count()

            total_payments = PaymentTransaction.objects.filter(
                student=student_profile,
                status='success'
            ).count()

            return Response({
                'user_type': 'student',
                'registered_courses': registered_courses,
                'total_payments': total_payments,
                'cgpa': float(student_profile.cgpa)
            })
        except StudentProfile.DoesNotExist:
            return Response({'error': 'Student profile not found'})

    elif user.user_type == 'staff':
        try:
            staff_profile = user.staffprofile
            department_students = User.objects.filter(
                user_type='student',
                studentprofile__department=staff_profile.department
            ).count()

            return Response({
                'user_type': 'staff',
                'department_students': department_students,
                'is_head_of_department': staff_profile.is_head_of_department
            })
        except StaffProfile.DoesNotExist:
            return Response({'error': 'Staff profile not found'})

    return Response({'user_type': user.user_type})