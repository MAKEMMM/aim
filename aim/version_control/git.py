from aim.version_control.base import Base
import os

from git import Repo, InvalidGitRepositoryError


class GitAdapter(Base):
    @staticmethod
    def get_repo():
        try:
            return Repo(os.environ['PWD'], search_parent_directories=True)
        except InvalidGitRepositoryError:
            return None

    def get_untracked_files(self) -> list:
        """
        Returns a list containing all untracked files
        """
        repo = self.get_repo()
        git = repo.git

        untracked_files = git.ls_files('--others', '--exclude-standard')

        if not untracked_files:
            return []

        return untracked_files.split('\n')

    def get_head_hash(self):
        """
        Returns repo HEAD hash or `False` otherwise
        """
        repo = self.get_repo()

        try:
            return repo.head.object.hexsha
        except ValueError:
            return False

    def commit_changes_to_branch(self, commit_msg,
                                 branch_name, branch_prefix='aim/'):
        """
        Commits changes to a new created branch and returns branch name
        """
        branch = '{}{}'.format(branch_prefix, branch_name)

        try:
            repo = self.get_repo()
            git = repo.git
            active_branch_name = repo.active_branch.name

            # Stash changes
            stashed = False
            if len(self.get_index_diff('HEAD')):
                git.stash('save')
                stashed = True

            # Checkout new branch
            git.checkout('HEAD', b=branch)

            if stashed:
                # Apply the last stash
                git.stash('apply')

                # Add and commit changes
                git.add('.')
                repo.index.commit(commit_msg)

            # Checkout to previous branch
            git.checkout(active_branch_name)

            # Apply and remove the last stash
            if stashed:
                git.stash('pop')
        except:
            raise Exception('failed to commit changes to {branch}, ' +
                            'find your uncommitted changes in stash list ' +
                            'to recover git index state manually' +
                            ''.format(branch=branch))

        return branch

    def get_index_diff(self, target):
        """
        Return differences between index and target
        """
        repo = self.get_repo()
        change_types = ('A', 'C', 'D', 'R', 'M', 'T')

        diff = repo.index.diff(target)

        changes = []
        for change_type in change_types:
            for diff_item in diff.iter_change_type(change_type):
                changes.append(diff_item)

        return changes
