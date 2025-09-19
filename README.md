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
- **Bun** (JavaScript runtime for running TypeScript scripts)
- **Linux system** (tested on Ubuntu/Debian)
- **Internet connection** for downloading updates
- **sudo privileges** (optional - for system-wide installation only)

## Installation

1. **Install Bun** (if not already installed):
   ```bash
   curl -fsSL https://bun.sh/install | bash
   # Or using npm: npm install -g bun
   ```

   **Note**: The script automatically detects Bun in `~/.bun/bin/bun` (user installation) or system PATH.

2. **Clone this repository:**
   ```bash
   git clone https://github.com/s0m3One47/update-cursor.git
   cd update-cursor
   ```

3. **Make the script executable:**
   ```bash
   chmod +x update-cursor.py
   ```

4. **Run the script:**

   **For system-wide installation (recommended):**
   ```bash
   sudo python3 update-cursor.py
   ```

   **For user-only installation (no sudo required):**
   ```bash
   python3 update-cursor.py
   ```

   **Optional: Add to PATH for user-only installation**

   To run `cursor` from anywhere without specifying the full path, add this to your `~/.bashrc` or `~/.zshrc`:
   ```bash
   export PATH="$HOME/.local/bin:$PATH"
   ```
   Then reload your shell: `source ~/.bashrc` (or `source ~/.zshrc`)

## Usage

### Basic Usage

**System-wide installation (recommended):**
```bash
sudo python3 update-cursor.py
```

**User-only installation (no sudo required):**
```bash
python3 update-cursor.py
```

### What the Script Does

1. **Version Information Update**:
   - Runs `update-cursor-links.ts` to fetch latest Cursor download links
   - Updates `version-history.json` with latest version information
   - Generates download badges and links for all platforms

2. **Version Comparison**:
   - Reads current installed version from `cursor_version.txt`
   - Compares with latest available version from `version-history.json`
   - Skips download if already up to date

3. **Download & Installation** (if update needed):
   - Downloads latest Cursor AppImage
   - Makes it executable
   - Installs to appropriate location:
     - **With sudo**: `/usr/local/bin/cursor` (system-wide)
     - **Without sudo**: `~/.local/bin/cursor` (user-only)
   - Updates desktop file for application menu
   - Updates version tracking file

4. **Progress Reporting**:
   - Shows real-time download progress
   - Displays success/failure counters
   - Provides final summary with success rate

### Installation Types

#### System-wide Installation (with sudo)
- **Location**: `/usr/local/bin/cursor`
- **Access**: Available to all users on the system
- **Desktop File**: System-wide application menu entry
- **Command**: `sudo python3 update-cursor.py`

#### User-only Installation (without sudo)
- **Location**: `~/.local/bin/cursor`
- **Access**: Available only to the current user
- **Desktop File**: User-specific application menu entry
- **Command**: `python3 update-cursor.py`
- **Note**: You may need to add `~/.local/bin` to your PATH to run `cursor` from anywhere

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
ℹ️  Running without sudo - Cursor will be installed to ~/.local/bin/
   For system-wide installation, run with sudo

⚠️  Potential installation conflicts detected:
   - Running without sudo but system-wide installation exists
   Consider using the same installation method consistently.
   Or remove the conflicting installation before proceeding.

🔍 Checking for latest Cursor version...
✅ Found Bun at: /home/aniket/.bun/bin/bun
✅ Successfully updated cursor links.
📖 Reading version history...
✅ Latest version found: 1.6.27
🔍 Found existing Cursor installations:
   System-wide: /usr/local/bin/cursor
📖 Current installed version: 1.6.27
✅ Cursor is already up to date (version 1.6.27)
   No download needed

🎉 Cursor is already up to date!
   You can launch Cursor from your applications menu or run 'cursor' from terminal

📊 Summary:
   ✅ Successful operations: 4
   ❌ Failed operations: 0
   📈 Success rate: 100.0%
```

## File Structure

```
update-cursor/
├── update-cursor.py          # Main update script
├── update-cursor-links.ts    # TypeScript script for fetching download links
├── cursor_version.txt        # Tracks current installed version
├── version-history.json      # Version information database (generated by TS script)
└── README.md                 # This file
```

## Configuration

The script automatically handles:
- **Version History**: `version-history.json` (generated by TypeScript script)
- **Installation Path**:
  - **With sudo**: `/usr/local/bin/cursor` (system-wide)
  - **Without sudo**: `~/.local/bin/cursor` (user-only)
- **Desktop File**: `~/.local/share/applications/cursor.desktop`
- **Version File**: `cursor_version.txt`

All errors are tracked in the success/failure counters and displayed in the final summary.

## Troubleshooting

### Bun Not Found
If you get "Bun is not installed or not in PATH" error:

1. **Check if Bun is installed**:
   ```bash
   ls ~/.bun/bin/bun
   ```

2. **If not installed, install Bun**:
   ```bash
   curl -fsSL https://bun.sh/install | bash
   ```

3. **If installed but not found, add to PATH** (optional):
   ```bash
   echo 'export PATH="$HOME/.bun/bin:$PATH"' >> ~/.bashrc
   source ~/.bashrc
   ```

### Permission Issues
- **With sudo**: Ensure the script runs as the original user for file operations
- **Without sudo**: The script automatically uses user-specific directories

### Installation Conflicts
**Important**: Avoid mixing installation methods to prevent conflicts:

- **Conflicting installations**: The script will warn if both system-wide (`/usr/local/bin/cursor`) and user-specific (`~/.local/bin/cursor`) installations exist

**If you need to switch installation methods**:
1. Remove the old installation first
2. Then run the script with the new method

### TypeScript Script Fails
- Check internet connection (script fetches data from Cursor API)
- Verify `update-cursor-links.ts` exists in the script directory
- Check Bun installation and permissions

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
