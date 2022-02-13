import random
import re
import sys
import os
from bdscan import globals

from github import Github
# from BlackDuckUtils import MavenUtils
# from BlackDuckUtils import NpmUtils
# from BlackDuckUtils import NugetUtils


def github_create_pull_request_comment(g, pr, comments_markdown):
    globals.printdebug(f"DEBUG: Look up GitHub repo '{globals.github_repo}'")
    repo = g.get_repo(globals.github_repo)

    body = comments_markdown

    issue = repo.get_issue(number=pr.number)

    globals.printdebug(f"DEBUG: Create pull request review comment for pull request #{pr.number} "
                       f"with the following body:\n{body}")
    issue.create_comment(body)


# def github_commit_file_and_create_fixpr(g, fix_pr_node, files_to_patch):
#     if len(files_to_patch) == 0:
#         print('BD-Scan-Action: WARN: Unable to apply fix patch - cannot determine containing package file')
#         return False
#     globals.printdebug(f"DEBUG: Look up GitHub repo '{globals.github_repo}'")
#     repo = g.get_repo(globals.github_repo)
#     globals.printdebug(repo)
#
#     globals.printdebug(f"DEBUG: Get HEAD commit from '{globals.github_repo}'")
#     commit = repo.get_commit('HEAD')
#     globals.printdebug(commit)
#
#     new_branch_seed = '%030x' % random.randrange(16 ** 30)
#     # new_branch_seed = secrets.token_hex(15)
#     new_branch_name = globals.github_ref + "-snps-fix-pr-" + new_branch_seed
#     globals.printdebug(f"DEBUG: Create branch '{new_branch_name}'")
#     ref = repo.create_git_ref("refs/heads/" + new_branch_name, commit.sha)
#     globals.printdebug(ref)
#
#     commit_message = f"Update {fix_pr_node['componentName']} to fix known security vulnerabilities"
#
#     # for file_to_patch in globals.files_to_patch:
#     for pkgfile in fix_pr_node['projfiles']:
#         globals.printdebug(f"DEBUG: Get SHA for file '{pkgfile}'")
#         orig_contents = repo.get_contents(pkgfile)
#
#         # print(os.getcwd())
#         globals.printdebug(f"DEBUG: Upload file '{pkgfile}'")
#         try:
#             with open(files_to_patch[pkgfile], 'r') as fp:
#                 new_contents = fp.read()
#         except Exception as exc:
#             print(f"BD-Scan-Action: ERROR: Unable to open package file '{files_to_patch[pkgfile]}'"
#                   f" - {str(exc)}")
#             return False
#
#         globals.printdebug(f"DEBUG: Update file '{pkgfile}' with commit message '{commit_message}'")
#         file = repo.update_file(pkgfile, commit_message, new_contents, orig_contents.sha, branch=new_branch_name)
#
#     pr_body = f"\n# Synopsys Black Duck Auto Pull Request\n" \
#               f"Upgrade {fix_pr_node['componentName']} from version {fix_pr_node['versionFrom']} to " \
#               f"{fix_pr_node['versionTo']} in order to fix security vulnerabilities:\n\n"
#
#     pr_body = pr_body + "\n".join(fix_pr_node['comments_markdown']) + "\n\n" + fix_pr_node['comments_markdown_footer']
#     globals.printdebug(f"DEBUG: Submitting pull request:")
#     globals.printdebug(pr_body)
#     pr = repo.create_pull(title=f"Black Duck: Upgrade {fix_pr_node['componentName']} to version "
#                                 f"{fix_pr_node['versionTo']} fix known security vulerabilities",
#                           body=pr_body, head=new_branch_name, base="master")
#     return True


def github_comp_commit_file_and_create_fixpr(g, comp, files_to_patch):
    if len(files_to_patch) == 0:
        print('BD-Scan-Action: WARN: Unable to apply fix patch - cannot determine containing package file')
        return False
    globals.printdebug(f"DEBUG: Look up GitHub repo '{globals.github_repo}'")
    repo = g.get_repo(globals.github_repo)
    globals.printdebug(repo)

    globals.printdebug(f"DEBUG: Get HEAD commit from '{globals.github_repo}'")
    commit = repo.get_commit('HEAD')
    globals.printdebug(commit)

    new_branch_seed = '%030x' % random.randrange(16 ** 30)
    # new_branch_seed = secrets.token_hex(15)
    new_branch_name = globals.github_ref + "-snps-fix-pr-" + new_branch_seed
    globals.printdebug(f"DEBUG: Create branch '{new_branch_name}'")
    ref = repo.create_git_ref("refs/heads/" + new_branch_name, commit.sha)
    globals.printdebug(ref)

    commit_message = f"Update {comp.name} to fix known security vulnerabilities"

    # for file_to_patch in globals.files_to_patch:
    for pkgfile in comp.projfiles:
        globals.printdebug(f"DEBUG: Get SHA for file '{pkgfile}'")
        orig_contents = repo.get_contents(pkgfile)

        # print(os.getcwd())
        globals.printdebug(f"DEBUG: Upload file '{pkgfile}'")
        try:
            with open(files_to_patch[pkgfile], 'r') as fp:
                new_contents = fp.read()
        except Exception as exc:
            print(f"BD-Scan-Action: ERROR: Unable to open package file '{files_to_patch[pkgfile]}'"
                  f" - {str(exc)}")
            return False

        globals.printdebug(f"DEBUG: Update file '{pkgfile}' with commit message '{commit_message}'")
        file = repo.update_file(pkgfile, commit_message, new_contents, orig_contents.sha, branch=new_branch_name)

    pr_body = f"\n# Synopsys Black Duck Auto Pull Request\n" \
              f"Upgrade {comp.name} from version {comp.version} to " \
              f"{comp.goodupgrade} in order to fix security vulnerabilities:\n\n"

    pr_body = pr_body + "\n".join(comp.longtext_md())
    globals.printdebug(f"DEBUG: Submitting pull request:")
    globals.printdebug(pr_body)
    pr = repo.create_pull(title=f"Black Duck: Upgrade {comp.name} to version "
                                f"{comp.goodupgrade} fix known security vulerabilities",
                                body=pr_body, head=new_branch_name, base="master")
    return True


def github_get_pull_requests(g):
    globals.printdebug(f"DEBUG: Index pull requests, Look up GitHub repo '{globals.github_repo}'")
    repo = g.get_repo(globals.github_repo)
    globals.printdebug(repo)

    pull_requests = []

    # TODO Should this handle other bases than master?
    pulls = repo.get_pulls(state='open', sort='created', base='master', direction="desc")
    for pull in pulls:
        globals.printdebug(f"DEBUG: Pull request number: {pull.number}: {pull.title}")
        pull_requests.append(pull.title)

    return pull_requests


# def github_fix_pr():
#     # fix_pr_components = dict()
#
#     globals.printdebug(f"DEBUG: Connect to GitHub at {globals.github_api_url}")
#     g = Github(globals.github_token, base_url=globals.github_api_url)
#
#     globals.printdebug("DEBUG: Generating Fix Pull Requests")
#
#     pulls = github_get_pull_requests(g)
#
#     globals.printdebug(f"fix_pr_data={globals.fix_pr_data}")
#     ret = True
#     for fix_pr_node in globals.fix_pr_data.values():
#         globals.printdebug(f"DEBUG: Fix '{fix_pr_node['componentName']}' version '{fix_pr_node['versionFrom']}' in "
#                            f"file '{fix_pr_node['projfiles']}' using ns '{fix_pr_node['ns']}' to version "
#                            f"'{fix_pr_node['versionTo']}'")
#
#         pull_request_title = f"Black Duck: Upgrade {fix_pr_node['componentName']} to version " \
#                              f"{fix_pr_node['versionTo']} to fix known security vulnerabilities"
#         if pull_request_title in pulls:
#             globals.printdebug(f"DEBUG: Skipping pull request for {fix_pr_node['componentName']}' version "
#                                f"'{fix_pr_node['versionFrom']} as it is already present")
#             continue
#
#         if fix_pr_node['ns'] == "npmjs":
#             files_to_patch = NpmUtils.upgrade_npm_dependency(
#                 fix_pr_node['projfiles'],fix_pr_node['componentName'],fix_pr_node['versionFrom'],
#                 fix_pr_node['versionTo'])
#         elif fix_pr_node['ns'] == "maven":
#             files_to_patch = MavenUtils.upgrade_maven_dependency(
#                 fix_pr_node['projfiles'],fix_pr_node['componentName'],fix_pr_node['versionFrom'],
#                 fix_pr_node['versionTo'])
#         elif fix_pr_node['ns'] == "nuget":
#             files_to_patch = NugetUtils.upgrade_nuget_dependency(
#                 fix_pr_node['projfiles'],fix_pr_node['componentName'],fix_pr_node['versionFrom'],
#                 fix_pr_node['versionTo'])
#         else:
#             print(f"BD-Scan-Action: WARN: Generating a Fix PR for packages of type '{fix_pr_node['ns']}' is "
#                   f"not supported yet")
#             return False
#
#         if len(files_to_patch) == 0:
#             print('BD-Scan-Action: WARN: Unable to apply fix patch - cannot determine containing package file')
#             return False
#
#         if not github_commit_file_and_create_fixpr(g, fix_pr_node, files_to_patch):
#             ret = False
#     return ret


def github_comp_fix_pr(comp):
    # fix_pr_node = {
    #     'componentName': comp_name,
    #     'versionFrom': comp_version,
    #     'versionTo': upgrade_ver,
    #     'ns': comp_ns,
    #     'projfiles': pkgfiles,
    #     'comments': [f"## Dependency {comp_name}/{comp_version}\n{shorttext}"],
    #     'comments_markdown': [longtext_md],
    #     'comments_markdown_footer': ''
    # }

    globals.printdebug(f"DEBUG: Connect to GitHub at {globals.github_api_url}")
    g = Github(globals.github_token, base_url=globals.github_api_url)

    pulls = github_get_pull_requests(g)

    ret = True
    globals.printdebug(f"DEBUG: Fix '{comp.name}' version '{comp.version}' in "
                       f"file '{comp.projfiles}' using ns '{comp.ns}' to version "
                       f"'{comp.goodupgrade}'")

    pull_request_title = f"Black Duck: Upgrade {comp.name} to version " \
                         f"{comp.goodupgrade} to fix known security vulnerabilities"
    if pull_request_title in pulls:
        globals.printdebug(f"DEBUG: Skipping pull request for {comp.name}' version "
                           f"'{comp.goodupgrade} as it is already present")
        return

    files_to_patch = comp.upgrade_dependency()

    if len(files_to_patch) == 0:
        print('BD-Scan-Action: WARN: Unable to apply fix patch - cannot determine containing package file')
        return False

    if not github_comp_commit_file_and_create_fixpr(g, comp, files_to_patch):
        ret = False
    return ret


def github_pr_comment(comment):
    globals.printdebug(f"DEBUG: Connect to GitHub at {globals.github_api_url}")
    g = Github(globals.github_token, base_url=globals.github_api_url)

    globals.printdebug(f"DEBUG: Look up GitHub repo '{globals.github_repo}'")
    repo = g.get_repo(globals.github_repo)
    globals.printdebug(repo)

    globals.printdebug(f"DEBUG: Look up GitHub ref '{globals.github_ref}'")
    # Remove leading refs/ as the API will prepend it on it's own
    # Actually look pu the head not merge ref to get the latest commit so
    # we can find the pull request
    ref = repo.get_git_ref(globals.github_ref[5:].replace("/merge", "/head"))
    globals.printdebug(ref)

    github_sha = ref.object.sha

    pull_number_for_sha = ref.ref.split('/')[2]
    globals.printdebug(f"DEBUG: Pull request #{pull_number_for_sha}")

    if pull_number_for_sha is None or not pull_number_for_sha.isnumeric():
        print(f"BD-Scan-Action: ERROR: Unable to find pull request #{pull_number_for_sha}")
        return False
    pull_number_for_sha = int(pull_number_for_sha)

    pr = repo.get_pull(pull_number_for_sha)

    pr_comments = repo.get_issues_comments(sort='updated', direction='desc')
    existing_comment = None
    for pr_comment in pr_comments:
        globals.printdebug(f"DEBUG: Issue comment={pr_comment.body}")
        arr = re.split('[/#]', pr_comment.html_url)
        if len(arr) >= 7:
            this_pullnum = arr[6]
            if not this_pullnum.isnumeric():
                continue
            this_pullnum = int(this_pullnum)
        else:
            continue
        if this_pullnum == pull_number_for_sha and globals.comment_on_pr_header in pr_comment.body:
            globals.printdebug(f"DEBUG: Found existing comment")
            existing_comment = pr_comment

    # Tricky here, we want everything all in one comment. So prepare a header, then append each of the comments and
    # create a comment
    # comments_markdown = [
    #     "| Component | Vulnerability | Severity |  Policy | Description | Current Ver | Upgrade to |",
    #     "| --- | --- | --- | --- | --- | --- | --- |"
    # ]
    #
    # for comment in globals.comment_on_pr_comments:
    #     comments_markdown.append(comment)
    comments_markdown = f"# {globals.comment_on_pr_header}\n" + "\n".join(comment)

    if len(comments_markdown) > 65535:
        comments_markdown = comments_markdown[:65535]

    if existing_comment is not None:
        globals.printdebug(f"DEBUG: Update/edit existing comment for PR #{pull_number_for_sha}\n{comments_markdown}")
        # existing_comment.edit("\n".join(comments_markdown))
        existing_comment.edit(comments_markdown)
    else:
        globals.printdebug(f"DEBUG: Create new comment for PR #{pull_number_for_sha}")
        github_create_pull_request_comment(g, pr, comments_markdown)
        issue = repo.get_issue(number=pr.number)
        issue.create_comment(comments_markdown)
    return True


def github_set_commit_status(is_ok):
    globals.printdebug(f"DEBUG: Set check status for commit '{globals.github_sha}', connect to GitHub at "
                       f"{globals.github_api_url}")
    g = Github(globals.github_token, base_url=globals.github_api_url)

    globals.printdebug(f"DEBUG: Look up GitHub repo '{globals.github_repo}'")
    repo = g.get_repo(globals.github_repo)
    globals.printdebug(repo)

    if not is_ok:
        status = repo.get_commit(sha=globals.github_sha).create_status(
            state="failure",
            target_url="https://synopsys.com/software",
            description="Black Duck security scan found vulnerabilities",
            context="Synopsys Black Duck"
        )
    else:
        status = repo.get_commit(sha=globals.github_sha).create_status(
            state="success",
            target_url="https://synopsys.com/software",
            description="Black Duck security scan clear from vulnerabilities",
            context="Synopsys Black Duck"
        )

    globals.printdebug(f"DEBUG: Status:")
    globals.printdebug(status)


def check_files_in_commit():
    g = Github(globals.github_token, base_url=globals.github_api_url)
    repo = g.get_repo(globals.github_repo)
    commit = repo.get_commit('HEAD')
    globals.printdebug(commit)

    found = False
    for commit_file in commit.files:
        if os.path.basename(commit_file.filename) in globals.pkg_files:
            found = True
            break

        if os.path.splitext(commit_file.filename)[-1] in globals.pkg_exts:
            found = True
            break

    return found


def check_files_in_pull_request():
    globals.printdebug(f"DEBUG: Connect to GitHub at {globals.github_api_url}")
    g = Github(globals.github_token, base_url=globals.github_api_url)

    globals.printdebug(f"DEBUG: Look up GitHub repo '{globals.github_repo}'")
    repo = g.get_repo(globals.github_repo)
    globals.printdebug(repo)

    globals.printdebug(f"DEBUG: Look up GitHub ref '{globals.github_ref}'")
    # Remove leading refs/ as the API will prepend it on it's own
    # Actually look pu the head not merge ref to get the latest commit so
    # we can find the pull request
    ref = repo.get_git_ref(globals.github_ref[5:].replace("/merge", "/head"))
    globals.printdebug(ref)

    github_sha = ref.object.sha

    pulls = repo.get_pulls(state='open', sort='created', base=repo.default_branch, direction="desc")
    pr = None
    pr_commit = None
    if globals.debug: print(f"DEBUG: Pull requests:")
    pull_number_for_sha = 0
    for pull in pulls:
        if globals.debug: print(f"DEBUG: Pull request number: {pull.number}")
        # Can we find the current commit sha?
        commits = pull.get_commits()
        for commit in commits.reversed:
            if globals.debug: print(f"DEBUG:   Commit sha: " + str(commit.sha))
            if commit.sha == github_sha:
                if globals.debug: print(f"DEBUG:     Found")
                pull_number_for_sha = pull.number
                pr = pull
                pr_commit = commit
                break
        if pull_number_for_sha != 0: break

    if pr_commit is None:
        print(f"ERROR: Unable to find pull request commits")
        sys.exit(1)

    # globals.printdebug(f"DEBUG: Pull request #{pull_number_for_sha}")
    #
    # if pull_number_for_sha is None:
    #     print(f"BD-Scan-Action: ERROR: Unable to find pull request #{pull_number_for_sha}")
    #     return False
    #
    # pr = repo.get_pull(pull_number_for_sha)
    #
    # pr_comments = repo.get_issues_comments(sort='updated', direction='desc')
    # existing_comment = None
    # for pr_comment in pr_comments:
    #     globals.printdebug(f"DEBUG: Issue comment={pr_comment.body}")
    #     if "Synopsys Black Duck XXXX" in pr_comment.body:
    #         globals.printdebug(f"DEBUG: Found existing comment")
    #         existing_comment = pr_comment

    found = False
    for commit_file in pr_commit.raw_data['files']:
        if os.path.basename(commit_file['filename']) in globals.pkg_files:
            found = True
            break

        if os.path.splitext(commit_file['filename'])[-1] in globals.pkg_exts:
            found = True
            break

    return found
