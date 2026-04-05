import dropbox
import os
import datetime
from dropbox.files import FileMetadata
from upload_post import UploadPostClient, UploadPostError
import time


# Replace with your access token
ACCESS_TOKEN_DB = ""
ACCESS_TOKEN_UP = ""
# Folder path in Dropbox (e.g., "/my-folder")
FOLDER_PATH = "/Apps/SocialContentManager"
CACHE_DIR = "/tmp/SocialMediacache"
VIDEOS = []
UPLOADVIDEO = None
dbx = dropbox.Dropbox(ACCESS_TOKEN_DB)
ARCHIVE_DB = "Apps/archive"



class Video:
    def __init__(self, name, dbpath, upload_time):
        self.name = name
        self.dbpath = dbpath
        self.upload_time = upload_time
        self.location = extract_location_from_path(dbpath)
        self.title = datetime.datetime.now().strftime(f"{self.location}, %B %d, %Y")
        self.upload_job_id = None
        self.tags = generate_tags(TAG_POOL, CORE_TAGS, self.location)
        self.local_path = os.path.join(CACHE_DIR, "upload_video.mov")  # Local path for downloaded video

def extract_location_from_path(path):
    """Extract location (folder name) from Dropbox path"""
    parts = path.split('/')
    # Path structure: /apps/socialcontentmanager/stockholm/video...
    # After split: ['', 'apps', 'socialcontentmanager', 'stockholm', 'video...']
    if len(parts) > 3:
        return parts[3].capitalize()  # Gets 'stockholm'
    return ""

def list_files_with_upload_time():
    try:
        result = dbx.files_list_folder(FOLDER_PATH, recursive=True)

        for entry in result.entries:
            if isinstance(entry, FileMetadata):
                video = Video(entry.name, entry.path_lower, entry.server_modified)
                print(f"Name: {video.name}, Path: {video.dbpath}, Upload Time: {video.upload_time}, Location: {video.location}")
                VIDEOS.append(video)

        # Handle pagination if many files
        while result.has_more:
            result = dbx.files_list_folder_continue(result.cursor)
            for entry in result.entries:
                if isinstance(entry, FileMetadata):
                    video = Video(entry.name, entry.path_lower, entry.server_modified)
                    print(f"Name: {video.name}, Path: {video.dbpath}, Upload Time: {video.upload_time}, Location: {video.location}")
                    VIDEOS.append(video)

    except Exception as e:
        print("Error:", e)

def download_file_by_video(video):

    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR)
    try:
        
        dbx.files_download_to_file(video.local_path, video.dbpath)
        
        print(f"Downloaded: {video.name} -> {video.local_path}")
    except Exception as e:
        print("Error:", e)

def move_file_to_archive(video):
    try:
        archive_path = f"{ARCHIVE_DB}"
        dbx.files_move_v2(video.dbpath, archive_path)
        print(f"Moved to archive: {video.dbpath} -> {archive_path}")
    except Exception as e:
        print("Error moving file to archive:", e)

def publish_video(video):
    client = UploadPostClient(ACCESS_TOKEN_UP)
    try:
        response = client.upload_video(
        video.local_path,  # Local path to the video file
        title = video.title,
        share_to_feed = True,  # Instagram Reels
        media_type = "REELS",  # Instagram Reels
        async_upload = True,
        user= "MrsMelbourneTiktok",
        platforms=["instagram", "tiktok", "youtube", "facebook", "pinterest"],
        # Optional: Platform-specific settings
        #privacy_level="PUBLIC_TO_EVERYONE",  # TikTok
        privacyStatus = "public",  # YouTube
        tags = video.tags,  # YouTube
        facebook_page_id = "1102374626282295",
        pinterest_board_id = "1100989508844827449",
        #user_tags = ",".join(video.tags),  # Instagram user-generated tags
    )
        print ("Upload response:", response)
        print("Job id:", response.get("job_id"))
        UPLOADVIDEO.upload_job_id = response.get("job_id")
        while True:
            status = client.get_status(response.get("job_id"))
            print(status)
            time.sleep(5)
    except UploadPostError as e:
        print("Upload failed:", str(e))   
    
def GetTags(video):
    try:
        tags_result = dbx.files_tags_get([video.path])
        
        # tags_result is a GetTagsResult object, access .paths_to_tags to get the list
        paths_to_tags = tags_result.paths_to_tags
        
        if paths_to_tags and len(paths_to_tags) > 0:
            path_to_tags = paths_to_tags[0]  # Get the first result
            tags = path_to_tags.tags  # This is a list of Tag objects
            
            # Extract tag text from each tag
            tag_texts = []
            for tag in tags:
                tag_texts.append(tag.get_user_generated_tag().tag_text)
            
            return tag_texts
        return []
    except Exception as e:
        print("Error getting tags:", e)
        return None

import random

TAG_POOL = [
    "writing", "writerlife", "writingjourney", "amwriting",
    "authorlife", "bookwriting", "writingprocess", "storytelling",
    "aspiringauthor", "writersofinstagram", "creativewriting",
    "dailyvideo", "dailyvlog", "dailyseries", "30secondvideo",
    "shortformcontent", "consistency", "buildinpublic",
    "dayinthelife", "creativejourney", "aestheticvideo",
    "ambientvibes", "creativevibes", "solocreator",
    "femalewriter", "womenwhowrite", "creatorlife",
    "youtubeShorts", "shortsvideo", "tiktokcreator",
    "reelsvideo", "contentcreator",
    "motivation", "discipline", "focusmode",
    "progressnotperfection", "creativehabit",
    "writingabook", "writinginspiration", "authorjourney",
    "behindthescenes", "writingroutine"
]

CORE_TAGS = [
    "writing", "writerlife", "writingjourney", "authorlife"
]

def generate_tags(pool, core, location, total_tags=15):
    core.append(location.lower())  # Add location as a core tag
    remaining_slots = total_tags - len(core)
    random_tags = random.sample(pool, remaining_slots)
    
    final_tags = list(set(core + random_tags))
    random.shuffle(final_tags)
    
    return final_tags


if __name__ == "__main__":
    list_files_with_upload_time()
    VIDEOS.sort(key=lambda video: video.upload_time)  # Oldest first
    UPLOADVIDEO = VIDEOS[0]  # Get the oldest video
    #download_file_by_video(UPLOADVIDEO)  # Download the oldest video
    #publish_video(UPLOADVIDEO)  # Publish the video to social media
    move_file_to_archive(UPLOADVIDEO)  # Move the video to archive after publishing
    
    