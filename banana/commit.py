#
# Banana commit
#


class Commit:
    """Base commit class"""

    def __init__(self, commit, patch_id=None, provenance=None):
        self.commit = commit
        self.commit_id = commit.hexsha
        self.subject = commit.summary
        self.details = commit.message
        self.committed_at = commit.committed_date
        self.author_name = commit.author.name
        self.author_email = commit.author.email
        self.authored_at = commit.authored_date
        self.patch_id = patch_id
        self.provenance = provenance
        self.fixes = []
        self.cves = []
        self.mentions = []

    def to_dict(self, attrs):
        """Return a dict with the given class attribute values"""
        d = {}
        for a in attrs:
            d[a] = getattr(self, a)
        return d
