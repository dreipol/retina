from unittest import mock

import pytest

from retina import File, Manager, ManagerContract, ImageAdapterContract, SupportsRetina
from tests.conftest import DummyAdapter, DummyAdapterRetina


def test_manager(raw_manager):
    # Assert manager default settings
    assert len(raw_manager._adapters) == 0
    assert raw_manager.density == 2

    raw_manager.update_adapters({str: DummyAdapter})
    raw_manager.update_density(99)
    adapter = raw_manager.get_adapter('foo.bar')

    # Assert mutated data on manager
    assert len(raw_manager._adapters) == 1
    assert raw_manager.density == 99
    assert adapter == DummyAdapter


def test_not_implemented_exceptions():
    filer_image = mock.Mock(name='FilerImage', spec=True)
    manager = ManagerContract()
    adapter = ImageAdapterContract()
    adapter_retina = SupportsRetina()

    with pytest.raises(NotImplementedError):
        manager.get_adapter(filer_image)

    with pytest.raises(NotImplementedError):
        adapter.url(filer_image)

    with pytest.raises(NotImplementedError):
        adapter.alt(filer_image)

    with pytest.raises(NotImplementedError):
        adapter_retina.retina(filer_image)


def test_invalid_adapter(raw_manager):
    # raw_manager has no adapters set
    with pytest.raises(ValueError):
        raw_manager.get_adapter('dummy.file')


def test_file_init(manager):
    file = File('dummy.file', manager=manager)

    assert file._file == 'dummy.file'
    assert file._adapter == DummyAdapter
    assert file._density == 2
    assert file._manager == manager
    assert file._additional == {}


def test_file_density(file):
    ret = file.density(99)
    assert ret == file
    assert file._density == 99


def test_file_additional(file):
    ret = file.additional(foo='bar')
    assert ret == file
    assert file._additional == {'foo': 'bar'}

    # Assert additional data
    ret = file.thumbnail()
    assert ret == {'url': 'url', 'alt': 'alt', 'foo': 'bar'}


def test_file_thumbnail(file):
    ret = file.thumbnail()
    assert ret == {'url': 'url', 'alt': 'alt'}

    ret = file.thumbnail(alias='foo')
    assert ret == {'url': 'url.foo', 'alt': 'alt'}


def test_srcset_no_retina(file):
    ret = file.srcset()
    assert ret == {'url': 'url', 'alt': 'alt'}

    ret = file.srcset(alias='foo')
    assert ret == {'url': 'url.foo', 'alt': 'alt'}

    # Has no impact since sizes gets ignored if the adapter has no retina support
    ret = file.srcset(alias='foo', sizes=['xl', 'md'])
    assert ret == {'url': 'url.foo', 'alt': 'alt'}


def test_srcset_retina():
    manager = Manager()
    manager.update_adapters({str: DummyAdapterRetina})
    file = File('dummy.file', manager=manager)

    ret = file.srcset()
    assert ret == {'urls': {'default': ['dummyfile_density_1.file', 'dummyfile_density_2.file']}, 'alt': 'alt'}

    with pytest.raises(ValueError):
        file.srcset(sizes=['size1', 'size2'])

    ret = file.srcset(alias='foo')
    assert ret == {'urls': {'default': ['dummyfile_density_1.foo.file', 'dummyfile_density_2.foo.file']}, 'alt': 'alt'}

    ret = file.srcset(alias='foo', sizes=['size1', 'size2'])
    assert ret == {
        'urls': {
            'size1': ['dummyfile_density_1.foo_size1.file', 'dummyfile_density_2.foo_size1.file'],
            'size2': ['dummyfile_density_1.foo_size2.file', 'dummyfile_density_2.foo_size2.file'],
        },
        'alt': 'alt'
    }

    file.additional(foo='bar')
    ret = file.srcset()
    assert ret == {'urls': {'default': ['dummyfile_density_1.file', 'dummyfile_density_2.file']}, 'alt': 'alt',
                   'foo': 'bar'}
