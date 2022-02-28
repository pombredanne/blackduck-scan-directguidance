import base64
import json
import random
import re
import os
import shutil
import sys
import tempfile

from azure.devops.connection import Connection
from msrest.authentication import BasicAuthentication

from bdscan import classSCMProvider
from bdscan import globals

from bdscan import utils

import gitlab as gitlab

import azure
import azure.devops
import requests
from azure.devops.v6_0.git import GitPushRef, GitRefUpdate, GitPush, GitCommitRef, GitPullRequest, \
    GitPullRequestCommentThread, Comment, GitPullRequestSearchCriteria


class GitLabProvider(classSCMProvider.SCMProvider):
    def __init__(self):
        super().__init__()
        self.scm = 'gitlab'

        self.gitlab_base_url = ''
        self.gitlab_gl_token = ''
        self.gitlab_ci_job_token = ''
        self.gitlab_merge_request_id = ''
        self.gitlab_namespace = ''
        self.gitlab_project = ''
        self.gitlab_project_id = ''
        self.gitlab_commit_branch = ''

        self.gitlab_client = None

    def init(self):
        globals.printdebug(f"DEBUG: Initializing Azure DevOps SCM Provider")

        self.gitlab_base_url = os.getenv('CI_SERVER_URL')
        self.gitlab_ci_job_token = os.getenv('CI_JOB_TOKEN')
        self.gitlab_gl_token = os.getenv('GL_TOKEN')

        self.gitlab_merge_request_id = os.getenv('CI_MERGE_REQUEST_IID')
        self.gitlab_namespace = os.getenv('CI_PROJECT_NAMESPACE')
        self.gitlab_project = os.getenv('CI_PROJECT_NAME')
        self.gitlab_project_id = os.getenv('CI_PROJECT_ID')
        self.gitlab_commit_branch = os.getenv('CI_COMMIT_BRANCH')

        globals.printdebug(f'DEBUG: GitLab base_url={self.gitlab_base_url} api_token={self.gitlab_ci_job_token},{self.gitlab_gl_token} '
                           f'merge_request_id={self.gitlab_merge_request_id} project={self.gitlab_project} '
                           f'project_id={self.gitlab_project_id}')

        if not self.gitlab_base_url or (not self.gitlab_ci_job_token and not self.gitlab_gl_token) \
                or not self.gitlab_project or not self.gitlab_project_id or not self.gitlab_namespace:
            print(f'BD-Scan-Action: ERROR: GitLab requires that CI_SERVER_URL, CI_JOB_TOKEN or GL_TOKEN,'
                  'CI_PROJECT_NAME, CI_PROJECT_NAMESPACE and CI_PROJECT_ID to be set.')
            sys.exit(1)

        if globals.args.comment_on_pr and not self.gitlab_merge_request_id:
            print(f'BD-Scan-Action: ERROR: GitLab requires that CI_MERGE_REQUEST_ID be set'
                  'when operating on a pull request')
            sys.exit(1)

        if globals.args.fix_pr and not self.gitlab_commit_branch:
            print(f'BD-Scan-Action: ERROR: GitLab requires that CI_COMMIT_BRANCH be set'
                  'when operating on a push')
            sys.exit(1)

        if self.gitlab_ci_job_token != None:
            globals.printdebug(f"DEBUG: GitLab using CI_JOB_TOKEN")
            self.gitlab_client = gitlab.Gitlab(self.gitlab_base_url, job_token=self.gitlab_ci_job_token)
        else:
            globals.printdebug(f"DEBUG: GitLab using CI_JOB_TOKEN")
            self.gitlab_client = gitlab.Gitlab(self.gitlab_base_url, private_token=self.gitlab_gl_token)

        self.gitlab_client.auth()

        globals.printdebug(f"DEBUG: Connected to GitLab")
        print(self.gitlab_client)

        return True

    def comp_fix_pr(self, comp):
        ret = True

        globals.printdebug(f"DEBUG: Fix '{comp.name}' version '{comp.version}' in "
                           f"file '{comp.projfiles}' using ns '{comp.ns}' to version "
                           f"'{comp.goodupgrade}'")

        pull_request_title = f"Black Duck: Upgrade {comp.name} to version " \
                             f"{comp.goodupgrade} to fix known security vulnerabilities"

        project = self.gitlab_client.projects.get(self.gitlab_project_id)

        mrs = project.mergerequests.list(state='opened', order_by='updated_at')
        for mr in mrs:
            if pull_request_title in mr.title:
                globals.printdebug(f"DEBUG: Skipping merge request for {comp.name}' version "
                                   f"'{comp.goodupgrade} as it is already present")
                return

        files_to_patch = comp.do_upgrade_dependency()

        if len(files_to_patch) == 0:
            print('BD-Scan-Action: WARN: Unable to apply fix patch - cannot determine containing package file')
            return False

        new_branch_seed = '%030x' % random.randrange(16 ** 30)
        new_branch_name = f"synopsys-enablement-{new_branch_seed}"

        branch = project.branches.create({'branch': new_branch_name,
                                          'ref': self.gitlab_commit_branch})

        # for file_to_patch in globals.files_to_patch:
        for pkgfile in files_to_patch:
            try:
                with open(files_to_patch[pkgfile], 'r') as fp:
                    new_contents = fp.read()
            except Exception as exc:
                print(f"BD-Scan-Action: ERROR: Unable to open package file '{files_to_patch[pkgfile]}'"
                      f" - {str(exc)}")
                return False

            f = project.files.get(file_path=pkgfile, ref=new_branch_name)

            f.content = new_contents
            f.save(branch=new_branch_name, commit_message=f'Update {pkgfile} to fix security vulnerability')

        pr_title = f"Black Duck: Upgrade {comp.name} to version {comp.goodupgrade} fix known security vulerabilities"
        pr_body = f"\n# Synopsys Black Duck Auto Pull Request\n" \
                  f"Upgrade {comp.name} from version {comp.version} to " \
                  f"{comp.goodupgrade} in order to fix security vulnerabilities:\n\n"

        new_mr = project.mergerequests.create({'source_branch': new_branch_name,
                                               'target_branch': self.gitlab_commit_branch,
                                               'title': pr_title,
                                               'description': pr_body,
                                               'labels': ['Synopsys', 'Black Duck']})

        return True

    def pr_comment(self, comment):
        project = self.gitlab_client.projects.get(self.gitlab_project_id)

        mr = project.mergerequests.get(self.gitlab_merge_request_id)

        existing_note = None

        mr_notes = mr.notes.list()
        for mr_note in mr_notes:
            if mr_note.body and globals.comment_on_pr_header in mr_note.body:
                existing_note = mr_note

        comments_markdown = f"# {globals.comment_on_pr_header}\n{comment}"

        if len(comments_markdown) > 65535:
            comments_markdown = comments_markdown[:65535]

        if existing_note is not None:
            globals.printdebug(f"DEBUG: Update/edit existing note for PR #{self.gitlab_merge_request_id}\n{comments_markdown}")

            existing_note.body = comments_markdown
            existing_note.save()
        else:
            globals.printdebug(f"DEBUG: Create new note for PR #{self.gitlab_merge_request_id}")

            mr_note = mr.notes.create({'body': comments_markdown})

        return True

    def set_commit_status(self, is_ok):
        globals.printdebug(f"WARNING: GitLab does not support set_commit_status")
        return

    def check_files_in_pull_request(self):
        found = False

        project = self.gitlab_client.projects.get(self.gitlab_project_id)

        mr = project.mergerequests.get(self.gitlab_merge_request_id)

        changes = mr.changes()
        for change in changes['changes']:
            if change['new_path'] in globals.pkg_files:
                found = True
                break

            if os.path.splitext(change['new_path'])[-1] in globals.pkg_exts:
                found = True
                break

        return found

    def check_files_in_commit(self):
        found = False

        project = self.gitlab_client.projects.get(self.gitlab_project_id)

        gitlab_commit_sha = os.getenv('CI_COMMIT_SHA')
        if not gitlab_commit_sha:
            print(f"BD-Scan-Action: ERROR: GitLab requires that CI_COMMIT_SHA be set to query commit")
            sys.exit(1)

        commit = project.commits.get(gitlab_commit_sha)

        diff = commit.diff()
        for change in diff:
            if change['new_path'] in globals.pkg_files:
                found = True
                break

            if os.path.splitext(change['new_path'])[-1] in globals.pkg_exts:
                found = True
                break

        return found
