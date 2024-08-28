#
# Banana error
#


class Error(Exception):
    pass


class RowExistsError(Error):
    pass


class InvalidIdError(Error):
    pass


class InvalidColumnError(Error):
    pass
