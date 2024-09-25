from rest_framework import viewsets, permissions, status,generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.db.models import Count, Q
from .models import User, Contact, SpamReport
from .serializers import UserSerializer, ContactSerializer, SpamReportSerializer, SearchResultSerializer, DetailedSearchResultSerializer
from .utils import calculate_spam_likelihood,IsAdminOrSelf,custom_ratelimit
from rest_framework_simplejwt.tokens import RefreshToken
from faker import Faker
import random
from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
fake = Faker()
from decouple import config

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class UserCreateView(generics.CreateAPIView):
        
        
    permission_classes = [permissions.AllowAny]
    serializer_class = UserSerializer

    @custom_ratelimit(rate='5/m')
    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            user.set_password(request.data.get('password'))
            user.save()
            refresh = RefreshToken.for_user(user)
            return Response({
                'user': serializer.data,
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserRUDView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrSelf]

    # need to save the response in cache also 
    
    @custom_ratelimit(rate='10/m')
    def get_object(self):
        return self.request.user

    @custom_ratelimit(rate='5/m')
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        if getattr(instance, '_prefetched_objects_cache', None):
            instance._prefetched_objects_cache = {}

        return Response(serializer.data)

    @custom_ratelimit(rate='5/m')
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)
    
class UserListView(generics.ListAPIView):
    queryset=User.objects.all().order_by('-date_joined')
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination
  
class ContactViewSet(viewsets.ModelViewSet):
    serializer_class = ContactSerializer
    # permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        return Contact.objects.filter(user=self.request.user)

    @custom_ratelimit(rate='50/m')
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class SpamReportViewSet(viewsets.ModelViewSet):
    serializer_class = SpamReportSerializer
    # permission_classes = [permissions.IsAuthenticated]
    permission_classes = [permissions.AllowAny]
    

    def get_queryset(self):
        return SpamReport.objects.filter(reporter=self.request.user)

    @custom_ratelimit(rate='10/m')
    def perform_create(self, serializer):
        serializer.save(reporter=self.request.user)

class SearchViewSet(viewsets.ViewSet):
    permission_classes = [permissions.AllowAny]
    pagination_class = StandardResultsSetPagination

    def paginate_queryset(self, queryset):
        if self.paginator is None:
            return None
        return self.paginator.paginate_queryset(queryset, self.request, view=self)


    def get_paginated_response(self, data):
        assert self.paginator is not None
        return self.paginator.get_paginated_response(data)

    @property
    def paginator(self):
        if not hasattr(self, '_paginator'):
            if self.pagination_class is None:
                self._paginator = None
            else:
                self._paginator = self.pagination_class()
        return self._paginator

    @custom_ratelimit(rate='50/m')
    @action(detail=False, methods=['get'])
    def by_name(self, request):
        name = request.query_params.get('name', '')
        if not name:
            return Response({"error": "Name parameter is required"}, status=status.HTTP_400_BAD_REQUEST)

        users = User.objects.filter(Q(name__istartswith=name) | Q(name__icontains=name))
        contacts = Contact.objects.filter(Q(name__istartswith=name) | Q(name__icontains=name))
        
        results = []
        for user in users:
            spam_likelihood = calculate_spam_likelihood(user.phone_number)
            results.append({
                'name': user.name,
                'phone_number': user.phone_number,
                'spam_likelihood': spam_likelihood
            })
        # its getting loaded full data here instead of only limited because, have to improve the code quality 
        for contact in contacts:
            if contact.phone_number not in [r['phone_number'] for r in results]:
                spam_likelihood = calculate_spam_likelihood(contact.phone_number)
                results.append({
                    'name': contact.name,
                    'phone_number': contact.phone_number,
                    'spam_likelihood': spam_likelihood
                })

        # Sort results to prioritize names starting with the search query
        results.sort(key=lambda x: (not x['name'].lower().startswith(name.lower()), x['name']))
        # print(results,len(results))
        page = self.paginate_queryset(results)
        if page is not None:
            serializer = SearchResultSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = SearchResultSerializer(results, many=True)
        return Response(serializer.data)

    @custom_ratelimit(rate='50/m')
    @action(detail=False, methods=['get'])
    def by_phone(self, request):
        phone_number = request.query_params.get('phone_number', '')
         # phone_number = '+'+phone_number #- also could be | its better if from FE write + as p and minus as m then here i will replace p--> + and m---> - then search OR SEARCH AS CONTAINS OR NOT..
 
        if not phone_number:
            return Response({"error": "Phone number parameter is required"}, status=status.HTTP_400_BAD_REQUEST)

        if phone_number[0] == 'm':
           phone_number = phone_number.replace('m','-')
        elif phone_number[0]=='p':
            phone_number = phone_number.replace('p','+')
        else:
            phone_number = phone_number.replace(' ','+')
            
        if not phone_number:
            return Response({"error": "Phone number parameter is required"}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.filter(phone_number=phone_number).first()
        if user:
            spam_likelihood = calculate_spam_likelihood(user.phone_number)
            result = [{
                'name': user.name,
                'phone_number': user.phone_number,
                'spam_likelihood': spam_likelihood
            }]
        else:
            contacts = Contact.objects.filter(phone_number=phone_number)
            result = []
            for contact in contacts:
                spam_likelihood = calculate_spam_likelihood(contact.phone_number)
                result.append({
                    'name': contact.name,
                    'phone_number': contact.phone_number,
                    'spam_likelihood': spam_likelihood
                })

        serializer = SearchResultSerializer(result, many=True)
        return Response(serializer.data)

    @custom_ratelimit(rate='50/m')
    @action(detail=True, methods=['get'])
    def details(self, request, pk=None):
        try:
            user = User.objects.get(phone_number=pk)
        except User.DoesNotExist:
            user = None

        if user:
            result = {
                'name': user.name,
                'phone_number': user.phone_number,
                'spam_likelihood': calculate_spam_likelihood(user.phone_number),
            }
            
            # Check if the requesting user is in the contact list of the found user
            requesting_user = request.user if request.user.is_authenticated else None
            if requesting_user and Contact.objects.filter(user=user, phone_number=requesting_user.phone_number).exists():
                result['email'] = user.email
        else:
            contacts = Contact.objects.filter(phone_number=pk)
            if not contacts:
                return Response({"error": "No results found"}, status=status.HTTP_404_NOT_FOUND)
            
            result = {
                'name': contacts[0].name,  
                'phone_number': pk,
                'spam_likelihood': calculate_spam_likelihood(pk),
                'other_names': [contact.name for contact in contacts[1:]]  # List other names if any
            }

        serializer = DetailedSearchResultSerializer(result)
        return Response(serializer.data)


@api_view(['GET'])
@custom_ratelimit(rate='1/m')
@permission_classes([permissions.IsAdminUser])
def populate_fake_data(request):
    num_users = 50
    num_contacts_per_user = 15
    num_spam_reports = 25

    # Create Users
    new_users = []
    for _ in range(num_users):
        name = fake.name()
        phone_number = f'+91{fake.msisdn()[3:]}'
        email = fake.email()
        user = User.objects.create_user(name=name, phone_number=phone_number, email=email, password='password')
        new_users.append(user)

    # Create Contacts
    contacts_to_create = []

    # 5 contacts with same number but different names (3 sets)
    for _ in range(3):
        shared_number = f'+91{fake.msisdn()[3:]}'
        for _ in range(5):
            user = random.choice(new_users)
            contacts_to_create.append(Contact(user=user, name=fake.name(), phone_number=shared_number))
    
    # 5 contacts with same number but different names (2 sets)
    for _ in range(2):
        user = random.choice(new_users)
        random_user = random.choice(new_users)
        for _ in range(5):
            contacts_to_create.append(Contact(user=user, name=fake.name(), phone_number=random_user.phone_number))
    
    
    # 2 random contacts
    
    same_user = random.choice(new_users)
    for _ in range(3):
        user = random.choice(new_users)
        contacts_to_create.append(Contact(user=user, name=same_user.name, phone_number=f'+91{fake.msisdn()[3:]}'))
        

    Contact.objects.bulk_create(contacts_to_create)

    # Create Spam Reports
    spam_reports_to_create = []
    
    # 1 same number (from users) reported by 5 different users
    reported_user = random.choice(new_users)
    for reporter in random.sample(new_users, 5):
        spam_reports_to_create.append(SpamReport(reporter=reporter, phone_number=reported_user.phone_number))
    
    # 5 different numbers (from users) reported once
    for reported_user in random.sample(new_users, 5):
        reporter = random.choice(new_users)
        spam_reports_to_create.append(SpamReport(reporter=reporter, phone_number=reported_user.phone_number))
    
    # 5 different numbers from contacts, each reported 3 times
    # all_contacts = list(Contact.objects.all())
    if len(contacts_to_create) >= 5:
        reported_contacts = random.sample(contacts_to_create, 5)
        for contact in reported_contacts:
            for _ in range(3):
                reporter = random.choice(new_users)
                spam_reports_to_create.append(SpamReport(reporter=reporter, phone_number=contact.phone_number))

    SpamReport.objects.bulk_create(spam_reports_to_create, ignore_conflicts=True)

    return JsonResponse({
        "message": "Fake data population completed",
        "users_created": num_users,
        "contacts_created": len(contacts_to_create),
        "spam_reports_created": len(spam_reports_to_create)
    })