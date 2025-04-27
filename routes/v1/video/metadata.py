import os
import logging
from flask import Blueprint, request, jsonify
from app_utils import *
from services.v1.ffmpeg.ffmpeg_compose import get_metadata
from services.authentication import authenticate
from services.file_management import download_file
from config import LOCAL_STORAGE_PATH

v1_video_metadata_bp = Blueprint('v1_video_metadata', __name__)
logger = logging.getLogger(__name__)

@v1_video_metadata_bp.route('/v1/video/metadata', methods=['POST'])
@authenticate
@validate_payload({
    "type": "object",
    "properties": {
        "video_url": {"type": "string", "format": "uri"},
        "metadata": {
            "type": "object",
            "properties": {
                "thumbnail": {"type": "boolean"},
                "filesize": {"type": "boolean"},
                "duration": {"type": "boolean"},
                "bitrate": {"type": "boolean"},
                "encoder": {"type": "boolean"}
            }
        },
        "id": {"type": "string"}
    },
    "required": ["video_url"],
    "additionalProperties": False
})
@queue_task_wrapper(bypass_queue=False)
def video_metadata_api(job_id, data):
    video_url = data['video_url']

    logger.info(f"Job {job_id}: Received v1 captioning request for {video_url}")

    try:
        video_path = download_file(video_url, LOCAL_STORAGE_PATH)
        logger.info(f"Job {job_id}: Video downloaded to {video_path}")
    except Exception as e:
        logger.error(f"Job {job_id}: Video download error: {str(e)}")
        # For non-font errors, do NOT include available_fonts
        return {"error": str(e)}

    try:
        metadata = []
        metadata = get_metadata(video_path, data["metadata"], job_id)

        return metadata, "/v1/video/metadata", 200
        
    except Exception as e:
        logger.error(f"Job {job_id}: Error processing Metadata request - {str(e)}")
        return str(e), "/v1/video/metadata", 500