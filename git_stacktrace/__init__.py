import pkg_resources

__version__ = pkg_resources.get_provider(pkg_resources.Requirement.parse('git-stacktrace')).version
