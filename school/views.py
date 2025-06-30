import jwt
import datetime
from django.http import JsonResponse
from django.views import View
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from .models import AccUsers, VCceMarks
from rest_framework.generics import ListAPIView
from rest_framework.views import APIView
from .serializers import FastCceEntrySerializer
from django.db.models import Q
from rest_framework.pagination import PageNumberPagination
from .protection import token_required
from django.shortcuts import render
from django.utils.timezone import now
from .models import CCEEntry


# Secret key for JWT
JWT_SECRET = settings.JWT_SECRET
JWT_ALGORITHM = 'HS256'
JWT_EXP_DELTA_DAYS = 365

# HEALTH CHECK VIEW
class HealthCheckView(View):
    def get(self, request, *args, **kwargs):
        return JsonResponse({"status": "ok", "message": "School API is healthy"}, status=200)

# ROOT VIEW TO SHOW PAGES
def root_redirect_view(request):
    return render(request, 'school/login.html',  {'timestamp': now().timestamp()})

# LOGIN PAGE VIEW
def login_page(request):
    return render(request, 'school/login.html',  {'timestamp': now().timestamp()})

# MARK PAGE VIEW
def mark_view_page(request):
    return render(request, 'school/mark_view.html', {'timestamp': now().timestamp()})


@api_view(['POST'])
def login_view(request):
    user_id = request.data.get('id', '').strip()
    password = request.data.get('pass', '').strip()

    try:
        user = AccUsers.objects.get(id__iexact=user_id.strip())
        if user.pass_field.strip() == password:
            payload = {
                'user_id': user.id,
                'exp': datetime.datetime.utcnow() + datetime.timedelta(days=JWT_EXP_DELTA_DAYS),
                'iat': datetime.datetime.utcnow(),
            }
            token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

            return Response({
                'token': token,
                'user_id': user.id.strip()
            }, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Invalid password'}, status=status.HTTP_401_UNAUTHORIZED)
    except AccUsers.DoesNotExist:
        return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)


class FlexibleFilterPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'


class FilteredMarksView(ListAPIView):
    """Fast marks view - everything pre-joined in database"""
    serializer_class = FastCceEntrySerializer
    pagination_class = FlexibleFilterPagination

    @token_required
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        filters = Q()
        query_params = self.request.query_params

        filter_map = {
            'class_field': 'class_field',
            'division': 'division', 
            'subject': 'subject',
            'term': 'term',
            'part': 'part',
            'assessmentitem': 'assessmentitem',
            'admission': 'admission'
        }

        for param, field in filter_map.items():
            value = query_params.get(param)
            if value:
                filters &= Q(**{field: value})

        return VCceMarks.objects.filter(filters).order_by('student_name')


class MarkFilterMetadata(APIView):
    """Filter metadata with dependent student filter"""

    def get(self, request):
        marks_qs = VCceMarks.objects.all()

        # 🔥 Read query params
        class_field = request.query_params.get('class_field')
        division = request.query_params.get('division')

        # ✅ Filter ONLY the student queryset if class or division is selected
        student_qs = marks_qs
        if class_field:
            student_qs = student_qs.filter(class_field=class_field)
        if division:
            student_qs = student_qs.filter(division=division)

        # 📦 Subjects (Global)
        subjects_data = marks_qs.values('subject', 'subject_name').distinct().order_by('subject_name')
        subjects = [
            {'code': item['subject'], 'name': item['subject_name']}
            for item in subjects_data if item['subject'] and item['subject_name']
        ]

        # 📦 Assessment Items (Global)
        assessment_data = marks_qs.values('assessmentitem', 'assessmentitem_name').distinct().order_by('assessmentitem_name')
        assessment_items = [
            {'code': item['assessmentitem'], 'name': item['assessmentitem_name']}
            for item in assessment_data if item['assessmentitem'] and item['assessmentitem_name']
        ]

        # 📦 Students (Filtered by class & division if given)
        students_data = student_qs.values('admission', 'student_name').distinct().order_by('student_name')
        students = [
            {'admission': item['admission'], 'name': item['student_name']}
            for item in students_data if item['admission'] and item['student_name']
        ]

        # 📦 Other filters (Global)
        terms = sorted([term for term in marks_qs.values_list('term', flat=True).distinct() if term])
        divisions = sorted([div for div in marks_qs.values_list('division', flat=True).distinct() if div])
        parts = sorted([part for part in marks_qs.values_list('part', flat=True).distinct() if part])
        classes = sorted([cls for cls in marks_qs.values_list('class_field', flat=True).distinct() if cls])

        return Response({
            "subjects": subjects,
            "assessment_items": assessment_items,
            "students": students,   # ✅ Filtered students
            "terms": terms,
            "divisions": divisions,
            "parts": parts,
            "classes": classes,
        })

    
# UPDATE MARK VIEW
class UpdateMarkView(APIView):

    @token_required
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    def post(self, request):
        slno = request.data.get("slno")
        mark = request.data.get("mark")

        if slno is None or mark is None:
            return Response({"error": "Missing slno or mark"}, status=400)

        try:
            entry = CCEEntry.objects.get(slno=slno)
        except CCEEntry.DoesNotExist:
            return Response({"error": "Entry not found"}, status=404)

        try:
            mark = float(mark)
        except ValueError:
            return Response({"error": "Invalid mark format"}, status=400)

        if mark < 0 or (entry.maxmark is not None and mark > float(entry.maxmark)):
            return Response({"error": f"Mark must be between 0 and {entry.maxmark}"}, status=400)

        entry.mark = mark
        entry.last_updated = now() # ✅ Set timestamp manually
        entry.save(update_fields=["mark", "last_updated"])

        return Response({"message": "Mark updated successfully"})