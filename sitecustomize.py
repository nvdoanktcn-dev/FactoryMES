import six

if not hasattr(six._importer, "_path"):
    six._importer._path = six.__file__