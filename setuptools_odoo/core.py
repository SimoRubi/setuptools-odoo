# -*- coding: utf-8 -*-
# © 2015 ACSONE SA/NV
# License LGPLv3 (http://www.gnu.org/licenses/lgpl-3.0-standalone.html)

import ast
import os
import setuptools
from distutils.core import DistutilsSetupError

from . import base_addons
from . import external_dependencies


ADDON_PKG_NAME_PREFIX = 'odoo-addon-'

ADDONS_NAMESPACE = 'odoo_addons'

ODOO_VERSION_INFO = {
    '8.0': {
        'odoo_dep': 'odoo>=8.0a,<9.0a',
        'base_addons': base_addons.odoo8,
        'addon_dep_version': '>=8.0a,<9.0a',
    },
    '9.0': {
        'odoo_dep': 'odoo>=9.0a,<9.1a',
        'base_addons': base_addons.odoo9,
        'addon_dep_version': '>=9.0a,<9.1a',
    },
}


def _get_manifest_path(addon_dir):
    for manifest_name in ('__odoo__.py', '__openerp__.py', '__terp__.py'):
        manifest_path = os.path.join(addon_dir, manifest_name)
        if os.path.isfile(manifest_path):
            return manifest_path


def _read_manifest(addon_dir):
    manifest_path = _get_manifest_path(addon_dir)
    if not manifest_path:
        raise DistutilsSetupError("no Odoo manifest found in %s" % addon_dir)
    return ast.literal_eval(open(manifest_path).read())


def is_installable_addon(addon_dir):
    try:
        manifest = _read_manifest(addon_dir)
        return manifest.get('installable', True)
    except:
        return False


def _get_version(addon_dir, manifest):
    version = manifest.get('version')
    if not version:
        raise DistutilsSetupError("No version in manifest in %s" % addon_dir)
    if len(version.split('.')) < 5:
        raise DistutilsSetupError("Version in manifest must have at least "
                                  "5 components and start with "
                                  "the Odoo series number in %s" % addon_dir)
    odoo_version = '.'.join(version.split('.')[:2])
    if odoo_version not in ODOO_VERSION_INFO:
        raise DistutilsSetupError("Unsupported odoo version '%s' in %s" %
                                  (odoo_version, addon_dir))
    odoo_version_info = ODOO_VERSION_INFO[odoo_version]
    return version, odoo_version_info


def _get_description(addon_dir, manifest):
    return manifest.get('summary', '').strip() or manifest.get('name').strip()


def _get_long_description(addon_dir, manifest):
    readme_path = os.path.join(addon_dir, 'README.rst')
    if os.path.exists(readme_path):
        return open(readme_path).read()
    else:
        return manifest.get('description')


def _get_pkg_name(name):
    return ADDON_PKG_NAME_PREFIX + name


def _get_install_requires(odoo_version_info, manifest, no_depends=[]):
    # dependency on Odoo
    install_requires = [odoo_version_info['odoo_dep']]
    # dependencies on other addons (except Odoo official addons)
    addon_dep_version = odoo_version_info['addon_dep_version']
    base_addons = odoo_version_info['base_addons']
    for depend in manifest.get('depends', []):
        if depend in base_addons:
            continue
        if depend in no_depends:
            continue
        install_require = _get_pkg_name(depend) + addon_dep_version
        install_requires.append(install_require)
    # python external_dependencies
    for dep in manifest.get('external_dependencies', {}).get('python', []):
        dep = external_dependencies.EXTERNAL_DEPENDENCIES_MAP.get(dep, dep)
        install_requires.append(dep)
    return sorted(install_requires)


def get_install_requires_odoo_addon(addon_dir, no_depends=[]):
    """ Get the list of requirements for an addon """
    manifest = _read_manifest(addon_dir)
    version, odoo_version_info = _get_version(addon_dir, manifest)
    return _get_install_requires(odoo_version_info, manifest, no_depends)


def get_install_requires_odoo_addons(addons_dir):
    """ Get the list of requirements for a directory containing addons """
    addon_dirs = []
    addons = os.listdir(addons_dir)
    for addon in addons:
        addon_dir = os.path.join(addons_dir, addon)
        if is_installable_addon(addon_dir):
            addon_dirs.append(addon_dir)
    install_requires = set()
    for addon_dir in addon_dirs:
        r = get_install_requires_odoo_addon(addon_dir, no_depends=addons)
        install_requires.update(r)
    return sorted(install_requires)


def prepare_odoo_addon():
    addons_dir = ADDONS_NAMESPACE
    addons = os.listdir(addons_dir)
    addons = [a for a in addons
              if os.path.isdir(os.path.realpath(os.path.join(addons_dir, a)))]
    if len(addons) != 1:
        raise DistutilsSetupError('%s must contain exactly one Odoo addon dir' %
                                  os.path.abspath(addons_dir))
    addon_name = addons[0]
    addon_dir = os.path.join(ADDONS_NAMESPACE, addon_name)
    if not is_installable_addon(addon_dir):
        raise DistutilsSetupError('%s is not an installable Odoo addon' %
                                  addon_dir)
    manifest = _read_manifest(addon_dir)
    version, odoo_version_info = _get_version(addon_dir, manifest)
    setup_keywords = {
        'name': _get_pkg_name(addon_name),
        'version': version,
        'description': _get_description(addon_dir, manifest),
        'long_description': _get_long_description(addon_dir, manifest),
        'url': manifest.get('website'),
        'license': manifest.get('license'),
        'packages': setuptools.find_packages(),
        'include_package_data': True,
        'namespace_packages': [ADDONS_NAMESPACE],
        'zip_safe': False,
        'install_requires': get_install_requires_odoo_addon(addon_dir),
        # TODO: keywords, classifiers, authors
    }
    # import pprint; pprint.pprint(setup_keywords)
    return setup_keywords


def prepare_odoo_addons():
    addons_dir = ADDONS_NAMESPACE
    setup_keywords = {
        'packages': setuptools.find_packages(),
        'include_package_data': True,
        'namespace_packages': [ADDONS_NAMESPACE],
        'zip_safe': False,
        'install_requires': get_install_requires_odoo_addons(addons_dir),
    }
    # import pprint; pprint.pprint(setup_keywords)
    return setup_keywords
