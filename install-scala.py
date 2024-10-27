import os
import platform
import subprocess
import urllib.request
import gzip
import shutil
import zipfile
import sys

try:
    from rich.console import Console
except:
    question = input("Python requires the rich library to install scala3, continue with rich install? [y/n]")
    if question.lower().strip().startswith("n") == True or question.lower().strip() == "":
        print("Exiting")
        sys.exit()
        
    if platform.system() == "Windows":
        subprocess.run(["pip", "install", "rich"])
    else:
        subprocess.run(["pip3",  "install",  "rich"])
finally:
    from rich.console import Console
    from rich.status import Status


console = Console()


def darwin_installation(status:Status):
    """Sets up Coursier for macOS based on architecture (Apple Silicon or Intel)."""
    arch = platform.machine()
    cs_path = "cs"

    if arch == "arm64":  # Apple Silicon (M1, M2, etc.)
        status.update("Detected Apple Silicon architecture. Downloading Coursier for ARM (M1, M2).")
        url = "https://github.com/VirtusLab/coursier-m1/releases/latest/download/cs-aarch64-apple-darwin.gz"
    elif arch == "x86_64":  # Intel x86_64 architecture
        status.update("Detected Intel x86_64 architecture. Downloading Coursier for x86_64.")
        url = "https://github.com/coursier/coursier/releases/latest/download/cs-x86_64-apple-darwin.gz"
    else:
        print(f"Unsupported architecture for macOS: {arch}")
        return False
    
    status.update("opening URL object...")
    
    with urllib.request.urlopen(url) as response:
        
        status.update(f"Reading compressed file {url}")
        
        with gzip.open(response, 'rb') as compressed_file:
            
            status.update(f"decompressing {cs_path}")
            
            with open(cs_path, 'wb') as outfile:
                shutil.copyfileobj(compressed_file, outfile)
    
    status.update(f"changing file permissions for {cs_path}")

    os.chmod(cs_path, 0o755)
    try:
        subprocess.run(["xattr", "-d", "com.apple.quarantine", cs_path], check=True)
    except subprocess.CalledProcessError:
        print("Failed to remove com.apple.quarantine attribute. Continuing...")

    status.update("Running cs setup...")
    subprocess.run(["./cs", "setup"], check=True)
    
    return verify_cs_path()

def linux_installation(status:Status):
    """Sets up Coursier for Linux based on architecture (x86_64 or ARM)."""
    arch = platform.machine()
    cs_path = "cs"

    if arch == "x86_64":
        status.update("Detected Linux x86_64 architecture. Downloading Coursier for x86_64.")
        url = "https://github.com/coursier/coursier/releases/latest/download/cs-x86_64-pc-linux.gz"
    elif arch == "aarch64":
        status.update("Detected Linux ARM architecture. Downloading Coursier for ARM.")
        url = "https://github.com/VirtusLab/coursier-m1/releases/latest/download/cs-aarch64-pc-linux.gz"
    else:
        print(f"Unsupported architecture: {arch}")
        return False

    with urllib.request.urlopen(url) as response:
        status.update(f"Reading compressed file {url}")
        with gzip.open(response, 'rb') as compressed_file:
            status.update(f"decompressing {cs_path}")
            with open(cs_path, 'wb') as outfile:
                shutil.copyfileobj(compressed_file, outfile)

    status.update(f"changing file permissions for {cs_path}")
    os.chmod(cs_path, 0o755)
    
    status.update("Running cs setup...")
    subprocess.run(["yes", "|", f"./{cs_path}", "setup"], shell=True)
    return verify_cs_path()

def windows_installation(status:Status):
    """Sets up Coursier for Windows (x86_64 only)."""
    arch = platform.machine()

    if arch != "AMD64":
        print(f"Unsupported architecture for Windows: {arch}")
        return False

    status.update("Detected Windows x86_64 architecture. Downloading Coursier for Windows.")
    url = "https://github.com/coursier/coursier/releases/latest/download/cs-x86_64-pc-win32.zip"
    cs_path = "cs.exe"
    zip_path = "cs.zip"

    with urllib.request.urlopen(url) as response:
        with open(zip_path, "wb") as outfile:
            outfile.write(response.read())

    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall()
    os.remove(zip_path)

    subprocess.run([cs_path, "setup"], shell=True)
    return verify_cs_path(cs_path)

def verify_cs_path(cs_executable="cs"):
    """Verify that cs or cs.exe is in PATH and executable."""
    try:
        result = subprocess.run([cs_executable, "setup"], check=True, capture_output=True, text=True)
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print("Error: Coursier setup failed:", e.stderr)
        return False
    except FileNotFoundError:
        print("Error: Coursier executable not found.")
        return False

def add_scala_to_path():
    """Add Scala to PATH if it is installed in the default coursier location."""
    scala_bin_path = os.path.expanduser("~/.local/share/coursier/bin")
    if platform.system() == "Windows":
        scala_bin_path = os.path.expanduser("~\\AppData\\Local\\Coursier\\bin")

    if scala_bin_path not in os.environ["PATH"]:
        os.environ["PATH"] += os.pathsep + scala_bin_path
        print(f"Added Scala to PATH: {scala_bin_path}")

    return scala_bin_path

def check_scala_availability():
    """Check if Scala is available in the system PATH."""
    try:
        subprocess.run(["scala", "-version"], check=True)
        print("Scala is installed and available.")
    except subprocess.CalledProcessError:
        print("Scala is installed but not configured correctly.")
        scala_path = add_scala_to_path()
        try:
            subprocess.run(["scala", "-version"], check=True)
            print("Scala is now available in the PATH.")
        except FileNotFoundError:
            print("Error: Scala was not found after PATH update. Please check the installation.")
    except FileNotFoundError:
        print("Error: Scala is not installed or not found in the PATH.")

def is_scala_installed():
    """Check if Scala is installed on the system."""
    try:
        # Attempt to run 'scala -version' to check for installation
        result = subprocess.run(["scala", "-version"], check=True, capture_output=True, text=True)
        print("Scala is installed.")
        print(result.stdout)  # Print the version information
        return True
    except subprocess.CalledProcessError:
        print("Scala is not installed or not found in the PATH.")
        return False
    except FileNotFoundError:
        print("'scala' command not found. Scala is not installed.")
        return False
    
def main():
    with Status("Checking scala installation...") as status:
        if is_scala_installed() == True:
            sys.exit()
            
        status.update("Scala not detected, installing scala3")
        os_type = platform.system()
        success = False
        
        if os_type == "Darwin":
            status.update("installing for MacOS")
            success = darwin_installation(status)
        
        elif os_type == "Linux":
            status.update("Installing for Linux")
            success = linux_installation(status)
        
        elif os_type == "Windows":
            status.update("installing for Windows")           
            success = windows_installation(status)
            
        else:
            print(f"Unsupported operating system: {os_type}")
            sys.exit(1)

        if success:
            status.update("Scala3 installed! checking availability")
            check_scala_availability()
        else:
            print("Installation of Coursier failed.")


if __name__ == "__main__":
    main()
