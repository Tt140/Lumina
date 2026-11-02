"""LuminaLab Swarm - S3 Storage and Polly Voice Service Module."""

import os
import uuid
from pathlib import Path
from typing import Any
from src.config import get_config


class S3PollyService:
    """
    Handles Amazon S3 storage for interactive labs and AWS Polly for audio narration.
    In Mock mode: saves artifacts locally in the _mock_storage/ directory.
    """

    def __init__(self, mock_dir: Path | str = "_mock_storage") -> None:
        """
        Initializes S3 and Polly clients or sets up local mock fallback storage.
        """
        config = get_config()
        self.mock_mode = config.LUMINA_MOCK_MODE
        self._mock_dir = Path(mock_dir)

        if self.mock_mode:
            self.s3_client = None
            self.polly_client = None
            self.bucket_name = "mock_local"
            self._mock_dir.mkdir(parents=True, exist_ok=True)
            (self._mock_dir / "labs").mkdir(parents=True, exist_ok=True)
            (self._mock_dir / "audio").mkdir(parents=True, exist_ok=True)
        else:
            import boto3
            import botocore.config
            boto_config = botocore.config.Config(
                connect_timeout=2.0,
                read_timeout=5.0,
                retries={"max_attempts": 2}
            )
            self.s3_client = boto3.client("s3", region_name=config.AWS_REGION, config=boto_config)
            self.polly_client = boto3.client("polly", region_name=config.AWS_REGION, config=boto_config)
            self.bucket_name = config.S3_BUCKET_NAME

    def upload_lab_to_s3(self, html_content: str, session_id: str) -> dict[str, Any]:
        """
        Uploads interactive simulation lab as a standalone HTML package to S3.

        Parameters:
            html_content: Complete standalone HTML content.
            session_id: Session identifier used as file key.

        Returns:
            dict with structure:
            {
                "s3_url": str,          # Accessible URL (S3 presigned/direct or local file URI)
                "bucket": str,
                "key": str,             # "labs/{session_id}.html"
                "size_kb": float,
                "status": "uploaded"
            }
        """
        key = f"labs/{session_id}.html"
        encoded = html_content.encode("utf-8")
        size_kb = len(encoded) / 1024.0

        if self.mock_mode:
            file_path = self._mock_dir / "labs" / f"{session_id}.html"
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(html_content)
            s3_url = f"file://{file_path.resolve()}"
            return {
                "s3_url": s3_url,
                "bucket": self.bucket_name,
                "key": key,
                "size_kb": size_kb,
                "status": "uploaded",
            }
        else:
            file_path = self._mock_dir / "labs" / f"{session_id}.html"
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(html_content)

            try:
                self.s3_client.put_object(
                    Bucket=self.bucket_name,
                    Key=key,
                    Body=encoded,
                    ContentType="text/html; charset=utf-8",
                )
                try:
                    s3_url = self.s3_client.generate_presigned_url(
                        "get_object",
                        Params={"Bucket": self.bucket_name, "Key": key},
                        ExpiresIn=86400 * 7
                    )
                except Exception:
                    s3_url = f"https://{self.bucket_name}.s3.amazonaws.com/{key}"
                status = "uploaded"
            except Exception as e:
                s3_url = f"file://{file_path.resolve()}"
                status = "uploaded_local_fallback"

            return {
                "s3_url": s3_url,
                "bucket": self.bucket_name,
                "key": key,
                "size_kb": size_kb,
                "status": status,
            }

    def synthesize_speech(
        self,
        text: str,
        language: str = "ar",
        session_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Synthesizes text into an audio narration file using Amazon Polly.

        Parameters:
            text: Text script to convert into voice audio.
            language: "ar" or "en" to determine the Polly voice persona.
            session_id: Optional session identifier for audio filename.

        Returns:
            dict with structure:
            {
                "audio_url": str,       # Direct or presigned URL for the audio stream
                "voice_id": str,        # Polly voice identifier utilized
                "language": str,
                "text_length": int,
                "status": "synthesized"
            }
        """
        config = get_config()
        voice_id = config.POLLY_VOICE_AR if language == "ar" else config.POLLY_VOICE_EN
        resolved_session_id = session_id or f"audio_{uuid.uuid4().hex[:12]}"

        if self.mock_mode:
            file_path = self._mock_dir / "audio" / f"{resolved_session_id}.mp3"
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(text)
            audio_url = f"file://{file_path.resolve()}"
            return {
                "audio_url": audio_url,
                "voice_id": voice_id,
                "language": language,
                "text_length": len(text),
                "status": "synthesized",
            }
        else:
            if language == "ar":
                if voice_id in ["Hala", "Zayd"]:
                    language_code = "ar-AE"
                    preferred_engine = "neural"
                else:
                    language_code = "arb"
                    preferred_engine = "standard"
            else:
                language_code = "en-US"
                preferred_engine = "neural"

            audio_key = f"audio/{resolved_session_id}.mp3"
            local_file = self._mock_dir / "audio" / f"{resolved_session_id}.mp3"
            local_file.parent.mkdir(parents=True, exist_ok=True)

            try:
                # Try preferred engine first (e.g. neural for Hala/Joanna)
                try:
                    response = self.polly_client.synthesize_speech(
                        Text=text,
                        OutputFormat="mp3",
                        VoiceId=voice_id,
                        LanguageCode=language_code,
                        Engine=preferred_engine,
                    )
                except Exception as ex:
                    err_str = str(ex).lower()
                    if "engine" in err_str or "parameter" in err_str or "validationexception" in err_str:
                        fallback_voice = "Zeina" if language == "ar" else "Joanna"
                        fallback_code = "arb" if language == "ar" else "en-US"
                        response = self.polly_client.synthesize_speech(
                            Text=text,
                            OutputFormat="mp3",
                            VoiceId=fallback_voice,
                            LanguageCode=fallback_code,
                            Engine="standard",
                        )
                        voice_id = fallback_voice
                    else:
                        raise ex

                audio_data = response["AudioStream"].read()

                # Always cache audio binary locally so /api/audio/{id}.mp3 streams instantly
                with open(local_file, "wb") as f:
                    f.write(audio_data)

                # Upload to S3 bucket without ACL
                self.s3_client.put_object(
                    Bucket=self.bucket_name,
                    Key=audio_key,
                    Body=audio_data,
                    ContentType="audio/mpeg",
                )
                try:
                    audio_url = self.s3_client.generate_presigned_url(
                        "get_object",
                        Params={"Bucket": self.bucket_name, "Key": audio_key},
                        ExpiresIn=86400 * 7
                    )
                except Exception:
                    audio_url = f"https://{self.bucket_name}.s3.amazonaws.com/{audio_key}"
                status = "synthesized"
            except Exception as e:
                if not local_file.exists():
                    with open(local_file, "w", encoding="utf-8") as f:
                        f.write(text)
                audio_url = f"/api/audio/{resolved_session_id}.mp3"
                status = "synthesized_local_fallback"

            return {
                "audio_url": audio_url,
                "local_url": f"/api/audio/{resolved_session_id}.mp3",
                "voice_id": voice_id,
                "language": language,
                "text_length": len(text),
                "status": status,
            }

    def create_offline_package(
        self,
        html_content: str,
        voice_script: str,
        session_id: str,
        language: str = "ar",
    ) -> dict[str, Any]:
        """
        Builds a complete standalone offline deployment package: simulation lab HTML + Polly audio.

        Parameters:
            html_content: Complete interactive lab HTML string.
            voice_script: Voice narration script text.
            session_id: Session identifier.
            language: Language code ("ar" or "en").

        Returns:
            dict with structure:
            {
                "s3_lab": dict,         # Result from upload_lab_to_s3
                "polly_audio": dict,    # Result from synthesize_speech
                "total_size_kb": float,
                "is_offline_ready": bool
            }
        """
        s3_lab = self.upload_lab_to_s3(html_content=html_content, session_id=session_id)
        polly_audio = self.synthesize_speech(
            text=voice_script,
            language=language,
            session_id=session_id,
        )

        script_size_kb = len(voice_script.encode("utf-8")) / 1024.0
        total_size_kb = s3_lab["size_kb"] + script_size_kb
        is_offline_ready = s3_lab["size_kb"] < 200.0

        return {
            "s3_lab": s3_lab,
            "polly_audio": polly_audio,
            "total_size_kb": round(total_size_kb, 2),
            "is_offline_ready": is_offline_ready,
        }
