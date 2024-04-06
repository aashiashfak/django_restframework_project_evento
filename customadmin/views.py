from .serializers import SuperuserLoginSerializer
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView


class SuperUserLoginView(APIView):
    def post(self, request):
        serializer = SuperuserLoginSerializer(data=request.data)
        if serializer.is_valid():
            return Response(serializer.validated_data, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

       

