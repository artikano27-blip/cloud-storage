from unittest.mock import MagicMock

from storage.services import S3MutationService


def test_delete_objects_batch_splits_into_chunks():
    service = S3MutationService()
    mock_delete = MagicMock()
    setattr(service.client, "delete_objects", mock_delete)

    test_keys = [{"Key": f"file_{i}.txt"} for i in range(1050)]
    service._delete_objects_batch(test_keys)

    assert mock_delete.call_count == 2
    first_batch_objects = mock_delete.call_args_list[0].kwargs["Delete"]["Objects"]
    second_batch_objects = mock_delete.call_args_list[1].kwargs["Delete"]["Objects"]
    assert len(first_batch_objects) == 1000
    assert len(second_batch_objects) == 50