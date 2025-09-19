#!/usr/bin/env python3
"""
Cursor Update Script
Downloads and installs the latest Cursor AppImage for Linux
"""

import os
import sys
import subprocess
import requests
import shutil
import json
from pathlib import Path
import tempfile
import re

def run_command(cmd, check=True):
    """Run a shell command and return the result"""
    try:
        result = subprocess.run(cmd, shell=True, check=check, capture_output=True, text=True)
        return result
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {cmd}")
        print(f"Error: {e.stderr}")
        if check:
            sys.exit(1)
        return e

def download_cursor_appimage(successful_checks=0, failed_checks=0):
    """Download the latest Cursor AppImage from local repository"""
    print("🔍 Checking for latest Cursor version...")

    # Check if TypeScript file exists
    ts_file = Path("update-cursor-links.ts")
    if not ts_file.exists():
        print(f"❌ TypeScript file not found: {ts_file}")
        failed_checks += 1
        return None, "0.0.0", successful_checks, failed_checks

    # Check if Bun is available (check user-specific installation first)
    original_user = os.environ.get('SUDO_USER')
    if original_user:
        # When running with sudo, check in the original user's home directory
        user_home = f'/home/{original_user}'
        bun_path = f'{user_home}/.bun/bin/bun'
    else:
        # When running as normal user, check in current user's home directory
        user_home = str(Path.home())
        bun_path = f'{user_home}/.bun/bin/bun'

    # Check if user-specific Bun exists
    if not Path(bun_path).exists():
        # Fallback to system PATH
        bun_check = run_command("which bun", check=False)
        if bun_check.returncode != 0:
            print("❌ Bun is not installed or not in PATH")
            print("   Please install Bun: curl -fsSL https://bun.sh/install | bash")
            print(f"   Expected location: {bun_path}")
            failed_checks += 1
            return None, "0.0.0", successful_checks, failed_checks
        else:
            bun_path = "bun"  # Use system bun
    else:
        print(f"✅ Found Bun at: {bun_path}")

    # Run the TypeScript update script as the original user when using sudo
    original_user = os.environ.get('SUDO_USER')
    if original_user:
        # When running with sudo, execute as the original user
        print(f"🔄 Running TypeScript script as user: {original_user}")
        result = run_command(f"sudo -u {original_user} bash -c 'cd {os.getcwd()} && {bun_path} update-cursor-links.ts'", check=False)
    else:
        # When running as normal user, execute directly
        print("🔄 Running TypeScript script as current user")
        result = run_command(f"{bun_path} update-cursor-links.ts", check=False)

    if result.returncode == 0:
        print("✅ Successfully updated cursor links.")
        successful_checks += 1
    else:
        print(f"❌ Failed to update cursor links. Exit code: {result.returncode}")
        if hasattr(result, 'stderr') and result.stderr:
            print(f"Error output: {result.stderr}")
        if hasattr(result, 'stdout') and result.stdout:
            print(f"Output: {result.stdout}")
        failed_checks += 1
        return None, "0.0.0", successful_checks, failed_checks

    # Define version file path (version-history.json created by the TypeScript script)
    version_file = Path("version-history.json")

    # Check if version file exists
    if not version_file.exists():
        print(f"❌ Version file not found: {version_file}")
        failed_checks += 1
        sys.exit(1)

    print("📖 Reading version history...")

    try:
        # Read and parse the version history
        with open(version_file, 'r') as f:
            version_data = json.load(f)
        successful_checks += 1

        # Find the latest version
        latest_version = None
        latest_version_info = None

        for version_info in version_data.get('versions', []):
            version = version_info.get('version')
            if version:
                # Parse version number for comparison
                version_parts = [int(x) for x in version.split('.')]

                if latest_version is None:
                    latest_version = version_parts
                    latest_version_info = version_info
                else:
                    # Compare version numbers
                    if version_parts > latest_version:
                        latest_version = version_parts
                        latest_version_info = version_info

        if not latest_version_info:
            print("❌ No valid versions found in version history")
            failed_checks += 1
            sys.exit(1)

        version_string = '.'.join(map(str, latest_version))
        print(f"✅ Latest version found: {version_string}")
        successful_checks += 1

        # Check if we need to download (compare with current version)
        current_version = get_current_version()
        if not compare_versions(current_version, version_string):
            print(f"✅ Cursor is already up to date (version {current_version})")
            print("   No download needed")
            successful_checks += 1
            return None, version_string, successful_checks, failed_checks
        print("📥 Cursor is not up to date, downloading latest version...")
        successful_checks += 1
        # Get the Linux x64 AppImage URL
        platforms = latest_version_info.get('platforms', {})
        linux_x64_url = platforms.get('linux-x64')

        if not linux_x64_url:
            print("❌ Linux x64 AppImage not found for latest version")
            failed_checks += 1
            sys.exit(1)

        print(f"📦 Downloading Cursor {version_string}")
        successful_checks += 1

        # Download the AppImage
        with tempfile.NamedTemporaryFile(delete=False, suffix='.AppImage') as temp_file:
            response = requests.get(linux_x64_url, stream=True)
            response.raise_for_status()

            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0

            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    temp_file.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        percent = (downloaded / total_size) * 100
                        print(f"\r📥 Downloading... {percent:.1f}%", end='', flush=True)

            print(f"\n✅ Download completed: {temp_file.name}")
            successful_checks += 1
            return temp_file.name, version_string, successful_checks, failed_checks

    except json.JSONDecodeError as e:
        print(f"❌ Error parsing version history JSON: {e}")
        failed_checks += 1
        sys.exit(1)
    except requests.RequestException as e:
        print(f"❌ Error downloading Cursor: {e}")
        failed_checks += 1
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        failed_checks += 1
        sys.exit(1)

def make_executable(file_path, successful_checks=0, failed_checks=0):
    """Make the AppImage executable"""
    print(f"🔧 Making {file_path} executable...")
    try:
        os.chmod(file_path, 0o755)
        print("✅ File is now executable")
        successful_checks += 1
    except Exception as e:
        print(f"❌ Failed to make file executable: {e}")
        failed_checks += 1
    return successful_checks, failed_checks

def install_cursor(appimage_path, successful_checks=0, failed_checks=0):
    """Install Cursor to appropriate location based on sudo usage"""
    # Check if running with sudo
    is_sudo = os.geteuid() == 0

    if is_sudo:
        install_path = '/usr/local/bin/cursor'
        print("📦 Installing Cursor to /usr/local/bin/cursor...")

        try:
            # Create directory if it doesn't exist
            os.makedirs('/usr/local/bin', exist_ok=True)

            # Move AppImage to /usr/local/bin/cursor
            shutil.move(appimage_path, install_path)
            successful_checks, failed_checks = make_executable(install_path, successful_checks, failed_checks)

            print("✅ Cursor installed successfully to system location")
            successful_checks += 1
        except Exception as e:
            print(f"❌ Failed to install Cursor: {e}")
            failed_checks += 1
    else:
        # Install to user's local bin directory
        home_path = Path.home()
        local_bin = home_path / '.local' / 'bin'
        install_path = local_bin / 'cursor'

        print(f"📦 Installing Cursor to {install_path}...")

        try:
            # Create directory if it doesn't exist
            local_bin.mkdir(parents=True, exist_ok=True)

            # Move AppImage to user's local bin
            shutil.move(appimage_path, install_path)
            successful_checks, failed_checks = make_executable(str(install_path), successful_checks, failed_checks)

            print("✅ Cursor installed successfully to user location")
            print(f"   You can run it with: {install_path}")
            print(f"   Or add {local_bin} to your PATH to run 'cursor' from anywhere")
            successful_checks += 1
        except Exception as e:
            print(f"❌ Failed to install Cursor: {e}")
            failed_checks += 1

    return successful_checks, failed_checks

def update_desktop_file(successful_checks=0, failed_checks=0):
    """Update the desktop file with correct Exec path"""
    # Get the original user's home directory (not root when using sudo)
    original_home = os.environ.get('SUDO_USER')
    if original_home:
        # When running with sudo, get the original user's home directory
        home_path = Path(f'/home/{original_home}')
    else:
        # When running as normal user, use current user's home
        home_path = Path.home()

    desktop_file = home_path / '.local/share/applications/cursor.desktop'

    # Determine the correct exec path based on sudo usage
    is_sudo = os.geteuid() == 0
    if is_sudo:
        exec_path = "/usr/local/bin/cursor"
    else:
        exec_path = str(home_path / '.local' / 'bin' / 'cursor')

    if not desktop_file.exists():
        print("⚠️  Desktop file not found, creating one...")
        # Create the directory if it doesn't exist
        desktop_file.parent.mkdir(parents=True, exist_ok=True)

        # Create a basic desktop file
        desktop_content = f"""[Desktop Entry]
Version=1.0
Type=Application
Name=Cursor
Comment=The AI-first code editor
Exec={exec_path} %U --no-sandbox
Icon=cursor
Terminal=false
Categories=Development;TextEditor;
StartupWMClass=cursor
"""
        try:
            desktop_file.write_text(desktop_content)
            print("✅ Desktop file created")
            successful_checks += 1
        except Exception as e:
            print(f"❌ Failed to create desktop file: {e}")
            failed_checks += 1
    else:
        print("📝 Updating existing desktop file...")

        try:
            # Read the current desktop file
            content = desktop_file.read_text()

            # Update the Exec line
            new_exec_line = f"Exec={exec_path} %U --no-sandbox"

            # Replace the Exec line using regex
            pattern = r'Exec=.*'
            if re.search(pattern, content):
                content = re.sub(pattern, new_exec_line, content)
            else:
                # If no Exec line found, add it
                content += f"\n{new_exec_line}\n"

            desktop_file.write_text(content)
            print("✅ Desktop file updated")
            successful_checks += 1
        except Exception as e:
            print(f"❌ Failed to update desktop file: {e}")
            failed_checks += 1

    return successful_checks, failed_checks

def get_current_version():
    """Get the current version from cursor_version.txt file"""
    # Get the original user's home directory (not root when using sudo)
    original_home = os.environ.get('SUDO_USER')
    if original_home:
        # When running with sudo, get the original user's home directory
        home_path = Path(f'/home/{original_home}')
    else:
        # When running as normal user, use current user's home
        home_path = Path.home()

    version_file = home_path / 'Projects' / 'update-cursor' / 'cursor_version.txt'

    if not version_file.exists():
        print("📝 No existing version file found, will download latest version")
        return None

    try:
        current_version = version_file.read_text().strip()
        print(f"📖 Current installed version: {current_version}")
        return current_version
    except Exception as e:
        print(f"⚠️  Warning: Could not read version file: {e}")
        return None

def compare_versions(current_version, latest_version):
    """Compare two version strings and return True if latest is greater"""
    if not current_version:
        return True  # If no current version, always download

    try:
        # Parse version numbers for comparison
        current_parts = [int(x) for x in current_version.split('.')]
        latest_parts = [int(x) for x in latest_version.split('.')]

        # Pad with zeros to make them the same length
        max_len = max(len(current_parts), len(latest_parts))
        current_parts.extend([0] * (max_len - len(current_parts)))
        latest_parts.extend([0] * (max_len - len(latest_parts)))

        return latest_parts > current_parts
    except (ValueError, AttributeError) as e:
        print(f"⚠️  Warning: Could not compare versions: {e}")
        return True  # If comparison fails, download to be safe

def update_version_file(version, successful_checks=0, failed_checks=0):
    """Update version number in cursor_version.txt file"""
    print(f"📝 Updating version file with version: {version}")

    # Get the original user's home directory (not root when using sudo)
    original_home = os.environ.get('SUDO_USER')
    if original_home:
        # When running with sudo, get the original user's home directory
        home_path = Path(f'/home/{original_home}')
    else:
        # When running as normal user, use current user's home
        home_path = Path.home()

    version_file = home_path / 'Projects' / 'update-cursor' / 'cursor_version.txt'

    try:
        # Create the directory if it doesn't exist
        version_file.parent.mkdir(parents=True, exist_ok=True)

        # Write the version to the file
        version_file.write_text(version)
        print(f"✅ Version file updated: {version_file}")
        successful_checks += 1

    except Exception as e:
        print(f"⚠️  Warning: Could not update version file: {e}")
        failed_checks += 1

    return successful_checks, failed_checks

def cleanup_temp_file(file_path):
    """Clean up temporary file"""
    try:
        os.unlink(file_path)
        print(f"🧹 Cleaned up temporary file: {file_path}")
    except OSError:
        pass

def main():
    """Main function"""
    print("🚀 Cursor Update Script")
    print("=" * 50)

    # Initialize counters
    successful_checks = 0
    failed_checks = 0

    # Check if running as root for system-wide installation
    if os.geteuid() != 0:
        print("ℹ️  Running without sudo - Cursor will be installed to ~/.local/bin/")
        print("   For system-wide installation, run with sudo\n")

    try:
        # Step 1: Download Cursor AppImage (if needed)
        result = download_cursor_appimage(successful_checks, failed_checks)
        if len(result) == 4:
            appimage_path, version, successful_checks, failed_checks = result
        else:
            appimage_path, version = result

        if appimage_path is None:
            # No download needed or prerequisites missing
            if version == "0.0.0":
                print("\n❌ Cannot proceed due to missing prerequisites.")
                print("   Please install Bun and try again.")
            else:
                print("\n🎉 Cursor is already up to date!")
                print("   You can launch Cursor from your applications menu or run 'cursor' from terminal")
        else:
            # Step 2: Make it executable
            successful_checks, failed_checks = make_executable(appimage_path, successful_checks, failed_checks)

            # Step 3: Install to /usr/local/bin/cursor
            successful_checks, failed_checks = install_cursor(appimage_path, successful_checks, failed_checks)

            # Step 4: Update desktop file
            successful_checks, failed_checks = update_desktop_file(successful_checks, failed_checks)

            # Step 5: Update version number in cursor_version.txt file
            successful_checks, failed_checks = update_version_file(str(version), successful_checks, failed_checks)

            # Step 6: Cleanup (no longer needed since we moved the file)

            print("✅ Updated Cursor successfully!")
            print("\n🎉 Cursor update completed successfully!")
            print("   You can now launch Cursor from your applications menu or run 'cursor' from terminal")

        # Display final counters
        print(f"\n📊 Summary:")
        print(f"   ✅ Successful operations: {successful_checks}")
        print(f"   ❌ Failed operations: {failed_checks}")
        print(f"   📈 Success rate: {(successful_checks / (successful_checks + failed_checks) * 100):.1f}%" if (successful_checks + failed_checks) > 0 else "   📈 Success rate: N/A")

    except KeyboardInterrupt:
        print("\n❌ Update cancelled by user")
        print(f"\n📊 Summary:")
        print(f"   ✅ Successful operations: {successful_checks}")
        print(f"   ❌ Failed operations: {failed_checks}")
        print(f"   📈 Success rate: {(successful_checks / (successful_checks + failed_checks) * 100):.1f}%" if (successful_checks + failed_checks) > 0 else "   📈 Success rate: N/A")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ An error occurred: {e}")
        failed_checks += 1
        print(f"\n📊 Summary:")
        print(f"   ✅ Successful operations: {successful_checks}")
        print(f"   ❌ Failed operations: {failed_checks}")
        print(f"   📈 Success rate: {(successful_checks / (successful_checks + failed_checks) * 100):.1f}%" if (successful_checks + failed_checks) > 0 else "   📈 Success rate: N/A")
        sys.exit(1)

if __name__ == "__main__":
    main()