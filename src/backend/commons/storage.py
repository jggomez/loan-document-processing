from google.cloud import storage


class GoogleCloudStorage:
    """
    A client for interacting with Google Cloud Storage.
    """

    def __init__(self, project_id: str):
        self.client = storage.Client(project=project_id)

    def upload_file(
        self, bucket_name: str, source_file_name: str, destination_blob_name: str
    ):
        try:
            bucket = self.client.bucket(bucket_name)
            blob = bucket.blob(destination_blob_name)

            blob.upload_from_filename(source_file_name)

            print(
                f"File {source_file_name} uploaded to {destination_blob_name} in bucket {bucket_name}."
            )

            return blob.public_url
        except Exception as e:
            print(f"An error occurred: {e}")
            raise
