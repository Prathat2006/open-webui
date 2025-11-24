import webview
import subprocess
import os
import signal
import threading
import time
import sys
import secrets

# New imports for system tray functionality
from pystray import MenuItem as item
import pystray
from PIL import Image, ImageDraw

# Global variables to hold the window and server process
server_process = None
window = None

def create_image():
    """Load the favicon image for the system tray."""
    try:
        script_dir = get_script_directory()
        # Assuming the script is in 'backend', construct the path to the favicon
        icon_path = os.path.join(script_dir, 'open_webui', 'frontend', 'build', 'favicon.png')
        image = Image.open(icon_path)
        return image
    except FileNotFoundError:
        print(f"Icon not found at {icon_path}, using a default icon.")
        # Fallback to creating a generic icon if the file is not found
        image = Image.new('RGB', (64, 64), 'black')
        dc = ImageDraw.Draw(image)
        dc.rectangle((32, 0, 64, 32), fill='white')
        dc.rectangle((0, 32, 32, 64), fill='white')
        return image

def get_script_directory():
    """Gets the directory where the script is located."""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(os.path.abspath(__file__))

def run_command(command, script_dir):
    """Runs a command and waits for it to complete."""
    print(f"Running setup command: {' '.join(command)}")
    try:
        # Using shell=True for commands like playwright that might be in the path
        subprocess.run(command, cwd=script_dir, check=True, shell=True)
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"Error running command: {' '.join(command)}\n{e}")
        # sys.exit(1) 

def start_server(script_dir):
    """Sets up the environment and starts the uvicorn server."""
    global server_process

    # --- Logic from start_windows.bat is now in Python ---

    # 1. Set environment variables with defaults
    os.environ.setdefault('PORT', '8080')
    os.environ.setdefault('HOST', '0.0.0.0')
    os.environ.setdefault('UVICORN_WORKERS', '1')

    # 2. Handle conditional Playwright installation
    if os.environ.get("WEB_LOADER_ENGINE", "").lower() == "playwright":
        if not os.environ.get("PLAYwright_WS_URL"):
            print("Installing Playwright browsers...")
            run_command(['playwright', 'install', 'chromium'], script_dir)
            run_command(['playwright', 'install-deps', 'chromium'], script_dir)
        
        # Ensure we use the correct python executable for the nltk command
        run_command([sys.executable, '-c', "import nltk; nltk.download('punkt_tab')"], script_dir)

    # 3. Handle WEBUI_SECRET_KEY generation
    if not os.environ.get('WEBUI_SECRET_KEY') and not os.environ.get('WEBUI_JWT_SECRET_KEY'):
        key_file_path = os.environ.get('WEBUI_SECRET_KEY_FILE', os.path.join(script_dir, '.webui_secret_key'))
        
        if not os.path.exists(key_file_path):
            print("Generating new WEBUI_SECRET_KEY")
            with open(key_file_path, 'w') as f:
                f.write(secrets.token_hex(16))
            print("WEBUI_SECRET_KEY generated in", key_file_path)

        print("Loading WEBUI_SECRET_KEY from", key_file_path)
        with open(key_file_path, 'r') as f:
            os.environ['WEBUI_SECRET_KEY'] = f.read().strip()

    # 4. Construct and run the Uvicorn server command
    command = [
        sys.executable,
        '-m', 'uvicorn',
        'open_webui.main:app',
        '--host', os.environ['HOST'],
        '--port', os.environ['PORT'],
        '--workers', os.environ['UVICORN_WORKERS'],
        '--forwarded-allow-ips=*',  # Combined flag and value to prevent wildcard expansion
        '--ws', 'auto'
    ]

    print(f"Starting server with command: {' '.join(command)}")
    
    server_process = subprocess.Popen(
        command,
        cwd=script_dir,
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
    )
    print(f"Server process started with PID: {server_process.pid}")


def stop_server():
    """Stops the server process when the window is closed."""
    global server_process
    if server_process:
        print(f"Stopping server process PID: {server_process.pid}")
        try:
            # CTRL_BREAK_EVENT is specific to Windows and good for console apps
            os.kill(server_process.pid, signal.CTRL_BREAK_EVENT)
        except OSError as e:
            print(f"Could not terminate server process: {e}")
        server_process = None
        print("Server process stopped.")

# --- New functions for System Tray ---

def show_window(icon, menu_item):
    """Show the main window when selected from the tray menu."""
    icon.stop()
    if window:
        window.show()

def exit_app(icon, menu_item):
    """Signals the application to exit cleanly from the system tray."""
    print("Exit requested from system tray. Shutting down...")
    if window:
        window.destroy()  # This safely signals the main thread to start shutdown
    icon.stop() # This will stop the tray icon's thread

def run_tray_icon():
    """Set up and run the system tray icon and its menu."""
    image = create_image()
    menu = (item('Show', show_window, default=True), item('Exit', exit_app))
    icon = pystray.Icon("Open WebUI", image, "Open WebUI", menu)
    icon.run()

def on_closing():
    """Intercept the window close event."""
    if window:
        window.hide()
    # Run the tray icon in a separate thread
    tray_thread = threading.Thread(target=run_tray_icon)
    tray_thread.daemon = True
    tray_thread.start()
    return False # Prevent the default closing behavior

if __name__ == '__main__':
    script_directory = get_script_directory()

    # The server setup and launch is now handled in a single function
    server_thread = threading.Thread(target=start_server, args=(script_directory,))
    server_thread.daemon = True
    server_thread.start()

    print("Waiting 5 seconds for the server to start...")
    time.sleep(5)
    print("Server should be running. Creating GUI window.")

    window = webview.create_window(
        'Open WebUI',
        f"http://127.000.1:{os.environ.get('PORT', 8080)}",
        width=1280,
        height=800
    )

    # Attach event handlers
    window.events.closing += on_closing # New handler for the 'X' button
    window.events.closed += stop_server   # This is the single shutdown point
    
    webview.start()

