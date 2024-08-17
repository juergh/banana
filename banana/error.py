#
# Banana error
#


class Error(Exception):
    pass


class CommitIdExistsError(Error):
    pass


class InvalidIdError(Error):
    pass


class InvalidColumnError(Error):
    pass
