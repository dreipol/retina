from collections import defaultdict
from typing import Optional, Dict, List


class ImageAdapterContract(object):
    """
    Base contract all adapters must implement. Acts as a interface to ensure a common
    class structure and feature support over all adapters.
    """

    @staticmethod
    def url(file, alias: Optional[str] = None) -> str:
        """
        Returns a string (url) of the given file with the applied thumbnail alias to eventually
        transform the given file. It's optional that the alias gets applied and the
        adapter implementation can decide that on its own, it's just important
        that a string gets returned. `file` can be of any type.
        """
        raise NotImplementedError

    @staticmethod
    def alt(file) -> str: raise NotImplementedError


class ManagerContract(object):
    density = 0

    def get_adapter(self, file) -> ImageAdapterContract:
        raise NotImplementedError


class SupportsRetina(object):
    @staticmethod
    def retina(file, alias: Optional[str] = None, density: Optional[int] = 0) -> list:
        """
        Must return a list of urls where each list entry has larger image dimensions then the one before. Considering
        an image with size 10x10px, the returned list has to look like this (with a density of 3):
            [
                10x10.jpg,
                20x20.jpg,
                30x30.jpg,
            ]

        The `density` parameter defines how many retina-versions you want. A good multiplier is 2, since it
        will return the 'original' size, plus double-the-size image for iphones and other retina displays.
        At the time of this writing only the IphoneX supports @3 images. If we don't pass in a alias, it
        implies that the image is already given `density`, so instead of upscaling it we need to
        downscale it. So with an image of 90x90px and a `density` of 3 this is the result:
            [
                10x10.jpg, -> base size e.g. original / density
                20x20.jpg, -> in between e.g original * 2 (since case 1 and 3 are covered)
                90x90.jpg, -> original
            ]

        """
        raise NotImplementedError


class Manager(ManagerContract):
    """
    Helper class to always return the same dict for images. We need to cover a lot of cases,
    that's why this class was introduced. It allows you to pass in different type of images
    and will always return the same format, namely a dict with url, urls and alt attributes.

    It also allows you to apply multiple thumbnail presets to a single image with the 'srcset' method.
    Each image type has it's own adapter which must be subclassed from ImageAdapterContract. Out of the
    box Filer Image and File objects as well as static images (represented by a string) are allowed.
    """
    density = 2  # Density of two means we'll also return a @2 version of the image, 1 will just return 1
    _adapters: Dict[type, ImageAdapterContract] = {}

    def update_adapters(self, adapters: dict) -> None:
        tmp_adapters = self._adapters.copy()
        tmp_adapters.update(adapters)
        self._adapters = tmp_adapters

    def load_default_adapters(self):
        from filer.models import Image as FilerImage
        from filer.models import File as FilerFile
        from retina.adapters.filer import FilerImageAdapter, FilerFileAdapter

        self.update_adapters({
            FilerImage: FilerImageAdapter,
            FilerFile: FilerFileAdapter,
        })

    def update_density(self, density: int) -> None:
        self.density = density

    def get_adapter(self, file) -> ImageAdapterContract:
        file_type = type(file)

        if file_type not in self._adapters:
            raise ValueError('[{}] is an unsupported adapter'.format(file_type.__name__))

        return self._adapters.get(file_type)


manager = Manager()


class File(object):

    def __init__(self, file, manager: ManagerContract = manager):
        self._file = file
        self._adapter = manager.get_adapter(file)
        self._density = manager.density
        self._manager = manager
        self._additional = {}  # Allows us to pass additional data in the returned dict

    def density(self, density: int) -> 'File':
        """ Allows us to overwrite the density for this particular File instance """
        self._density = density

        return self

    def additional(self, **kwargs) -> 'File':
        """ Allows us to pass additional data in the returned dict """
        self._additional = {**self._additional, **kwargs}

        return self

    def thumbnail(self, alias: Optional[str] = None) -> dict:
        """
        Basic thumbnail generation method, also used for backwards compatibility. Uses
        the image instance and the provided thumbnail alias to return a dict
        with a url and an alt text.
        """
        return {
            'url': self._adapter.url(self._file, alias),
            'alt': self._adapter.alt(self._file),
            **self._additional,
        }

    def srcset(self, alias: Optional[str] = None, sizes: Optional[List[str]] = None) -> dict:
        """
        Successor of the thumbnail function with support for different sizes and retina images. The method tries
        to find thumbnail aliases for the passed in alias + _ + size and will throw a key error if none is
        found. If the adapter for the current file doesn't support retina images, it will just return
        a single image per srcset in a list.
        """
        alt = self._adapter.alt(self._file)
        urls = defaultdict(list)
        default_size = False
        real_alias = None

        if not issubclass(self._adapter, SupportsRetina):
            return self.thumbnail(alias)

        if sizes and not alias:
            raise ValueError('srcset can\'t be called with sizes but no alias')

        # srcset can be called with an alias but without any extra sizes, by convention
        # we force it to return one size called `default`. The corresponding
        # easy_thumbnail alias doesn't need to be called myalias_default
        # just myalias is enough.
        if not sizes:
            sizes = ['default']
            real_alias = alias
            default_size = True

        for size in sizes:
            if not default_size:
                real_alias = alias + '_' + size

            urls[size] = self._adapter.retina(self._file, alias=real_alias, density=self._density)

        return {
            'urls': urls,
            'alt': alt,
            **self._additional,
        }
