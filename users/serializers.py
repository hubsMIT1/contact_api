from rest_framework import serializers
from .models import User, Contact, SpamReport

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'name', 'phone_number', 'email']
        extra_kwargs = {'email': {'required': False}}

class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = ['id', 'name', 'phone_number', 'email']

class SpamReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = SpamReport
        fields = ['id', 'phone_number']

class SearchResultSerializer(serializers.Serializer):
    name = serializers.CharField()
    phone_number = serializers.CharField()
    spam_likelihood = serializers.FloatField()
  
class DetailedSearchResultSerializer(SearchResultSerializer):
    email = serializers.EmailField(allow_null=True)