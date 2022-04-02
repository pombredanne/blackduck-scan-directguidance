# [PROTOTYPE] Black Duck Scan Action
A [GitHub Action](https://github.com/features/actions) for launching a Black Duck scan as part of a GitHub CI/CD workflow, offering a number of workflow use cases:
- Break the build if a security policy is not met
- Run rapid (dependency) scan 
- Compare scan against previous full scan for same project/version (optionally report only changed components)
- Leave comments on a pull request that identify vulnerable components and offer upgrade guidance
- Open fix pull requests for vulnerable components with an available upgrade (for npm/lerna/yarn/maven/nuget package managers)
- Import Black Duck vulnerabilities as code scanning alerts via SARIF

This script is provided under an OSS license (specified in the LICENSE file) and has been developed by Synopsys field engineers as a contribution to the Synopsys user community. Please direct questions and comments to the [Black Duck Integrations Forum](https://community.synopsys.com/s/topic/0TO34000000gGZnGAM/black-duck-integrations) in the Synopsys user community.

## Overview

This action uses Black Duck rapid scan to identify vulnerable direct dependencies supporting multiple package managers (including maven, npm, nuget, yarn, lerna, cargo, conan, gradle, python, pypi, pip etc.).

Vulnerable direct dependencies can be reported in SARIF (for import as code scanning alerts) or as comments in pull requests.

For specific package managers (npm, lerna, yarn, nuget, maven), it can also generate automatic fix Pull Requests to upgrade vulnerable direct dependencies to address identified vulnerabilities.

Scans can be compared against previous full (intelligent) scans of the same project version, with the option to only report changed components.

## Usage

The action runs as a Docker container, supporting GitHub-hosted and Self-hosted Linux runners.

The action has several independent modes of operation intended to be used with different GitHub activities:
1. Produce SARIF output of vulnerable direct dependencies for import as code scanning alerts in Github
2. For a Pull Request, add a comment listing vulnerable direct dependencies with upgrade guidance
3. For a Commit/Push, create fix Pull Requests for each vulnerable direct dependency where an upgrade can be determined

Mode 1 (SARIF production) can be used standalone or optionally combined with modes 2 or 3.
Modes 2 and 3 are mutually exclusive (and should be defined as separate steps in the Action workflow).

Additional options for the Action include:
- upgrade_major true: Allow upgrades for future major releases (default is to only report upgrades within the same major release)
- incremental_results true: Only report vulnerable direct dependencies which have been changed since the last full scan
- nocheck true: Skip checking that modified package manager config file is included in PR or commit
- debug N: Show debug messages (integer value above 0)

Other options are used to manage the Black Duck scan including:
- url BD_URL: Black Duck server URL including https:// (can also be specified in BLACKDUCK_URL environment variable)
- token BD_TOKEN: Black Duck API token (can also be specified in BLACKDUCK_API_TOKEN environment variable)
- trustcert true: Ignore Black Duck server certificate
- output FOLDER: temporary folder for Black Duck scans (default 'blackduck-output')
- project PROJECT: Black Duck project name
- version VERSION: Black Duck version name
- mode MODE: Scan mode ('rapid' or 'intelligent' - default 'rapid')
- detect_opts OPTION=VALUE,OPTION=VALUE: List of additional Synopsys Detect options, comma delimited without leading hyphens, no spaces

## Prerequisites

Please ensure the following prerequisites are met before using this action:

1. Access to a Black Duck Professional or Security Edition server
2. At least 1 policy has been created in the Black Duck server configured for Rapid scans and covering security vulnerabilities
3. API Token has been generated with permission to run scans
4. Repos to be scanned are ready to be built and have 

## Generate SARIF for code scanning alerts

The following step shws

You can use the Action as follows:

```yaml
name: Scan a project with Black Duck

on:
  push:
    branches: [ master ]
  pull_request:
    branches: [ master ]
  workflow_dispatch:

jobs:
  blackduck:
    runs-on: ubuntu-latest
    steps:
    
    - name: Checkout the code
      uses: actions/checkout@v2
      
    # Runs a Black Duck intelligent scan on commits to master
    # This will run a "full" or "intelligent" scan, logging new components in the Black Duck Hub server
    # in order to provide real time notifications when new vulnerabilities are reported.
    - name: Run Baseline Black Duck Scan (manual, workflow dispatch)
      if: ${{github.event_name == 'workflow_dispatch'}}
      uses: synopsys-sig-community/blackduck-scan-action@v1
      with:
        url: ${{ secrets.BLACKDUCK_URL }}
        token: ${{ secrets.BLACKDUCK_TOKEN }}
        mode: intelligent
        
    # Runs a Black Duck rapid scan on push
    # This will run a "rapid" scan on pushes to a main branch, and attempt to file a fix pull request
    # for vulnerable components if there is a suitable upgrade path
    - name: Run Black Duck security scan (push)
      if: ${{github.event_name == 'push'}}
      uses: synopsys-sig-community/blackduck-scan-action@v1
      with:
        url: ${{ secrets.BLACKDUCK_URL }}
        token: ${{ secrets.BLACKDUCK_TOKEN }}
        # Generate SARIF output
        sarif: blackduck-sarif.json
        # Use "rapid" mode for a fast scan appropriate for CI/CD pipeline
        mode: rapid
        # Generate fix pull requests when upgarde guidance
        fix_pr: true
      # Must continue on error in order to reach SARIF import
      continue-on-error: true
      env:
        # Pass the GitHub token to the script in order to create PRs
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        
     - name: Upload SARIF file (push)
      if: ${{github.event_name == 'push'}}
      uses: github/codeql-action/upload-sarif@v1
      with:
        # Path to SARIF file relative to the root of the repository
        sarif_file: blackduck-sarif.json

    # Runs a Black Duck rapid scan on pull request
    # This will run a "rapid" scan on pull requests, only reporting components that have been introduced since the
    # last full or intelligent scan, abd comment 
    - name: Run Black Duck security scan (pull_request)
      if: ${{github.event_name == 'pull_request'}}
      uses: synopsys-sig-community/blackduck-scan-action@v1
      with:
        url: ${{ secrets.BLACKDUCK_URL }}
        token: ${{ secrets.BLACKDUCK_TOKEN }}
        # Generate SARIF output
        sarif: blackduck-sarif.json
        # Use "rapid" mode for a fast scan appropriate for CI/CD pipeline
        mode: rapid
        # Leave feedback through a comment on the PR
        comment_on_pr: true
        # Only report newly introduced components
        incremental_results: true
      # Must continue on error in order to reach SARIF import
      continue-on-error: true
      env:
        # Pass the GitHub token to the script in order to create PRs
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}

     - name: Upload SARIF file (pull_request)
      if: ${{github.event_name == 'pull_request'}}
      uses: github/codeql-action/upload-sarif@v1
      with:
        # Path to SARIF file relative to the root of the repository
        sarif_file: blackduck-sarif.json

```

## Inputs

The Black Duck Scanning action has a number of input parameters that can be passed using `with`. All input parameters have default vaules that should ensure reasonable default behavior.

| Property | Default | Description |
| --- | --- | --- |
| mode | intelligent | Run either an intelligent scan (comprehensive, and update central database with component versions) or rapid scan (runs in seconds, ephemeral)|
| sarif | blackduck-sarif.json | Output results in SARIF file suitable for import into GitHub |
| comment_on_pr | false | If running triggered by a pull request, leave a comment on the pull request with the reported issues |
| fix_pr | false | Generate a fix pull request if a vulnerable componenent has an available upgrade path |
| upgrade_major | false | Include upgrades that are beyond the current major version of the component being used - note, this can introduce a breaking change if the component's APIs are sufficiently different |
| incremental_results | false | Filter the output to only report on newly introduced components. Do not report on any vulnerabilities on component versions previously detected in the project |

