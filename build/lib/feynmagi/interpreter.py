###########################################################################################
#
# FeynmAGI V0.1
# Imed MAGROUNE
# 2024-06
#
#########################################################################################

import subprocess
import threading
import platform
import shutil

import subprocess
import threading

import subprocess
import threading
import platform
import shutil

def execute_command(command):
    if not command:
        return {'error': 'No command provided'}, 1

    def run_command(command, results):
        try:
            # Spécifiez l'encodage explicitement pour éviter les erreurs de décodage
            result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='cp1252')
            results['output'] = result.stdout
            # Filtrer les messages d'erreur spécifiques
            error_message = result.stderr.strip()
            filtered_error = "\n".join(line for line in error_message.splitlines() if "Descripteur non valide" not in line and "failed to get console mode for stderr" not in line)
            results['error'] = filtered_error
            results['status'] = result.returncode
        except Exception as e:
            results['error'] = str(e)
            results['status'] = 1

    results = {}
    thread = threading.Thread(target=run_command, args=(command, results))
    thread.start()
    thread.join()

    return results, results.get('status', 1)
    
def execute_python(python_code):
    escaped_python_code = python_code.replace('"', '\\"')
    command = f'python -c "{escaped_python_code}"'
    response, status = execute_command(command)
    return response, status

def check_ffmpeg_installed():
    # Vérifie si ffmpeg est installé
    return shutil.which("ffmpeg") is not None

def get_platform():
    return platform.system()
    
def install_ffmpeg():
    system = platform.system()
    if system == "Linux":
        distro = platform.linux_distribution()[0].lower()
        if "debian" in distro or "ubuntu" in distro:
            print("Installing ffmpeg on Debian/Ubuntu...")
            subprocess.run("sudo apt update && sudo apt install -y ffmpeg", shell=True)
        elif "arch" in distro:
            print("Installing ffmpeg on Arch Linux...")
            subprocess.run("sudo pacman -S ffmpeg", shell=True)
        else:
            print("Unsupported Linux distribution. Please install ffmpeg manually.")
    elif system == "Darwin":
        print("Installing ffmpeg on MacOS...")
        subprocess.run("/bin/bash -c \"$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\"", shell=True)
        subprocess.run("brew install ffmpeg", shell=True)
    elif system == "Windows":
        if shutil.which("choco") is not None:
            print("Installing ffmpeg using Chocolatey...")
            subprocess.run("choco install ffmpeg -y", shell=True)
        elif shutil.which("scoop") is not None:
            print("Installing ffmpeg using Scoop...")
            subprocess.run("scoop install ffmpeg", shell=True)
        else:
            print("Please install either Chocolatey or Scoop to manage packages on Windows.")
    else:
        print("Unsupported OS. Please install ffmpeg manually.")
