try:
    import importlib.metadata  # >=3.8
    __version__ = importlib.metadata.version(__package__ or __name__)
except ImportError:
    import importlib_metadata  # <=3.7
    __version__ = importlib_metadata.version(__package__ or __name__)
