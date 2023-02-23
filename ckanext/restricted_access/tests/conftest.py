from pytest_factoryboy import register

from ckan.tests import factories


@register
class UserFactory(factories.User):
    about = "hidden user"


class SysadminFactory(factories.Sysadmin):
    pass


register(SysadminFactory, "sysadmin")


class DatasetFactory(factories.Dataset):
    pass


register(DatasetFactory, "dataset")
