from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (UserCreateView,UserListView,UserRUDView, ContactViewSet, SpamReportViewSet, SearchViewSet,populate_fake_data)

from rest_framework_simplejwt import views as jwt_views

router = DefaultRouter()
# router.register(r'users', UserViewSet,basename='users')
router.register(r'contacts', ContactViewSet, basename='contact')
router.register(r'spam-reports', SpamReportViewSet, basename='spam-report')
router.register(r'search', SearchViewSet, basename='search')

urlpatterns = [
    path('', include(router.urls)),
    path('user/register/', UserCreateView.as_view(), name='user_create'),
    path('login/', jwt_views.TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', jwt_views.TokenRefreshView.as_view(), name='token_refresh'),
    path('user/profile/', UserRUDView.as_view(), name='user_rud'),
    path('user/all/',UserListView.as_view(),name='user_list'),
    
    
    path('populate_fake_data/', populate_fake_data, name='populate_fake_data'),
]