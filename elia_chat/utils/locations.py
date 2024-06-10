from pathlib import Path
from xdg_base_dirs import xdg_config_home, xdg_data_home

def _elia_directory(root: Path) -> Path:
    directory = root / "elia"
    directory.mkdir(exist_ok=True, parents=True)
    return directory

def elia_chat_root() -> Path:
    """Return the root path of the `elia_chat` directory."""
    return Path(__file__).parent.parent

def config_directory() -> Path:
    """Return (possibly creating) the application config directory."""
    return _elia_directory(xdg_config_home())

def config_file() -> Path:
    return config_directory() / "config.toml"
