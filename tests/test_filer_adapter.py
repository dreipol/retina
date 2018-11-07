import os

import django
import pytest

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tests.django_settings')
django.setup()

from unittest import mock
from unittest.mock import MagicMock, PropertyMock, call

from doublex import Spy, property_got, assert_that, Stub
from filer.models import Image as FilerImage

from retina.adapters.filer import FilerImageAdapter


def test_url_without_alias():
    with Spy(FilerImage) as filer_image:
        filer_image.url.returns('dummy.url')

    res = FilerImageAdapter().url(filer_image)
    assert_that(filer_image, property_got('url'))
    assert res == 'dummy.url'


@mock.patch('retina.adapters.filer.get_thumbnailer')
def test_url_with_alias(get_thumbnailer_mock):
    with Spy(FilerImage) as filer_image:
        filer_image.url.returns('dummy.url')

    # Mock the get_thumbnailer() function call and make it return our mocked Thumbnailer instance
    thumbnailer_mock = MagicMock()
    thumbnailer_mock.__getitem__.return_value = filer_image
    get_thumbnailer_mock.return_value = thumbnailer_mock

    res = FilerImageAdapter().url(filer_image, alias='foo')  # Trigger
    get_thumbnailer_mock.assert_called_with(filer_image)  # Was get_thumbnailer() called correctly?
    thumbnailer_mock.__getitem__.assert_called_with('foo')  # Was the correct alias on our Thumbnailer accessed?
    assert_that(filer_image, property_got('url'))  # Was our filer_image mocks url property accessed?
    assert res == 'dummy.url'


@mock.patch('retina.adapters.filer.FilerImageAdapter.retina_downscale')
def test_retina_without_alias(downscale_mock):
    filer_image = Stub(FilerImage)
    FilerImageAdapter().retina(filer_image)
    downscale_mock.assert_called_with(filer_image, 1)
    FilerImageAdapter().retina(filer_image, density=2)
    downscale_mock.assert_called_with(filer_image, 2)


@mock.patch('retina.adapters.filer.FilerImageAdapter.retina_upscale')
def test_retina_with_alias(upscale_mock):
    filer_image = Stub(FilerImage)
    FilerImageAdapter().retina(filer_image, alias='foo')
    upscale_mock.assert_called_with(filer_image, 'foo', 1)
    FilerImageAdapter().retina(filer_image, alias='foo', density=2)
    upscale_mock.assert_called_with(filer_image, 'foo', 2)


@mock.patch('retina.adapters.filer.get_thumbnailer')
@mock.patch('retina.adapters.filer.aliases')
def test_retina_upscale(aliases_mock, get_thumbnailer_mock):
    with Spy(FilerImage) as filer_image:
        filer_image.width.returns(300)
        filer_image.height.returns(300)
        filer_image.subject_location = None

    # Mock the get_thumbnailer() function call and make it return our mocked Thumbnailer instance
    thumbnail_mock = MagicMock(name='Thumbnail')
    thumbnail_mock.url = 'dummy-generated'

    thumbnailer_mock = MagicMock(name='Thumbnailer')
    thumbnailer_mock.get_thumbnail.return_value = thumbnail_mock
    get_thumbnailer_mock.return_value = thumbnailer_mock
    aliases_mock.get.return_value = {'size': (300, 300)}

    result = FilerImageAdapter().retina_upscale(filer_image, density=3)
    assert result == ['dummy-generated', 'dummy-generated', 'dummy-generated']
    thumbnailer_mock.get_thumbnail.assert_has_calls([
        call({'size': (300, 300)}),
        call({'size': (600, 600)}),
        call({'size': (900, 900)})],
    )

    # Test subject_location
    filer_image.subject_location = (1, 1)
    thumbnailer_mock.reset_mock()
    result = FilerImageAdapter().retina_upscale(filer_image, density=2)
    assert result == ['dummy-generated', 'dummy-generated']
    thumbnailer_mock.get_thumbnail.assert_has_calls([
        call({'size': (300, 300), 'subject_location': (1, 1)}),
        call({'size': (600, 600), 'subject_location': (1, 1)}),
    ])

    aliases_mock.get.return_value = {}
    with pytest.raises(KeyError):
        FilerImageAdapter().retina_upscale(filer_image, density=3)


@mock.patch('retina.adapters.filer.get_thumbnailer')
def test_retina_downscale(get_thumbnailer_mock):
    with Spy(FilerImage) as filer_image:
        filer_image.width.returns(300)
        filer_image.height.returns(300)
        filer_image.url.returns('dummy-original')

    # Mock the get_thumbnailer() function call and make it return our mocked Thumbnailer instance
    thumbnail_mock = MagicMock(name='Thumbnail')
    thumbnail_mock.url = 'dummy-generated'

    thumbnailer_mock = MagicMock(name='Thumbnailer')
    thumbnailer_mock.__getitem__.return_value = filer_image
    thumbnailer_mock.get_thumbnail.return_value = thumbnail_mock
    get_thumbnailer_mock.return_value = thumbnailer_mock

    result = FilerImageAdapter().retina_downscale(filer_image, density=3)
    assert result == ['dummy-generated', 'dummy-generated', 'dummy-original']
    thumbnailer_mock.get_thumbnail.assert_has_calls([
        call({'size': (100, 100)}),
        call({'size': (200, 200)})],
    )
    thumbnailer_mock.reset_mock()

    result = FilerImageAdapter().retina_downscale(filer_image, density=4)
    assert result == ['dummy-generated', 'dummy-generated', 'dummy-generated', 'dummy-original']
    thumbnailer_mock.get_thumbnail.assert_has_calls([
        call({'size': (75, 75)}),
        call({'size': (150, 150)})],
        call({'size': (225, 225)}),
    )


def test_alt_empty_return():
    """ Douplex doesn't support mocked properties on free doubles so we need to use the standard mock library """
    filer_image = mock.Mock(name='FilerImage', spec=True)

    original_filename = PropertyMock(name='original_filename')
    type(filer_image).original_filename = original_filename
    original_filename.return_value = None

    name = PropertyMock(name='name')
    type(filer_image).name = name
    name.return_value = None

    default_alt_text = PropertyMock(name='default_alt_text')
    type(filer_image).default_alt_text = default_alt_text
    default_alt_text.return_value = None

    result = FilerImageAdapter().alt(filer_image)

    assert result == ''
    assert original_filename.call_count == 1
    assert name.call_count == 1
    assert default_alt_text.call_count == 1


def test_alt_return():
    filer_image = mock.Mock(name='FilerImage', spec=True)

    original_filename = PropertyMock(name='original_filename')
    type(filer_image).original_filename = original_filename
    original_filename.return_value = 'foo'

    result = FilerImageAdapter().alt(filer_image)

    assert result == 'foo'
    # It's 2 because once for checking if the attribute exists and once for returning it
    assert original_filename.call_count == 2
