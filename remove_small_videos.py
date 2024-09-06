import os
import sys

def remove_small_videos(folder_path, size_limit_mb=5):
    size_limit_bytes = size_limit_mb * 1024 * 1024  # Convert MB to bytes
    removed_count = 0

    # Check if the folder exists
    if not os.path.isdir(folder_path):
        print(f"Error: The folder '{folder_path}' does not exist.")
        return

    # Iterate through all files in the folder
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        
        # Check if it's a file (not a directory)
        if os.path.isfile(file_path):
            # Check if the file size is less than the limit
            if os.path.getsize(file_path) < size_limit_bytes:
                try:
                    os.remove(file_path)
                    print(f"Removed: {filename}")
                    removed_count += 1
                except Exception as e:
                    print(f"Error removing {filename}: {str(e)}")

    print(f"\nTotal files removed: {removed_count}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python remove_small_videos.py <folder_path>")
        sys.exit(1)

    folder_path = sys.argv[1]
    remove_small_videos(folder_path)