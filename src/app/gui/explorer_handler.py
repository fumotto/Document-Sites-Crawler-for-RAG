import subprocess
import sys

from src.app.gui.user_paths import get_output_root


class Explorer_handler:
    def open_output_directory(self, path):
        dir_name = ""
        match sys.platform:
            case "win32":
                dir_name = "explorer"
            case "linux":
                dir_name = "xdg-open"
            case "darwin":
                dir_name = "open"

        subprocess.Popen([dir_name, get_output_root()])
        return True
