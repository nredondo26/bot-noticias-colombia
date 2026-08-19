import os
import time
import requests
import json


def upload_video(page_id, access_token, video_path, caption="", as_reel=True):
    if not os.path.exists(video_path):
        return {"success": False, "error": f"Video no encontrado: {video_path}"}

    upload_url = "https://graph.facebook.com/v21.0/me/video_uploaders"
    data = {
        "upload_phase": "start",
        "access_token": access_token,
        "upload_asset_type": "STILL_IMAGE",
    }
    try:
        resp = requests.post(upload_url, data=data, timeout=30)
        result = resp.json()
        if "error" in result:
            return {"success": False, "error": result["error"].get("message", "")}
        video_id = result.get("video_id")
        upload_session_id = result.get("upload_session_id")
    except Exception as e:
        return {"success": False, "error": str(e)}

    file_size = os.path.getsize(video_path)

    data2 = {
        "upload_phase": "transfer",
        "upload_session_id": upload_session_id,
        "access_token": access_token,
    }
    files = {"video_chunk": open(video_path, "rb")}
    try:
        resp = requests.post(upload_url, data=data2, files=files, timeout=60)
        result2 = resp.json()
        if "error" in result2:
            return {"success": False, "error": result2["error"].get("message", "")}
    except Exception as e:
        return {"success": False, "error": str(e)}

    data3 = {
        "upload_phase": "finish",
        "upload_session_id": upload_session_id,
        "access_token": access_token,
        "title": caption[:100],
        "description": caption[:5000],
        "video_state": "PUBLISHED",
    }
    if as_reel:
        data3["video_state"] = "PUBLISHED"
        data3["upload_asset_type"] = "STILL_IMAGE"

    try:
        resp = requests.post(upload_url, data=data3, timeout=30)
        result3 = resp.json()
        if "error" in result3:
            return {"success": False, "error": result3["error"].get("message", "")}
    except Exception as e:
        return {"success": False, "error": str(e)}

    return {"success": True, "video_id": video_id}


def post_reel(page_id, access_token, video_path, caption="", hashtags=""):
    full_caption = caption
    if hashtags:
        full_caption += "\n\n" + hashtags

    result = upload_video(page_id, access_token, video_path, full_caption, as_reel=True)

    if result["success"]:
        return {"success": True, "video_id": result["video_id"]}

    return upload_video_simple(page_id, access_token, video_path, full_caption)


def upload_video_simple(page_id, access_token, video_path, description=""):
    url = f"https://graph.facebook.com/v21.0/{page_id}/videos"
    files = {"source": open(video_path, "rb")}
    data = {
        "access_token": access_token,
        "description": description[:5000],
        "title": description[:100],
    }
    try:
        resp = requests.post(url, data=data, files=files, timeout=120)
        result = resp.json()
        if "id" in result:
            return {"success": True, "video_id": result["id"]}
        return {"success": False, "error": result.get("error", {}).get("message", "")}
    except Exception as e:
        return {"success": False, "error": str(e)}
