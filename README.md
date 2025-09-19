# Cursor Update Script

A Python script that automatically downloads and installs the latest version of Cursor (AI-first code editor) for Linux systems. The script intelligently checks for updates and only downloads when a newer version is available.

## Features

- 🔄 **Automatic Version Checking**: Compares current installed version with latest available
- 📦 **Smart Download**: Only downloads when a newer version is available
- 🚀 **One-Click Installation**: Automatically installs to `/usr/local/bin/cursor`
- 🖥️ **Desktop Integration**: Creates/updates desktop file for application menu
- 📊 **Progress Tracking**: Real-time download progress with percentage
- ✅ **Success/Failure Tracking**: Comprehensive counters for all operations
- 🔧 **Error Handling**: Robust error handling with detailed feedback
- 🔐 **Sudo Support**: Handles both regular user and sudo execution scenarios

## Requirements

- **Python 3.6+**
- **Linux system** (tested on Ubuntu/Debian)
- **Internet connection** for downloading updates
- **Git** (for repository operations)
- **sudo privileges** (for system-wide installation)

## Installation

1. **Clone this repository:**
   ```bash
   git clone https://github.com/s0m3One47/update-cursor.git
   cd update-cursor
   ```

2. **Make the script executable:**
   ```bash
   chmod +x update-cursor.py
   ```

3. **Run the script:**
   ```bash
   sudo python3 update-cursor.py
   ```

## Usage

### Basic Usage

```bash
sudo python3 update-cursor.py
```

### What the Script Does

1. **Repository Management**:
   - Updates the local `cursor-ai-downloads` repository
   - Fetches latest version information

2. **Version Comparison**:
   - Reads current installed version from `cursor_version.txt`
   - Compares with latest available version
   - Skips download if already up to date

3. **Download & Installation** (if update needed):
   - Downloads latest Cursor AppImage
   - Makes it executable
   - Installs to `/usr/local/bin/cursor`
   - Updates desktop file for application menu
   - Updates version tracking file

4. **Progress Reporting**:
   - Shows real-time download progress
   - Displays success/failure counters
   - Provides final summary with success rate

## Example Output

### When Update is Available:
```
🚀 Cursor Update Script
==================================================
🔍 Updating local repository...
📥 Fetching latest changes...
✅ Fetched latest changes.
🔄 Pulling latest changes...
✅ Pulled latest changes.
✅ Updated local repository.

📖 Reading version history...
✅ Latest version found: 1.5.12
📖 Current installed version: 1.5.11
📥 Cursor is not up to date, downloading latest version...
📦 Downloading Cursor 1.5.12
📥 Downloading... 100.0%
✅ Download completed: /tmp/tmpXXXXXX.AppImage

🔧 Making /tmp/tmpXXXXXX.AppImage executable...
✅ File is now executable

📦 Installing Cursor to /usr/local/bin/cursor...
✅ Cursor installed successfully

📝 Updating existing desktop file...
✅ Desktop file updated

📝 Updating version file with version: 1.5.12
✅ Version file updated: /home/user/Projects/update-cursor/cursor_version.txt

✅ Updated Cursor successfully!
🎉 Cursor update completed successfully!

📊 Summary:
   ✅ Successful operations: 8
   ❌ Failed operations: 0
   📈 Success rate: 100.0%
```

### When Already Up to Date:
```
🚀 Cursor Update Script
==================================================
⚠️ This script needs to install to /usr/local/bin/
   You may need to run with sudo

🔍 Updating local repository...
📥 Fetching latest changes...
✅ Fetched latest changes.
🔄 Pulling latest changes...
✅ Pulled latest changes.
✅ Updated local repository.
📖 Reading version history...
✅ Latest version found: 1.6.27
📖 Current installed version: 1.6.27
✅ Cursor is already up to date (version 1.6.27)
   No download needed

🎉 Cursor is already up to date!
   You can launch Cursor from your applications menu or run 'cursor' from terminal

📊 Summary:
   ✅ Successful operations: 6
   ❌ Failed operations: 0
   📈 Success rate: 100.0%
```

## File Structure

```
update-cursor/
├── update-cursor.py          # Main update script
├── cursor_version.txt        # Tracks current installed version
├── cursor-ai-downloads/      # Local repository with version data
│   ├── version-history.json  # Version information database
│   └── cursor_products/      # Product files for each version
|   └── ...
└── README.md                 # This file
```

## Configuration

The script automatically handles:
- **Repository Path**: `.../update-cursor/cursor-ai-downloads/`
- **Installation Path**: `/usr/local/bin/cursor`
- **Desktop File**: `~/.local/share/applications/cursor.desktop`
- **Version File**: `.../update-cursor/cursor_version.txt`

All errors are tracked in the success/failure counters and displayed in the final summary.

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes
4. Test thoroughly
5. Commit your changes: `git commit -am 'Add feature'`
6. Push to the branch: `git push origin feature-name`
7. Submit a pull request

## License

This project is under MIT License.

## Acknowledgments

- **Cursor Team** for creating the amazing AI-first code editor
- **oslook/cursor-ai-downloads** repository for maintaining version information
- **Python Community** for the excellent standard library

**Note**: This script is designed for Linux systems. For other operating systems, please refer to the official Cursor documentation for installation instructions.
