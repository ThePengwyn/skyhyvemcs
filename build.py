import platform

class PlatformError(Exception):

    def __init__(self, error_message, *args, **kwargs):
        self.error_message = error_message

    def __str__(self):
        return

def main():

    system = platform.system()
    if system == "Linux":
        from .build.debian.build import build
    elif system == "Darwin":
        from .build.osx.build import build
    else:
        raise PlatformError("The Platform: '" + system + "' is not Supported. Supported Platforms are: 'Linux' or 'Darwin/OSX'")

    build()

if __name__ == "__main__":
    main()
