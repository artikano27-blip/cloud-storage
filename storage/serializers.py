
from rest_framework import serializers

class ResourceSerializer(serializers.Serializer):
    path = serializers.CharField()
    name = serializers.CharField()
    size = serializers.IntegerField(required= False, allow_null= True)
    type = serializers.CharField()

