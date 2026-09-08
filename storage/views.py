from functools import cached_property

from django.http.response import FileResponse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from storage.exceptions import InvalidPathError, FileNotExistsError
from storage.serializers import ResourceSerializer
from users.exceptions import IsAuthenticatedCustom
from storage.services import (
    S3DirectoryService,
    S3DownloadService,
    S3MutationService,
    S3SearchService,
    S3UploadService,
)
from storage.validators import is_valid_path

class BaseStorageView(APIView):
    permission_classes = [IsAuthenticatedCustom]

    @cached_property
    def directory_service(self) -> S3DirectoryService:
        return S3DirectoryService()

    @cached_property
    def upload_service(self) -> S3UploadService:
        return S3UploadService()

    @cached_property
    def mutation_service(self) -> S3MutationService:
        return S3MutationService()

    @cached_property
    def download_service(self) -> S3DownloadService:
        return S3DownloadService()

    @cached_property
    def search_service(self) -> S3SearchService:
        return S3SearchService()

    @staticmethod
    def get_requested_path(
            request,
            param_name: str = "path",
            allow_empty: bool = False,
            error_message: str = "Недопустимый или пустой путь к ресурсу",
    ) -> str:
        raw_path = request.data.get(param_name) if hasattr(request, "data") else ""
        if not raw_path:
            raw_path = request.query_params.get(param_name, "")

        path = str(raw_path or "").strip()

        if not is_valid_path(path, allow_empty=allow_empty):
            raise InvalidPathError(detail={"message": error_message})
        return path

class ResourceView(BaseStorageView):

    def get(self, request):
        path = self.get_requested_path(request, allow_empty=False)
        data = self.directory_service.get_resource_info(user_id=request.user.id, path= path)
        is_many = isinstance(data, list)
        serializer = ResourceSerializer(data, many=is_many)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):

        path = self.get_requested_path(request, allow_empty=True)
        files = request.FILES.getlist("object") or request.FILES.getlist("file")
        if not files:
            raise FileNotExistsError(detail={"message": "Не удалось найти файл"})
        paths = request.data.getlist("paths")

        if paths and len(paths) == len(files):
            for file, rel_path in zip(files, paths):
                file._name = rel_path

        data = self.upload_service.upload_resource(user_id=request.user.id, path=path, files=files)
        is_many = isinstance(data, list)
        serializer = ResourceSerializer(data, many=is_many)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self,request):
        path = self.get_requested_path(request, allow_empty=False)
        self.mutation_service.delete_resource(user_id=request.user.id, path=path)
        return Response(status= status.HTTP_204_NO_CONTENT)

class ResourceDownloadView(BaseStorageView):

    def get(self, request):
        path = self.get_requested_path(request, allow_empty=False)

        stream, filename = self.download_service.download_resource(
            user_id=request.user.id, path=path
        )
        return FileResponse(
            stream,
            filename=filename,
            content_type="application/octet-stream",
            as_attachment=True,
        )

class ResourceRenameMoveView(BaseStorageView):

    def post(self,request):
        source_key = self.get_requested_path(request, param_name="from", allow_empty=False)
        target_key = self.get_requested_path(request, param_name="to", allow_empty=False)

        response = self.mutation_service.move_resource(user_id=request.user.id, source_key=source_key, target_key=target_key)
        is_many = isinstance(response, list)
        serializer = ResourceSerializer(response, many=is_many)
        return Response(serializer.data, status=status.HTTP_200_OK)

class ResourceSearchView(BaseStorageView):

    def get(self, request):
        query = self.get_requested_path(request, param_name="query", allow_empty=False, error_message= "Невалидный или отсутствующий поисковый запрос")

        data = self.search_service.search_resource(user_id = request.user.id, query = query)

        serializer = ResourceSerializer(data, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class DirectoryView(BaseStorageView):

    def get(self,request):
        path = self.get_requested_path(request, allow_empty=True)
        data = self.directory_service.get_folder_resources(user_id=request.user.id, path=path)
        serializer = ResourceSerializer(data, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        path = self.get_requested_path(request, allow_empty=False)
        data = self.upload_service.create_null_folder(user_id = request.user.id, path = path)
        serializer = ResourceSerializer(data, many = False)
        return Response(serializer.data, status = status.HTTP_201_CREATED)