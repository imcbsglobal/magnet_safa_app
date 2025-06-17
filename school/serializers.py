from rest_framework import serializers
from .models import AccUsers, VCceMarks


class AccUsersSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccUsers
        fields = '__all__'



class FastCceEntrySerializer(serializers.ModelSerializer):
    """This is all you need - simple and fast"""
    class Meta:
        model = VCceMarks
        fields = '__all__'