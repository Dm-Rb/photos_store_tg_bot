This project is a Telegram bot designed to serve as a centralized storage for photos and videos with built-in cataloging functionality.
Problem Statement

I noticed that groups of friends often struggle to find published photos from various events because they are scattered across different platforms (e.g., chats, social media, cloud storage). This bot aims to solve that problem by acting as a personal media archive for such groups.
Key Features
1. Media Cataloging

- Uploaded files are organized into virtual catalogs.

- Each catalog is represented as an inline button—clicking it sends the user all files belonging to that category.

2. Automatic Google Drive Backup

- By default, all uploaded media is automatically backed up to the owner's Google Drive inside an encrypted archive.

- This ensures data safety in case Telegram servers delete the files (e.g., due to storage policies).

- If needed, the bot can download, decrypt, and restore the files upon request.

3. Access Control

- The bot is password-protected—only authorized users can interact with it.

- The password is set in the .env configuration file.

Why Use This Bot?

- No more lost photos – All media stays in one secure place.

- Easy retrieval – Files are neatly categorized for quick access.

- Backup safety – Even if Telegram deletes files, your data remains intact in Google Drive.

- Privacy-first – Encrypted backups and password protection ensure only your group has access.

<b>.env file content:</b>

````
BOT_TOKEN=your_telegram_bot_token
PASSPHRASE=your_password_for_access
GOOGLE_CREDENTIALS_FILE=credentials.json  # Generated in Google Cloud Console, place in project root
BACKUP_TIME=23:57                        # Daily backup time (UTC)
google_drive_folder_id=1MZqp4Wdt1237Ihaui1  # Specific GD folder ID or None/False if storing files in GD root
backup_files_on_google_drive=1           # 1=enable, 0=disable GD backups
clear_local_disk_after_backup=0          # 1=delete local files after backup, 0=leave all files in temporary directory
````
You will also need a "credentials.json" file, which must be generated in your Google Console if you plan to use Google Drive for file backups.

![1](https://github.com/user-attachments/assets/22165a7d-d3d7-41b3-a784-c794ce0ccb1e)
![2](https://github.com/user-attachments/assets/e1ae9c92-ef1f-4568-9f58-d4397e0ca1fd)
![4](https://github.com/user-attachments/assets/d622ba6b-b57a-4c0d-8f60-078c4ff2292c)


