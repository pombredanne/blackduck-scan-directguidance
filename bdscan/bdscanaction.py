#!/usr/bin/env python

import argparse
import sys
import os
from bdscan import scan
from bdscan import globals


def main():
    def isempty(val):
        if val is None or val == '':
            return True
        return False

    def evaltrue(val):
        if not isempty(val) and str(val).lower() == 'true':
            return True
        return False

    # os.chdir('/Users/mbrad/working/duck_hub_ORI')
    parser = argparse.ArgumentParser(
        description="Scan project to determine upgrades for vulnerable dirwct dependencies")
    parser.add_argument('--debug', default=0, help='set debug level [0-9]')
    parser.add_argument("--url", required=True, type=str, help="Black Duck Hub URL")
    parser.add_argument("--token", required=True, type=str, help="Black Duck Hub Token")
    parser.add_argument("--trustcert", default="false", type=str, help="Trust Black Duck server certificate")
    parser.add_argument("--project", type=str, help="Project name")
    parser.add_argument("--version", type=str, help="Project version name")
    parser.add_argument("--mode", default="rapid", type=str,
                        help="Black Duck scanning mode, either intelligent or rapid")
    parser.add_argument("--output", default="blackduck-output", type=str, help="Output directory")
    parser.add_argument("--fix_pr", type=str, default="false", help="Create Fix PRs for upgrades, true or false")
    parser.add_argument("--upgrade_major", type=str, default="false",
                        help="Offer upgrades to major versions, true or false")
    parser.add_argument("--comment_on_pr", type=str, default="false",
                        help="Generate a comment on pull request, true or false")
    parser.add_argument("--sarif", type=str, help="SARIF output file")
    parser.add_argument("--incremental_results", default="false", type=str,
                        help="Compare to previous intelligent scan project - only report & ix new/changed components")
    parser.add_argument("--nocheck", type=str,
                        help="Skip check of GH commit/PR for changed package manager config files")
    parser.add_argument("--detect_opts", type=str,
                        help="Passthrough options to Detect, comma delimited, exclude leading hyphens")

    globals.args = parser.parse_args()

    if isempty(globals.args.url):
        globals.args.url = os.getenv("BLACKDUCK_URL")
    if isempty(globals.args.token):
        globals.args.token = os.getenv("BLACKDUCK_API_TOKEN")

    if isempty(globals.args.url) or isempty(globals.args.token):
        print(f"BD-Scan-Action: ERROR: Must specify Black Duck Hub URL and API Token")
        sys.exit(1)

    print(f'BD-Scan-Action: Start\n\n'
          f'--- BD-SCAN-ACTION CONFIGURATION (version {globals.scan_utility_version}) -----------------------')

    globals.args.trustcert = evaltrue(globals.args.trustcert)
    if globals.args.trustcert is False:
        trustcert = os.getenv("BLACKDUCK_TRUST_CERT")
        if isempty(trustcert):
            globals.args.trustcert = False
        else:
            globals.args.trustcert = True

    globals.args.fix_pr = evaltrue(globals.args.fix_pr)
    if globals.args.fix_pr:
        print('  --fix_pr:              CREATE FIX PR')

    globals.args.comment_on_pr = evaltrue(globals.args.comment_on_pr)
    if globals.args.comment_on_pr:
        print('  --comment_on_pr:       ADD COMMENT TO EXISTING PR')

    if not isempty(globals.args.sarif):
        print(f"  --sarif:               OUTPUT GH SARIF TO '{globals.args.sarif}'")
    else:
        globals.args.sarif = None

    print(f'  --url:                 BD URL {globals.args.url}')
    print(f'  --token:               BD Token *************')
    runargs = []
    if globals.args.trustcert:
        runargs.append("--blackduck.trust.cert=true")
        print('  --trustcert:           Trust BD server certificate')

    if isempty(globals.args.mode):
        globals.args.mode = 'rapid'
    elif str(globals.args.mode).lower() == 'full' or str(globals.args.mode).lower() == 'intelligent':
        globals.args.mode = 'intelligent'
        print('  --mode:                Run intelligent (full) scan')
    else:
        globals.args.mode = 'rapid'
        print('  --mode:                Run Rapid scan')

    globals.args.upgrade_major = evaltrue(globals.args.upgrade_major)
    if globals.args.upgrade_major:
        print('  --upgrade_major:       Allow major version upgrades')

    globals.args.incremental_results = evaltrue(globals.args.incremental_results)
    if globals.args.incremental_results:
        print('  --incremental_results: Calculate incremental results (since last full/intelligent scan')

    globals.args.nocheck = evaltrue(globals.args.nocheck)
    if globals.args.nocheck:
        print('  --nocheck              Skip check of GH commit/PR for changed package manager config files')

    # if globals.args.upgrade_indirect is None or globals.args.upgrade_indirect == 'false' or \
    #         globals.args.upgrade_indirect == '':
    #     globals.args.upgrade_indirect = False
    # elif str(globals.args.upgrade_indirect).lower() == 'true':
    #   print('  --upgrade_indirect:    Calculate upgrades for direct dependencies to address indirect vulnerabilities')
    #     globals.args.upgrade_indirect = True
    # else:
    #     globals.args.upgrade_indirect = False
    # Ignoring the upgrade_indirect setting as it is no longer useful
    # globals.args.upgrade_indirect = True

    globals.debug = 0
    if not isempty(globals.args.debug):
        globals.debug = int(globals.args.debug)

    runargs.extend(["--blackduck.url=" + globals.args.url,
                    "--blackduck.api.token=" + globals.args.token,
                    "--detect.blackduck.scan.mode=" + globals.args.mode,
                    # "--detect.detector.buildless=true",
                    "--detect.output.path=" + globals.args.output,
                    "--detect.bdio.file.name=scanout.bdio",
                    "--detect.cleanup=false"])

    if not isempty(globals.args.project):
        runargs.append("--detect.project.name=" + globals.args.project)
        print(f"  --project:            BD project name '{globals.args.project}'")

    if not isempty(globals.args.version):
        runargs.append("--detect.project.version.name=" + globals.args.version)
        print(f"  --version:            BD project version name '{globals.args.version}'")

    if not isempty(globals.args.detect_opts):
        for opt in str(globals.args.detect_opts).split(','):
            newopt = f"--{opt}"
            print(f"  --detect_opts:    Add option to Detect scan {newopt}")
            runargs.append(newopt)

    print('-------------------------------------------------------------------------\n')

    if isempty(globals.args.sarif) and not globals.args.comment_on_pr and not globals.args.fix_pr and \
            globals.args.mode == 'rapid':
        print("BD-Scan-Action: Nothing to do - specify at least 1 option from 'sarif, comment_on_pr, fix_pr'")
        sys.exit(1)

    if globals.args.fix_pr and globals.args.comment_on_pr:
        print("BD-Scan-Action: Cannot specify BOTH fix_pr and comment_on_pr - Exiting")
        sys.exit(1)

    scan.main_process(globals.args.output, runargs)


if __name__ == "__main__":
    main()
