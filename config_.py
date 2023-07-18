#Rename this file to config.py and fill in the values

from pydantic import BaseSettings


class Settings(BaseSettings):
    MongoDB_username: str = "username"
    MongoDB_password: str = "password"
    MongoDB_id: str = "cluster_id"
    file_count: int = 0
    google_drive_api_key = "API_key"
    google_auth_path = "path_to_auth_file"
    bucket_name = "bucket_name"
    email: str = "admin_email"
    password: str = "admin_password"
    nonce: str = "define a nonce"


settings = Settings()
