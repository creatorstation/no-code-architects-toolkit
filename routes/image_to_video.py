from flask import Blueprint, request, jsonify
from flask import current_app
from app_utils import *
import logging
from services.image_to_video import process_image_to_video
from services.authentication import authenticate
from services.gcp_toolkit import upload_to_gcs

image_to_video_bp = Blueprint('image_to_video', __name__)
logger = logging.getLogger(__name__)

@image_to_video_bp.route('/image-to-video', methods=['POST'])
@authenticate
@validate_payload({
    "type": "object",
    "properties": {
        "image_url": {"type": "string", "format": "uri"},
        "length": {"type": "number", "minimum": 1, "maximum": 60},
        "frames": {"type": "integer", "minimum": 30, "maximum": 1800},
        "zoom": {"type": "number", "minimum": 0.0001, "maximum": 0.1},
        "webhook_url": {"type": "string", "format": "uri"},
        "id": {"type": "string"}
    },
    "required": ["image_url"],
    "additionalProperties": False
})
@queue_task_wrapper(bypass_queue=False)
def image_to_video(job_id, data):
    image_url = data.get('image_url')
    length = data.get('length', 5)
    frames = data.get('frames', 600)
    zoom = data.get('zoom', 0.0015)
    webhook_url = data.get('webhook_url')
    id = data.get('id')

    logger.info(f"Job {job_id}: Received image to video request for {image_url}")

    try:
        output_filename = process_image_to_video(
            image_url, length, frames, zoom, job_id, webhook_url
        )
        gcs_url = upload_to_gcs(output_filename)

        return gcs_url, "/image-to-video", 200
        
    except Exception as e:
        logger.error(f"Job {job_id}: Error processing image to video: {str(e)}", exc_info=True)
        return str(e), "/image-to-video", 500