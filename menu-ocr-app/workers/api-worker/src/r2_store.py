import os
import boto3
import anyio

R2_BUCKET = os.getenv("R2_BUCKET", "")
R2_ENDPOINT = os.getenv("R2_ENDPOINT", "")
R2_ACCESS_KEY_ID = os.getenv("R2_ACCESS_KEY_ID", "")
R2_SECRET_ACCESS_KEY = os.getenv("R2_SECRET_ACCESS_KEY", "") or os.getenv("R2_ACCESS_KEY_SECRET", "")
CF_ACCOUNT_ID = os.getenv("CF_ACCOUNT_ID", "")

class R2Store:
    def __init__(self):
        endpoint = R2_ENDPOINT
        if not endpoint and CF_ACCOUNT_ID:
            endpoint = f"https://{CF_ACCOUNT_ID}.r2.cloudflarestorage.com"

        if not all([R2_BUCKET, endpoint, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY]):
            raise RuntimeError("R2 credentials not configured")
        self._client = boto3.client(
            "s3",
            endpoint_url=endpoint,
            aws_access_key_id=R2_ACCESS_KEY_ID,
            aws_secret_access_key=R2_SECRET_ACCESS_KEY,
            region_name="auto",
        )

    async def upload(self, key, data: bytes):
        def _put():
            self._client.put_object(Bucket=R2_BUCKET, Key=key, Body=data)
        await anyio.to_thread.run_sync(_put)

    async def download(self, key):
        def _get():
            resp = self._client.get_object(Bucket=R2_BUCKET, Key=key)
            return resp["Body"].read()
        return await anyio.to_thread.run_sync(_get)
