from rest_framework import serializers
from .models import AccUsers, Personel, MagSubject, CceAssessmentItems, CceEntry


class AccUsersSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccUsers
        fields = '__all__'


class PersonelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Personel
        fields = '__all__'


class MagSubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = MagSubject
        fields = '__all__'


class CceAssessmentItemsSerializer(serializers.ModelSerializer):
    class Meta:
        model = CceAssessmentItems
        fields = '__all__'


class CceEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = CceEntry
        fields = '__all__'
