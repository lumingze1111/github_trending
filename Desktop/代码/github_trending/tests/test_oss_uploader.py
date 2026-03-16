"""Tests for OSS uploader."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
from src.oss_uploader import OSSUploader
from src.exceptions import OSSException
import oss2


@pytest.fixture
def mock_oss_bucket():
    """Mock OSS bucket."""
    bucket = Mock()
    bucket.put_object.return_value = Mock(status=200)
    bucket.put_object_acl.return_value = None
    bucket.head_object.return_value = Mock()
    bucket.delete_object.return_value = None
    return bucket


@pytest.fixture
def uploader(mock_oss_bucket):
    """Create OSS uploader with mocked bucket."""
    with patch("src.oss_uploader.oss2.Auth"), \
         patch("src.oss_uploader.oss2.Bucket", return_value=mock_oss_bucket):
        uploader = OSSUploader(
            access_key_id="test_key",
            access_key_secret="test_secret",
            bucket_name="test-bucket",
            endpoint="oss-cn-test.aliyuncs.com",
            path_prefix="github-trending",
        )
        return uploader


def test_oss_uploader_initialization():
    """Test OSS uploader initializes correctly."""
    with patch("src.oss_uploader.oss2.Auth"), \
         patch("src.oss_uploader.oss2.Bucket"):
        uploader = OSSUploader(
            access_key_id="test_key",
            access_key_secret="test_secret",
            bucket_name="test-bucket",
            endpoint="oss-cn-test.aliyuncs.com",
        )

        assert uploader.access_key_id == "test_key"
        assert uploader.bucket_name == "test-bucket"
        assert uploader.endpoint == "oss-cn-test.aliyuncs.com"
        assert uploader.path_prefix == ""


def test_oss_uploader_initialization_with_prefix():
    """Test OSS uploader with path prefix."""
    with patch("src.oss_uploader.oss2.Auth"), \
         patch("src.oss_uploader.oss2.Bucket"):
        uploader = OSSUploader(
            access_key_id="test_key",
            access_key_secret="test_secret",
            bucket_name="test-bucket",
            endpoint="oss-cn-test.aliyuncs.com",
            path_prefix="github-trending/",
        )

        assert uploader.path_prefix == "github-trending"


def test_upload_file(uploader, tmp_path):
    """Test uploading file to OSS."""
    # Create test file
    test_file = tmp_path / "test.html"
    test_file.write_text("Test content")

    url = uploader.upload_file(str(test_file))

    assert url == "https://test-bucket.oss-cn-test.aliyuncs.com/github-trending/test.html"
    uploader.bucket.put_object.assert_called_once()
    uploader.bucket.put_object_acl.assert_called_once()


def test_upload_file_with_custom_object_name(uploader, tmp_path):
    """Test uploading file with custom object name."""
    test_file = tmp_path / "test.html"
    test_file.write_text("Test content")

    url = uploader.upload_file(str(test_file), object_name="custom-name.html")

    assert url == "https://test-bucket.oss-cn-test.aliyuncs.com/github-trending/custom-name.html"


def test_upload_file_not_found(uploader):
    """Test uploading non-existent file raises exception."""
    with pytest.raises(OSSException, match="Local file not found"):
        uploader.upload_file("/nonexistent/file.html")


def test_upload_file_oss_error(uploader, tmp_path):
    """Test handling OSS error during upload."""
    test_file = tmp_path / "test.html"
    test_file.write_text("Test content")

    uploader.bucket.put_object.side_effect = oss2.exceptions.OssError(
        500, {}, "", {"Code": "InternalError"}
    )

    with pytest.raises(OSSException, match="Failed to upload to OSS"):
        uploader.upload_file(str(test_file))


def test_upload_file_bad_status(uploader, tmp_path):
    """Test handling bad status code from OSS."""
    test_file = tmp_path / "test.html"
    test_file.write_text("Test content")

    uploader.bucket.put_object.return_value = Mock(status=500)

    with pytest.raises(OSSException, match="Upload failed with status: 500"):
        uploader.upload_file(str(test_file))


def test_generate_public_url(uploader):
    """Test generating public URL."""
    url = uploader._generate_public_url("test/file.html")
    assert url == "https://test-bucket.oss-cn-test.aliyuncs.com/test/file.html"


def test_file_exists(uploader):
    """Test checking if file exists."""
    assert uploader.file_exists("test.html") is True
    uploader.bucket.head_object.assert_called_once_with("test.html")


def test_file_exists_not_found(uploader):
    """Test checking non-existent file."""
    uploader.bucket.head_object.side_effect = oss2.exceptions.NoSuchKey(
        404, {}, "", {"Code": "NoSuchKey"}
    )

    assert uploader.file_exists("nonexistent.html") is False


def test_file_exists_error(uploader):
    """Test handling error when checking file existence."""
    uploader.bucket.head_object.side_effect = Exception("Connection error")

    assert uploader.file_exists("test.html") is False


def test_delete_file(uploader):
    """Test deleting file from OSS."""
    result = uploader.delete_file("test.html")

    assert result is True
    uploader.bucket.delete_object.assert_called_once_with("test.html")


def test_delete_file_error(uploader):
    """Test handling error when deleting file."""
    uploader.bucket.delete_object.side_effect = Exception("Delete failed")

    result = uploader.delete_file("test.html")

    assert result is False


def test_upload_file_without_prefix(tmp_path):
    """Test uploading file without path prefix."""
    mock_bucket = Mock()
    mock_bucket.put_object.return_value = Mock(status=200)
    mock_bucket.put_object_acl.return_value = None

    with patch("src.oss_uploader.oss2.Auth"), \
         patch("src.oss_uploader.oss2.Bucket", return_value=mock_bucket):
        uploader = OSSUploader(
            access_key_id="test_key",
            access_key_secret="test_secret",
            bucket_name="test-bucket",
            endpoint="oss-cn-test.aliyuncs.com",
            path_prefix="",
        )

        test_file = tmp_path / "test.html"
        test_file.write_text("Test content")

        url = uploader.upload_file(str(test_file))

        assert url == "https://test-bucket.oss-cn-test.aliyuncs.com/test.html"
