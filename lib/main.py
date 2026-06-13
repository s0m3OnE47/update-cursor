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
import pwd
import platform
import shlex
from datetime import date

def get_effective_user():
    """Return (username, home_path) for the user whose config should be updated."""
    sudo_user = os.environ.get('SUDO_USER')
    if sudo_user:
        try:
            info = pwd.getpwnam(sudo_user)
            return sudo_user, Path(info.pw_dir)
        except KeyError:
            pass
    info = pwd.getpwuid(os.getuid())
    return info.pw_name, Path(info.pw_dir)

def find_cursor_installation():
    """Return the path to the cursor binary if installed, otherwise None."""
    _, home_path = get_effective_user()
    system_cursor = Path('/usr/local/bin/cursor')
    user_cursor = home_path / '.local/bin/cursor'
    if system_cursor.exists():
        return system_cursor
    if user_cursor.exists():
        return user_cursor
    return None

def _should_write_as_user(username):
    """True when running as root via sudo and target is a regular user."""
    return os.geteuid() == 0 and username and os.environ.get('SUDO_USER') == username

def write_text_as_user(file_path, content, username):
    """Write a text file, using the target user's permissions when invoked via sudo."""
    file_path = Path(file_path)
    if _should_write_as_user(username):
        parent = shlex.quote(str(file_path.parent))
        target = shlex.quote(str(file_path))
        run_command(f"sudo -u {username} mkdir -p {parent}", check=True)
        result = subprocess.run(
            ['sudo', '-u', username, 'bash', '-c', f'cat > {target}'],
            input=content,
            text=True,
            capture_output=True,
            check=False,
        )
        if result.returncode != 0:
            raise OSError(result.stderr.strip() or f"Failed to write {file_path} as {username}")
    else:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content)

def write_bytes_as_user(file_path, data, username):
    """Write a binary file, using the target user's permissions when invoked via sudo."""
    file_path = Path(file_path)
    if _should_write_as_user(username):
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(data)
            tmp_path = tmp.name
        os.chmod(tmp_path, 0o644)
        try:
            parent = shlex.quote(str(file_path.parent))
            target = shlex.quote(str(file_path))
            src = shlex.quote(tmp_path)
            run_command(f"sudo -u {username} mkdir -p {parent}", check=True)
            run_command(f"sudo -u {username} cp {src} {target}", check=True)
        finally:
            os.unlink(tmp_path)
    else:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_bytes(data)

def print_help():
    """Print CLI usage information"""
    help_text = (
        "Usage: update-cursor [OPTIONS]\n\n"
        "Options:\n"
        "  --no-progress-bar   Hide the download progress percentage output.\n"
        "  -h, --help          Show this help message and exit.\n\n"
        "Description:\n"
        "  Downloads and installs the latest Cursor AppImage for Linux.\n"
        "  Automatically detects x64 or ARM64 architecture.\n"
        "  With sudo: installs to /usr/local/bin/cursor.\n"
        "  Without sudo: installs to ~/.local/bin/cursor.\n"
    )
    print(help_text)

def get_linux_platform():
    """Detect the appropriate Linux download platform for this system."""
    machine = platform.machine().lower()
    if machine in ('aarch64', 'arm64'):
        return 'linux-arm64', 'ARM64'
    if machine in ('x86_64', 'amd64', 'i686', 'i386'):
        return 'linux-x64', 'x64'
    print(f"⚠️  Unknown architecture '{machine}', defaulting to x64")
    return 'linux-x64', 'x64'

def fetch_latest_from_cursor_api(linux_platform):
    """Fetch the latest Cursor download URL directly from the Cursor API."""
    api_url = f"https://cursor.com/api/download?platform={linux_platform}&releaseTrack=latest"
    print(f"🌐 Fetching latest version from Cursor API ({linux_platform})...")
    response = requests.get(
        api_url,
        headers={'User-Agent': 'Cursor-Version-Checker', 'Cache-Control': 'no-cache'},
        timeout=30,
    )
    response.raise_for_status()
    data = response.json()
    download_url = data.get('downloadUrl')
    version = data.get('version')
    if not download_url or not version:
        raise ValueError("Cursor API response missing downloadUrl or version")
    return download_url, version

def save_version_history_entry(version_file, version_string, download_url, linux_platform):
    """Persist a version entry fetched via API fallback."""
    history = {"versions": []}
    if version_file.exists():
        try:
            with open(version_file, 'r') as f:
                history = json.load(f)
        except (json.JSONDecodeError, OSError):
            history = {"versions": []}

    platforms = {linux_platform: download_url}
    for entry in history.get('versions', []):
        if entry.get('version') == version_string:
            entry.setdefault('platforms', {})[linux_platform] = download_url
            break
    else:
        history.setdefault('versions', []).append({
            'version': version_string,
            'date': date.today().isoformat(),
            'platforms': platforms,
        })

    version_file.parent.mkdir(parents=True, exist_ok=True)
    with open(version_file, 'w') as f:
        json.dump(history, f, indent=2)

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

def download_cursor_appimage(successful_checks=0, failed_checks=0, no_progress_bar=False):
    """Download the latest Cursor AppImage from local repository"""
    print("🔍 Checking for latest Cursor version...")

    # Check if TypeScript file exists
    # Try multiple approaches to find the script directory
    script_dir = None
    ts_file = None

    # Method 1: Use __file__ if available and valid
    if '__file__' in globals() and __file__:
        potential_dir = Path(__file__).parent.absolute()
        potential_ts = potential_dir / "update-cursor-links.ts"
        if potential_ts.exists():
            script_dir = potential_dir
            ts_file = potential_ts

    # Method 2: Check current working directory
    if not ts_file:
        potential_dir = Path.cwd()
        potential_ts = potential_dir / "update-cursor-links.ts"
        if potential_ts.exists():
            script_dir = potential_dir
            ts_file = potential_ts

    # Method 3: Check the known installation directory
    if not ts_file:
        potential_dir = Path("/opt/update-cursor")
        potential_ts = potential_dir / "updater" / "fetch_updates.ts"
        if potential_ts.exists():
            script_dir = potential_dir
            ts_file = potential_ts

    if not ts_file or not ts_file.exists():
        print(f"❌ TypeScript file not found: update-cursor-links.ts")
        print(f"   Checked directories:")
        if '__file__' in globals() and __file__:
            print(f"   - {Path(__file__).parent.absolute()}")
        print(f"   - {Path.cwd()}")
        print(f"   - /opt/update-cursor")
        failed_checks += 1
        return None, "0.0.0", successful_checks, failed_checks

    # Check if Bun is available (check user-specific installation first)
    # Get list of users with valid shells
    users_result = run_command("grep -E '/(bash|sh|zsh|fish|ksh|tcsh|csh)$' /etc/passwd | cut -d: -f1 | sort", check=False)
    bun_path = None
    user_home = None

    if users_result.returncode == 0 and users_result.stdout:
        users = [user.strip() for user in users_result.stdout.strip().split('\n') if user.strip()]
        print(f"🔍 Checking for Bun in {len(users)} user(s)...")

        # Check each user's home directory for bun
        for username in users:
            try:
                user_info = pwd.getpwnam(username)
                home_dir = user_info.pw_dir
                potential_bun = Path(home_dir) / '.bun' / 'bin' / 'bun'

                if potential_bun.exists():
                    bun_path = str(potential_bun)
                    user_home = home_dir
                    print(f"✅ Found Bun at: {bun_path} (user: {username})")
                    break
            except (KeyError, PermissionError) as e:
                # User might not exist or we don't have permission
                continue

    # If no user-specific Bun found, fallback to system PATH
    if not bun_path:
        bun_check = run_command("which bun", check=False)
        if bun_check.returncode != 0:
            print("❌ Bun is not installed or not in PATH")
            print("   Please install Bun: curl -fsSL https://bun.sh/install | bash")
            failed_checks += 1
            return None, "0.0.0", successful_checks, failed_checks
        else:
            bun_path = "bun"  # Use system bun
            print(f"✅ Found Bun in system PATH: {bun_path}")

    # Ensure data directory exists before running TypeScript script
    data_dir = script_dir / "data"
    if not data_dir.exists():
        print(f"📁 Creating data directory: {data_dir}")
        try:
            data_dir.mkdir(parents=True, exist_ok=True)
            print("✅ Data directory created")
        except Exception as e:
            print(f"❌ Failed to create data directory: {e}")
            failed_checks += 1
            return None, "0.0.0", successful_checks, failed_checks

    # When running with sudo, ensure the original user can write to data/
    original_user = os.environ.get('SUDO_USER')
    if original_user and os.geteuid() == 0:
        run_command(f"chown -R {original_user} {data_dir}", check=False)

    linux_platform, arch_label = get_linux_platform()
    print(f"🖥️  Detected architecture: {arch_label} ({linux_platform})")
    if original_user:
        # When running with sudo, execute as the original user
        result = run_command(f"sudo -u {original_user} bash -c 'cd {script_dir} && {bun_path} updater/fetch_updates.ts'", check=False)
    else:
        # When running as normal user, execute directly
        result = run_command(f"cd {script_dir} && {bun_path} updater/fetch_updates.ts", check=False)

    if result.returncode == 0:
        print("✅ Successfully updated cursor links.")
        successful_checks += 1
    else:
        print(f"⚠️  Failed to update cursor links (exit code: {result.returncode}), will try API fallback if needed")
        if hasattr(result, 'stderr') and result.stderr:
            print(f"Error output: {result.stderr}")
        if hasattr(result, 'stdout') and result.stdout:
            print(f"Output: {result.stdout}")
        failed_checks += 1

    # Define version file path (version-history.json created by the TypeScript script)
    version_file = script_dir / "data" / "version-history.json"

    print("📖 Reading version history...")

    try:
        version_data = {"versions": []}
        if version_file.exists():
            with open(version_file, 'r') as f:
                version_data = json.load(f)
            successful_checks += 1
        else:
            print(f"⚠️  Version file not found: {version_file}")

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

        # Fallback to Cursor API when version history is empty (first-time install)
        if not latest_version_info:
            print("⚠️  No valid versions in version history, trying Cursor API...")
            try:
                download_url, version_string = fetch_latest_from_cursor_api(linux_platform)
                save_version_history_entry(version_file, version_string, download_url, linux_platform)
                latest_version_info = {
                    'version': version_string,
                    'platforms': {linux_platform: download_url},
                }
                latest_version = [int(x) for x in version_string.split('.')]
                print(f"✅ Latest version from API: {version_string}")
                successful_checks += 1
            except Exception as e:
                print(f"❌ No valid versions found in version history and API fallback failed: {e}")
                failed_checks += 1
                sys.exit(1)

        version_string = '.'.join(map(str, latest_version))
        print(f"✅ Latest version found: {version_string}")
        successful_checks += 1

        # Check if we need to download (compare with current version)
        if not find_cursor_installation():
            print("📝 Cursor is not installed, downloading latest version...")
            successful_checks += 1
        else:
            current_version = get_current_version()
            if not compare_versions(current_version, version_string):
                print(f"✅ Cursor is already up to date (version {current_version})")
                print("   No download needed")
                successful_checks += 1
                return None, version_string, successful_checks, failed_checks
            print("📥 Cursor is not up to date, downloading latest version...")
            successful_checks += 1
        # Get the AppImage URL for the detected architecture
        platforms = latest_version_info.get('platforms', {})
        appimage_url = platforms.get(linux_platform)

        if not appimage_url:
            print(f"⚠️  {linux_platform} AppImage not found in version history, trying Cursor API...")
            try:
                appimage_url, api_version = fetch_latest_from_cursor_api(linux_platform)
                version_string = api_version
                save_version_history_entry(version_file, version_string, appimage_url, linux_platform)
                successful_checks += 1
            except Exception as e:
                print(f"❌ {linux_platform} AppImage not found and API fallback failed: {e}")
                failed_checks += 1
                sys.exit(1)

        print(f"📦 Downloading Cursor {version_string} ({arch_label})")
        successful_checks += 1

        # Download the AppImage
        with tempfile.NamedTemporaryFile(delete=False, suffix='.AppImage') as temp_file:
            response = requests.get(appimage_url, stream=True)
            response.raise_for_status()

            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0

            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    temp_file.write(chunk)
                    downloaded += len(chunk)
                    if not no_progress_bar and total_size > 0:
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
            print(f"   Or add {local_bin} to your PATH to run 'cursor --no-sandbox' from anywhere")
            successful_checks += 1
        except Exception as e:
            print(f"❌ Failed to install Cursor: {e}")
            failed_checks += 1

    return successful_checks, failed_checks

CURSOR_ICON_URL = "https://cursor.com/marketing-static/icon-512x512.png"

def download_cursor_icon(home_path, username):
    """
    Download Cursor icon only if missing; save to:
    - User: ~/.local/share/icons/cursor/cursor.png (for normal user run)
    - System: /usr/share/pixmaps/cursor.png (when running with sudo, for system-wide)
    Returns the path to the user icon for use in the desktop file, or None on failure.
    """
    user_icon_dir = home_path / ".local/share/icons/cursor"
    user_icon_path = user_icon_dir / "cursor.png"
    system_icon_path = Path("/usr/share/pixmaps/cursor.png")

    user_needs = not user_icon_path.exists()
    system_needs = os.geteuid() == 0 and not system_icon_path.exists()

    if not user_needs and not system_needs:
        return str(user_icon_path)

    if user_icon_path.exists():
        data = user_icon_path.read_bytes()
    else:
        try:
            resp = requests.get(CURSOR_ICON_URL, timeout=30)
            resp.raise_for_status()
            data = resp.content
        except Exception as e:
            print(f"⚠️  Failed to download Cursor icon: {e}")
            return None

    if user_needs:
        try:
            write_bytes_as_user(user_icon_path, data, username)
            print(f"✅ Cursor icon saved to {user_icon_path}")
        except Exception as e:
            print(f"⚠️  Failed to save user icon: {e}")
            return None

    if system_needs:
        try:
            system_icon_path.write_bytes(data)
            print(f"✅ Cursor icon saved for system-wide use: {system_icon_path}")
        except Exception as e:
            print(f"⚠️  Failed to save system icon: {e}")

    return str(user_icon_path)

def update_desktop_file(successful_checks=0, failed_checks=0):
    """Update the desktop file with correct Exec path"""
    username, home_path = get_effective_user()
    desktop_file = home_path / '.local/share/applications/cursor.desktop'

    # Download icon for user (~/.local/share/icons/cursor/cursor.png) and optionally system (/usr/share/pixmaps)
    icon_path = download_cursor_icon(home_path, username)
    icon_value = icon_path if icon_path else "cursor"

    # Determine the correct exec path based on actual installation locations
    # Check which installation exists and prioritize accordingly
    system_cursor = Path('/usr/local/bin/cursor')
    user_cursor = home_path / '.local/bin/cursor'

    # Determine exec path based on installation priority
    exec_path = None
    if system_cursor.exists():
        # System-wide installation exists, use it
        exec_path = "/usr/local/bin/cursor"
        print(f"📱 Desktop file will point to system-wide installation: {exec_path}")
    elif user_cursor.exists():
        # User installation exists, use it
        exec_path = str(user_cursor)
        print(f"📱 Desktop file will point to user installation: {exec_path}")
    else:
        # No installation found, fall back to sudo-based logic
        is_sudo = os.geteuid() == 0
        if is_sudo:
            exec_path = "/usr/local/bin/cursor"
        else:
            exec_path = str(home_path / '.local' / 'bin' / 'cursor')
        print(f"📱 No existing installation found, using default path: {exec_path}")

    desktop_content = f"""[Desktop Entry]
Version=1.0
Type=Application
Name=Cursor
Comment=The AI-first code editor
Exec={exec_path} %U --no-sandbox
Icon={icon_value}
Terminal=false
Categories=Development;TextEditor;
StartupWMClass=cursor
"""

    if not desktop_file.exists():
        print("⚠️  Desktop file not found, creating one...")
        try:
            write_text_as_user(desktop_file, desktop_content, username)
            print("✅ Desktop file created")
            successful_checks += 1
        except Exception as e:
            print(f"❌ Failed to create desktop file: {e}")
            failed_checks += 1
    else:
        print("📝 Updating existing desktop file...")
        try:
            try:
                content = desktop_file.read_text()
            except PermissionError:
                if _should_write_as_user(username):
                    content = desktop_content
                else:
                    raise

            new_exec_line = f"Exec={exec_path} %U --no-sandbox"
            pattern = r'Exec=.*'
            if re.search(pattern, content):
                content = re.sub(pattern, new_exec_line, content)
            else:
                content += f"\n{new_exec_line}\n"

            icon_pattern = r'Icon=.*'
            if re.search(icon_pattern, content):
                content = re.sub(icon_pattern, f'Icon={icon_value}', content)
            else:
                content += f"\nIcon={icon_value}\n"

            write_text_as_user(desktop_file, content, username)
            print("✅ Desktop file updated")
            successful_checks += 1
        except PermissionError:
            print("❌ Failed to update desktop file: permission denied")
            print("   If you previously ran with sudo, try running: sudo update-cursor")
            failed_checks += 1
        except Exception as e:
            print(f"❌ Failed to update desktop file: {e}")
            failed_checks += 1

    return successful_checks, failed_checks

def check_installation_conflicts():
    """Check for potential conflicts between different installation types"""
    _, home_path = get_effective_user()

    system_cursor = Path('/usr/local/bin/cursor')
    user_cursor = home_path / '.local/bin/cursor'

    conflicts = []

    # Check if both installations exist
    if system_cursor.exists() and user_cursor.exists():
        conflicts.append("Both system-wide and user-specific installations found")

    # Check if running with sudo but user installation exists
    if os.geteuid() == 0 and user_cursor.exists():
        conflicts.append("Running with sudo but user-specific installation exists")

    # Check if running without sudo but system installation exists
    if os.geteuid() != 0 and system_cursor.exists():
        conflicts.append("Running without sudo but system-wide installation exists")

    if conflicts:
        print("⚠️  Potential installation conflicts detected:")
        for conflict in conflicts:
            print(f"   - {conflict}")
        print("   Consider using the same installation method consistently.")
        print("   Or remove the conflicting installation before proceeding.\n")
        return True

    return False

def get_current_version():
    """Get the installed Cursor version, only if the binary is present."""
    install_path = find_cursor_installation()
    if not install_path:
        return None

    _, home_path = get_effective_user()
    print(f"🔍 Found Cursor installation: {install_path}")

    # Prefer version file next to the installed binary
    version_files = [
        home_path / '.local' / 'bin' / 'cursor_version.txt',
        Path("/opt/update-cursor/config/version.txt"),
        Path.cwd() / 'cursor_version.txt',
    ]

    for vf in version_files:
        if vf.exists():
            try:
                current_version = vf.read_text().strip()
                print(f"📖 Current installed version: {current_version}")
                return current_version
            except Exception as e:
                print(f"⚠️  Warning: Could not read version file {vf}: {e}")

    print("📝 No version file found, will download latest version")
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

    username, home_path = get_effective_user()

    # Primary version file location: /opt/update-cursor
    primary_version_file = Path("/opt/update-cursor/config/version.txt")

    try:
        # Create the directory if it doesn't exist
        primary_version_file.parent.mkdir(parents=True, exist_ok=True)

        # Write the version to the primary file
        primary_version_file.write_text(version)
        print(f"✅ Version file updated: {primary_version_file}")
        successful_checks += 1

    except Exception as e:
        print(f"⚠️  Warning: Could not update primary version file: {e}")
        failed_checks += 1

    # Also update version file in user's .local/bin for backward compatibility
    user_version_file = home_path / '.local' / 'bin' / 'cursor_version.txt'

    try:
        write_text_as_user(user_version_file, version, username)
        print(f"✅ User version file updated: {user_version_file}")
        successful_checks += 1

    except Exception as e:
        print(f"⚠️  Warning: Could not update user version file: {e}")
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

    # Parse CLI flags
    args = sys.argv[1:]
    if ('--help' in args) or ('-h' in args):
        print_help()
        return
    no_progress_bar = ('--no-progress-bar' in args) or ('no-progress-bar' in args)

    # Initialize counters
    successful_checks = 0
    failed_checks = 0

    # Check if running as root for system-wide installation
    if os.geteuid() != 0:
        print("ℹ️  Running without sudo - Cursor will be installed to ~/.local/bin/")
        print("   For system-wide installation, run with sudo\n")

    # Check for installation conflicts
    check_installation_conflicts()

    try:
        # Step 1: Download Cursor AppImage (if needed)
        result = download_cursor_appimage(successful_checks, failed_checks, no_progress_bar=no_progress_bar)
        if len(result) == 4:
            appimage_path, version, successful_checks, failed_checks = result
        else:
            appimage_path, version = result

        if appimage_path is None:
            # No download needed or prerequisites missing
            if version == "0.0.0":
                print("\n❌ Cannot proceed due to missing prerequisites.")
                print("   Please install Bun and try again.")
            elif not find_cursor_installation():
                print("\n❌ Cursor is not installed.")
                print("   Re-run the script to download and install Cursor.")
            else:
                print("\n🎉 Cursor is already up to date!")
                print("   You can launch Cursor from your applications menu or run 'cursor' from terminal")
        else:
            # Step 2: Make it executable
            successful_checks, failed_checks = make_executable(appimage_path, successful_checks, failed_checks)

            # Step 3: Install to /usr/local/bin/cursor
            successful_checks, failed_checks = install_cursor(appimage_path, successful_checks, failed_checks)

            # Step 4: Update version number in cursor_version.txt file
            successful_checks, failed_checks = update_version_file(str(version), successful_checks, failed_checks)

            print("✅ Updated Cursor successfully!")
            print("\n🎉 Cursor update completed successfully!")
            print("   You can now launch Cursor from your applications menu or run 'cursor' from terminal")

        # Always ensure desktop file and icon (even when no Cursor update was needed)
        if version != "0.0.0":
            successful_checks, failed_checks = update_desktop_file(successful_checks, failed_checks)

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
