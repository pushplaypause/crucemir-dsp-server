import os
import json

VERSION_DIR = "/app/song_versions"

def save_version(song_id, audio_url):
    song_folder = os.path.join(VERSION_DIR, song_id)
    os.makedirs(song_folder, exist_ok=True)

    version_path = os.path.join(song_folder, "versions.json")

    if os.path.exists(version_path):
        versions = json.load(open(version_path))
    else:
        versions = []

    version_num = len(versions) + 1

    entry = {
        "version": f"v{version_num}",
        "audio_url": audio_url
    }

    versions.append(entry)

    json.dump(versions, open(version_path, "w"))

    return {
        "saved_as": f"v{version_num}",
        "versions": versions
    }


def get_versions(song_id):
    version_path = os.path.join(VERSION_DIR, song_id, "versions.json")
    if not os.path.exists(version_path):
        return []
    return json.load(open(version_path))
