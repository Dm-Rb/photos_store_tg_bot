![1](https://github.com/user-attachments/assets/e2e3c6bb-161d-427d-b903-325a57ccbef8)
![2](https://github.com/user-attachments/assets/a7a59af4-946d-4ee7-a999-68d4d2d932cf)
![3](https://github.com/user-attachments/assets/ee920a63-3b1c-44b4-8e9d-b6f684b37b8f)

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

.env file content:

````BOT_TOKEN=your_telegram_bot_token
PASSPHRASE=your_password_for_access
GOOGLE_CREDENTIALS_FILE=credentials.json  # Generated in Google Cloud Console, place in project root
BACKUP_TIME=23:57                        # Daily backup time (UTC)
google_drive_folder_id=1MZqp4Wdt1237Ihaui1  # Specific GD folder ID or None/False if storing files in GD root
backup_files_on_google_drive=1           # 1=enable, 0=disable GD backups
clear_local_disk_after_backup=0          # 1=delete local files after backup, 0=leave all files in temporary directory````
