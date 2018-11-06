from typing import Optional

import pytest

from retina import ImageAdapterContract, Manager, SupportsRetina, File


class DummyAdapter(ImageAdapterContract):

    @staticmethod
    def url(file, alias: Optional[str] = None) -> str:
        if alias:
            return 'url.{}'.format(alias)

        return 'url'

    @staticmethod
    def alt(file) -> str:
        return 'alt'


class DummyAdapterRetina(SupportsRetina, ImageAdapterContract):

    @staticmethod
    def retina(file, alias: Optional[str] = None, density: Optional[int] = 0) -> list:
        ret = []
        if alias:
            for i in range(0, density):
                ret.append('dummyfile_density_{}.{}.file'.format(i + 1, alias))
        else:
            for i in range(0, density):
                ret.append('dummyfile_density_{}.file'.format(i + 1))

        return ret

    @staticmethod
    def url(file, alias: Optional[str] = None) -> str:
        return 'url'

    @staticmethod
    def alt(file) -> str:
        return 'alt'


@pytest.fixture(scope='function')
def manager():
    manager = Manager()
    manager.update_adapters({str: DummyAdapter})

    return manager


@pytest.fixture(scope='function')
def raw_manager():
    manager = Manager()

    return manager


@pytest.fixture(scope='function')
def file(manager):
    return File('dummy.file', manager=manager)
