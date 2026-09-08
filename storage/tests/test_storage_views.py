
import pytest
from botocore.exceptions import ClientError

from django.urls import reverse
from rest_framework import status

from storage.utils import build_s3_key

@pytest.mark.django_db
class TestDirectoryAPI:
    def test_get_folder_resource_success(self, authenticated_client, create_s3_file):
        create_s3_file("123.png")
        create_s3_file("zapret2-master/")

        url = reverse("directory")
        response = authenticated_client.get(url, {"path": ""})

        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list)
        assert len(response.data) == 2

        items = {item["name"]: item for item in response.data}
        assert "123.png" in items
        assert items["123.png"]["type"] == "FILE"
        assert items["123.png"]["path"] == ""

        assert "zapret2-master" in items
        assert items["zapret2-master"]["type"] == "DIRECTORY"
        assert items["zapret2-master"]["path"] == ""

    def test_folder_create_success_201(self, authenticated_client, s3_client, bucket_name, created_user):
        url = reverse("directory")
        response = authenticated_client.post(f"{url}?path=documents", format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["name"] == "documents"
        assert response.data["type"] == "DIRECTORY"
        assert response.data["path"] == ""

        objs = s3_client.list_objects_v2(Bucket=bucket_name)
        resources = objs.get("Contents", [])
        expected_key = build_s3_key(created_user.id, "documents/")
        s3_keys = {item["Key"]: item for item in resources}
        assert expected_key in s3_keys

    def test_folder_create_nested_success_201(
        self, authenticated_client, s3_client, bucket_name, created_user, create_s3_file
    ):
        create_s3_file("zapret2-master/")
        url = reverse("directory")
        path = "zapret2-master/some-directory"
        response = authenticated_client.post(f"{url}?path={path}", format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["name"] == "some-directory"
        assert response.data["type"] == "DIRECTORY"
        assert response.data["path"] == "zapret2-master/"

        objs = s3_client.list_objects_v2(Bucket=bucket_name)
        resources = objs.get("Contents", [])
        expected_key = build_s3_key(created_user.id, "zapret2-master/some-directory/")
        s3_keys = {item["Key"]: item for item in resources}
        assert expected_key in s3_keys

    @pytest.mark.parametrize(
        "test_path, expected_status, expected_message",
        [
            ("ghost-folder/sub-folder", status.HTTP_404_NOT_FOUND, "Родительская папка не найдена"),
            ("existing-folder", status.HTTP_409_CONFLICT, "Ресурс по указанному пути уже существует"),
        ],
    )
    def test_folder_create_errors(
        self, authenticated_client, create_s3_file, test_path, expected_status, expected_message
    ):
        create_s3_file("existing-folder/")
        url = reverse("directory")
        response = authenticated_client.post(f"{url}?path={test_path}", format="json")

        assert response.status_code == expected_status
        assert response.data.get("message") == expected_message


@pytest.mark.django_db
class TestResourceAPI:
    def test_upload_success_201(
        self, authenticated_client, create_uploaded_file, s3_client, bucket_name, created_user
    ):
        file1 = create_uploaded_file("test_notes.txt")
        file2 = create_uploaded_file("alot_notes")

        url = reverse("resource")
        data = {"file": [file1, file2], "path": ""}
        response = authenticated_client.post(url, data=data, format="multipart")

        assert response.status_code == status.HTTP_201_CREATED
        assert len(response.data) == 2
        items = {item["name"]: item for item in response.data}
        assert "test_notes.txt" in items
        assert "alot_notes" in items

        objs = s3_client.list_objects_v2(Bucket=bucket_name)
        resources = objs.get("Contents", [])
        s3_keys = {item["Key"]: item for item in resources}

        assert len(resources) == 2
        assert build_s3_key(created_user.id, "test_notes.txt") in s3_keys
        assert build_s3_key(created_user.id, "alot_notes") in s3_keys

    def test_upload_pre_flight_check_error_409(
        self, authenticated_client, create_s3_file, create_uploaded_file, s3_client, bucket_name
    ):
        _, path_file_target = create_s3_file("my_folder_notes.txt")
        file1 = create_uploaded_file("my_folder_notes.txt")
        file2 = create_uploaded_file("secure_file")

        url = reverse("resource")
        data = {"file": [file1, file2], "path": ""}
        response = authenticated_client.post(url, data=data, format="multipart")

        assert response.status_code == status.HTTP_409_CONFLICT

        objs = s3_client.list_objects_v2(Bucket=bucket_name)
        resources = objs.get("Contents", [])
        items = {item["Key"]: item for item in resources}

        assert len(resources) == 1
        assert path_file_target in items

    def test_simple_delete_resource_success(self, authenticated_client, bucket_name, create_s3_file, s3_client):
        _, path_file1 = create_s3_file("folder/file1.txt")
        _, path_file2 = create_s3_file("folder/sub/file2.txt")
        _, path_file3 = create_s3_file("other_file.txt")

        url = reverse("resource")
        response = authenticated_client.delete(f"{url}?path=folder/")

        assert response.status_code == status.HTTP_204_NO_CONTENT
        with pytest.raises(ClientError):
            s3_client.head_object(Bucket=bucket_name, Key=path_file1)
        with pytest.raises(ClientError):
            s3_client.head_object(Bucket=bucket_name, Key=path_file2)
        s3_client.head_object(Bucket=bucket_name, Key=path_file3)


@pytest.mark.django_db
class TestDownloadAPI:
    def test_download_resource_success(self, authenticated_client, create_s3_file):
        expected_content = b"just for test"
        filename, _ = create_s3_file("123.png", content=expected_content)

        url = reverse("download")
        response = authenticated_client.get(f"{url}?path={filename}")

        assert response.status_code == status.HTTP_200_OK
        assert response["Content-Type"] == "application/octet-stream"
        assert b"".join(response.streaming_content) == expected_content

    def test_download_resource_error_404(self, authenticated_client):
        url = reverse("download")
        response = authenticated_client.get(f"{url}?path=124.png")

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.data["message"] == "Ресурс не найден"

    @pytest.mark.parametrize("invalid_path", ["", "   ", "../file.png", "folder/../../secret.txt"])
    def test_download_resource_error_400(self, authenticated_client, invalid_path):
        url = reverse("download")
        response = authenticated_client.get(f"{url}?path={invalid_path}")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["message"] == "Недопустимый или пустой путь к ресурсу"

    def test_download_resource_unauthorized(self, api_client):
        url = reverse("download")
        response = api_client.get(f"{url}?path=test.png")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestMoveAPI:
    def test_move_file_success(self, authenticated_client, created_user, bucket_name, create_s3_file, s3_client):
        source_rel_path = "folder/old_name.txt"
        target_rel_path = "folder/new_name.txt"
        _, source_s3_key = create_s3_file(source_rel_path)

        url = reverse("move")
        response = authenticated_client.post(
            f"{url}?from={source_rel_path}&to={target_rel_path}", format="json"
        )
        assert response.status_code == status.HTTP_200_OK

        with pytest.raises(ClientError):
            s3_client.head_object(Bucket=bucket_name, Key=source_s3_key)

        target_s3_key = build_s3_key(created_user.id, target_rel_path)
        s3_client.head_object(Bucket=bucket_name, Key=target_s3_key)

    def test_move_directory_success(
        self, authenticated_client, create_s3_file, s3_client, bucket_name, created_user
    ):
        source_rel_path = "folder/another_folder/this_folder/"
        target_rel_path = "folder/unique_folder/finish_folder/"

        _, path_file_root = create_s3_file("folder/file_root.txt")
        _, path_file_mid = create_s3_file("folder/another_folder/file_mid.txt")
        _, path_file_target = create_s3_file("folder/another_folder/this_folder/file_target.txt")

        url = reverse("move")
        response = authenticated_client.post(
            f"{url}?from={source_rel_path}&to={target_rel_path}", format="json"
        )
        assert response.status_code == status.HTTP_200_OK

        with pytest.raises(ClientError):
            s3_client.head_object(Bucket=bucket_name, Key=path_file_target)

        path_file_target_new = f"{build_s3_key(created_user.id, target_rel_path)}file_target.txt"
        s3_client.head_object(Bucket=bucket_name, Key=path_file_target_new)
        s3_client.head_object(Bucket=bucket_name, Key=path_file_mid)
        s3_client.head_object(Bucket=bucket_name, Key=path_file_root)


@pytest.mark.django_db
class TestSearchAPI:
    def test_search_resource_success(self, create_s3_file, authenticated_client):
        create_s3_file("folder/file_root.txt")
        create_s3_file("folder/file_qwerty.txt")
        create_s3_file("folder/flle_root.txt")

        url = reverse("search")
        response = authenticated_client.get(f"{url}?query=file", format="json")

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2
        items = {item["name"]: item for item in response.data}

        assert "file_root.txt" in items
        assert "file_qwerty.txt" in items
        assert "flle_root.txt" not in items

    def test_search_folders_and_files_success(self, create_s3_file, authenticated_client):
        create_s3_file("folder/")
        create_s3_file("just_folder/")
        create_s3_file("big_files/")
        create_s3_file("my_folder_notes.txt")

        url = reverse("search")
        response = authenticated_client.get(f"{url}?query=folder", format="json")

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 3
        items = {item["name"]: item for item in response.data}

        assert "folder" in items
        assert items["folder"]["type"] == "DIRECTORY"
        assert "just_folder" in items
        assert items["just_folder"]["type"] == "DIRECTORY"
        assert "big_files" not in items
        assert "my_folder_notes.txt" in items
        assert items["my_folder_notes.txt"]["type"] == "FILE"

    def test_search_resource_error_400(self, authenticated_client):
        url = reverse("search")
        response = authenticated_client.get(f"{url}?query=", format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_search_does_not_leak_other_user_files(
        self, authenticated_client, create_s3_file, bucket_name, s3_client, django_user_model
    ):
        create_s3_file("my_document.pdf")

        other_user = django_user_model.objects.create_user(username="other", password="pwd")
        other_key = build_s3_key(other_user.id, "other_document.pdf")
        s3_client.put_object(
            Bucket=bucket_name,
            Key=other_key,
            Body=b"secret",
        )

        url = reverse("search")
        response = authenticated_client.get(f"{url}?query=document")

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]["name"] == "my_document.pdf"

    def test_search_no_results(self, authenticated_client, create_s3_file):
        create_s3_file("notes.txt")

        url = reverse("search")
        response = authenticated_client.get(f"{url}?query=nonexistent")

        assert response.status_code == status.HTTP_200_OK
        assert response.data == []

    def test_search_case_insensitive(self, authenticated_client, create_s3_file):
        create_s3_file("RePoRt_2026.PDF")

        url = reverse("search")
        response = authenticated_client.get(f"{url}?query=report")

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]["name"] == "RePoRt_2026.PDF"


