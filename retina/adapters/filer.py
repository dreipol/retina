from easy_thumbnails.alias import aliases
from easy_thumbnails.files import get_thumbnailer
from filer.models import File as FilerFile, Image as FilerImage
from filer.utils.filer_easy_thumbnails import FilerThumbnailer

from retina import SupportsRetina, ImageAdapterContract, Optional


class FilerFileImageProxy(object):
    """
    Since the FilerFile Adapter receives FilerFile objects instead of FilerImage, but for the thumbnailer
    to work we need the easy_thumbnails_thumbnailer property. With this proxy we provide said
    property to the FilerFile class without any ugly hacks.
    """

    def __init__(self, wrappee):
        self.wrappee = wrappee

    @property
    def easy_thumbnails_thumbnailer(self):
        tn = FilerThumbnailer(
            file=self.file, name=self.file.name,
            source_storage=self.file.source_storage,
            thumbnail_storage=self.file.thumbnail_storage,
            thumbnail_basedir=self.file.thumbnail_basedir)
        return tn

    def __getattr__(self, attr):
        return getattr(self.wrappee, attr)


class FilerFileAdapter(SupportsRetina, ImageAdapterContract):
    @staticmethod
    def _is_image(file: FilerFile) -> bool:
        return file.extension in ['jpg', 'jpeg', 'png']

    @classmethod
    def url(cls, file: FilerFile, alias: Optional[str] = None) -> str:
        if cls._is_image(file):
            file = FilerFileImageProxy(file)
            return FilerImageAdapter().url(file=file, alias=alias)

        return file.url

    @classmethod
    def retina(cls, file: FilerFile, alias: Optional[str] = None, density: Optional[int] = 1) -> list:
        if cls._is_image(file):
            file = FilerFileImageProxy(file)
            return FilerImageAdapter().retina(file=file, alias=alias, density=density)

        return [file.url]

    @staticmethod
    def alt(file: FilerFile) -> str:
        for attribute in ['default_alt_text', 'name', 'original_filename']:
            if getattr(file, attribute, None):
                return getattr(file, attribute)

        return ''


class FilerImageAdapter(SupportsRetina, ImageAdapterContract):
    @staticmethod
    def url(file: FilerImage, alias: Optional[str] = None) -> str:
        if not alias:
            return file.url

        return get_thumbnailer(file)[alias].url

    @classmethod
    def retina(cls, file: FilerImage, alias: Optional[str] = None, density: Optional[int] = 1) -> list:
        if alias:
            return cls.retina_upscale(file, alias, density)

        return cls.retina_downscale(file, density)

    @staticmethod
    def retina_downscale(file: FilerImage, density: Optional[int] = 1) -> list:
        thumbnailer = get_thumbnailer(file)

        dimensions = (file.width, file.height)
        base = tuple(round(size / density) for size in dimensions)

        # Start by adding the base size as key 0 to the files list
        files = [thumbnailer.get_thumbnail({'size': base}).url]

        # Add everything in between (e.g. density=3 results in base*2 since case 1 and 3 are covered
        for i in range(2, density):
            options = {'size': tuple(size * i for size in base)}
            files.append(thumbnailer.get_thumbnail(options).url)

        # End with the original image, since we're downscaling we know the original equals the density
        files.append(file.url)
        return files

    @staticmethod
    def retina_upscale(file: FilerImage, alias: Optional[str] = None, density: Optional[int] = 1) -> list:
        thumbnailer = get_thumbnailer(file)

        # We need to manually raise a KeyError since the get function can return None
        options = dict(aliases.get(alias))
        if not options:
            raise KeyError(alias)

        # Support for subject_location. This only works if scale_and_crop_with_subject_location is in
        # the THUMBNAIL_PROCESSORS and crop in the given alias is True
        if getattr(file, 'subject_location', None):
            options.update({'subject_location': file.subject_location})

        files = [thumbnailer.get_thumbnail(options).url]

        # Throws AttributeError if no size defined so make sure this property is set in your thumbnail alias
        original_size = options['size']

        for i in range(1, density):
            # Create a copy of the options since we're multiplying the size values bellow and
            # don't want to change the original ones
            new_options = options.copy()
            new_options.update({'size': tuple(size * (i + 1) for size in original_size)})

            files.append(thumbnailer.get_thumbnail(new_options).url)

        return files

    @staticmethod
    def alt(file: FilerImage) -> str:
        for attribute in ['default_alt_text', 'name', 'original_filename']:
            if getattr(file, attribute, None):
                return getattr(file, attribute)

        return ''
