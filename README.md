# Community Black Duck GitHub Scan Action

## Overview

This is a community supported [GitHub Action](https://github.com/features/actions) for launching Black Duck SCA (OSS vulnerability analysis) scans as part of a GitHub CI/CD workflow, offering a number of workflow use cases:
- Run Black Duck Synopsys Detect scans within a GitHub Action
- For `Pull Requests`, optionally leave comments on a pull request that identify vulnerable components and offer upgrade guidance (all supported package managers)
- For `Commits/Pushes`, identify the vulnerable direct dependencies and optionally create new fix pull requests with available upgrades including for vulnerable child dependencies (primary package managers only - see below)
- Optionally report only newly introduced components (as compared against the last FULL scan)
- Optionally export Black Duck vulnerabilities via SARIF for subsequent import as code scanning alerts in GitHub (requires Advanced Security subscription in GitHub)
- Break the build if security policies are not met

Black Duck RAPID scan policies are used to determine vulnerabilities to be reported/fixed, allowing specific vulnerability severities and types to be covered. See the Black Duck User Guide within your server for more information on configuring policies.

This script is provided under an OSS license (specified in the LICENSE file) and has been developed by Synopsys field engineers as a contribution to the Synopsys user community. Please direct questions and comments to the [Black Duck Integrations Forum](https://community.synopsys.com/s/topic/0TO34000000gGZnGAM/black-duck-integrations) in the Synopsys user community.

## Supported Technologies

The utility supports a primary list of package managers:
- Npm/Lerna/Pnpm/Yarn
- Maven
- NuGet

Projects built with one or more of the primary package managers can utilise all features as shown below, deployed as a GitHub Action and using a pre-built container downloaded in the run.
This deployment supports the calculation of upgrade guidance for direct dependencies which includes validation that all indirect (transitive) dependencies are also resolved by upgrade.
It will optionally create a comment within a Pull Request or create fix PRs within commits/pushes for the vulnerable direct dependencies.

For the list secondary of package managers shown below, the utility needs to be installed as a PyPi module and run directly as a command.
This deployment supports identifying vulnerable direct dependencies with transitive vulnerabilities, but does not provide complete upgrade guidance for all children, and does not support creating fix PRs to address vulnerabilities.
- Conan
- Conda
- Dart
- GoLang
- Hex
- Pypi

The utility can support multiple package managers in a single project, although you need to ensure you choose the correct mode (primary or secondary package managers) based on the full list. For example, if you have a project using Maven, npm and Pypi, you will need to use the secondary package manager operation mode throughout, unless you specify Synopsys Detect options to exclude the secondary package managers (in this case pypi).

# Configuration

## Prerequisites

For all package managers, the following prerequisites are required:
- This utility requires access to a Black Duck Professional server v2021.10 or above.
- At least 1 security policy for RAPID scan must be configured (otherwise scans will show no results as no components will violate policies).
- The following repository secrets must be configured:
  - BLACKDUCK_URL - full URL to Black Duck server (e.g. `https://server.blackduck.synopsys.com`)
  - BLACKDUCK_API_TOKEN - Black Duck API Token including scan permissions
- Ensure additional options to run successful Synopsys Detect dependency scans have been specified (either as environment variables or using the `detect_opts` parameter). For example, you may need to modify the package manager search depth, or exclude specific package managers.

For the secondary package managers:
- Only Linux runners are supported
- Ensure the required package manager(s) are installed and available on the PATH within the Action

## Usage

The action can either run as a Docker container which is downloaded dynamically or as a python package installed locally, and supports GitHub-hosted and Self-hosted Linux runners.

The action has 3 independent modes of operation intended to be used for different GitHub activities:
- For a Pull Request, if there are security policy violations, add a comment with information on the vulnerabilities and set the check status (all supported package managers)
- For a Commit/Push, if there are security policy violations, create fix Pull Requests to upgrade the vulnerable direct dependencies (only for the primary package managers listed above) and set the check status 
- For any activity, if there are security policy violations, create a SARIF output file for import as code security issues in Github (all supported package managers)

Add steps to run the utility for the specific scenarios you wish to support.

## Github Action for Primary Package Managers

Adding the utility as a GitHub Action will support creating comments on Pull Requests or creating fix PRs to upgrade vulnerable direct dependencies for the primary package managers. The action can also fail the code scan check.

The following step would need to be added to a Github Action for projects using the primary package managers:

```yaml
    - name: Black Duck security scan
      uses: matthewb66/blackduck-scan-directguidance@v4
      with:
        url: ${{ secrets.BLACKDUCK_URL }}
        token: ${{ secrets.BLACKDUCK_API_TOKEN }}
        upgrade_major: true
      env:
        GITHUB_TOKEN: ${{ github.token }}
```

See below for full descriptions of all available parameters.

## Creating SARIF for Import as GitHub Code Scanning Alerts - Primary Package Managers

This operation mode will create a GitHub SARIF output file documenting vulnerable direct dependencies (and vulnerable child dependencies) for the primary package managers listed above.

The `sarif` parameter is used to indicate that a SARIF file should be created. Note that specifying the `sarif` parameter will stop the other operation modes from running by default.
See the FAQs below for how to run the other operation modes in addition to SARIF output.

The following step would need to be added to a Github Action to create the SARIF file `blackduck-sarif.json`:

```yaml
    - name: Black Duck security scan SARIF
      uses: matthewb66/blackduck-scan-directguidance@v4
      with:
        url: ${{ secrets.BLACKDUCK_URL }}
        token: ${{ secrets.BLACKDUCK_API_TOKEN }}
        upgrade_major: true
        sarif: blackduck-sarif.json  
      env:
        GITHUB_TOKEN: ${{ github.token }}
```

You could then add the following additional step to import the SARIF file as code scanning alerts:

```yaml
    - name: "Check file existence"
      id: check_files
      uses: andstor/file-existence-action@v1
      with:
        files: "blackduck-sarif.json"
    - name: Upload SARIF file
      if: steps.check_files.outputs.files_exists == 'true'
      uses: github/codeql-action/upload-sarif@v1
      with:
        sarif_file: blackduck-sarif.json
```

## Supported Parameters

The Black Duck Scanning action has a number of input parameters that can be passed using `with`. All input parameters have default vaules that should ensure reasonable default behavior.

| Property            | Default              | Description                                                                                                                                                                                                            |
|---------------------|----------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| trustcert           | false                | Trust the certificate from the BD server (required if certificate is not fully signed)                                                                                                                                 |
| mode                | rapid                | Run either an `intelligent` scan (comprehensive, will update project version in BD server) or `rapid` scan (runs in seconds, ephemeral - use this to support the main functions of this action)                        |
| comment_on_pr       | false                | Leave a comment on the pull request with the reported issues - if specified and set to true, will override the automatic detection of the event type and stop fix PRs from being created                               |
| fix_pr              | false                | Generate a fix pull request if a vulnerable componenent has an available upgrade path  - if specified and set to true, will override the automatic detection of the event type and stop PR comments from being created |
| upgrade_major       | false                | Include upgrades that are beyond the current major version of the component being used - note, this can introduce a breaking change if the component's APIs are sufficiently different                                 |
| sarif               | blackduck-sarif.json | Output results in SARIF file suitable for import into GitHub as code scanning alerts                                                                                                                                   |
| incremental_results | false                | Set to `true` to filter the output to only report on newly introduced components (do not report on any vulnerabilities on component versions previously detected in the project)                                       |
| debug               | 0                    | Set to value `9` to see debug messages from the action                                                                                                                                                                 |
| no_files_check      | false                | Skip the validation of the changed files - by default this check will terminate the action if no package manager config files have been changed in the coomit/pull request                                             |
| detect_opts         | N/A                  | Add Synopsys Detect scan options in a comma-delimited list (e.g. `detect.detector.buildless=true,detect.maven.buildless.legacy.mode=false`)                                                                            | 

## Overall Example Yaml - Primary Package Managers

The following YAML file shows the usage of the scan action for multiple workflows within an Action including the ability to run a full (intelligent) scan manually:

```yaml
  name: Scan a project with Black Duck
  
  on:
    push:
      branches: [ main ]
    pull_request:
      branches: [ main ]
    workflow_dispatch:
  
  jobs:
    blackduck:
      runs-on: ubuntu-latest
      steps:
      
      - name: Checkout the code
        uses: actions/checkout@v2
        
      # Runs a Black Duck intelligent scan manually
      # This will run a "full" or "intelligent" scan, logging new components in the Black Duck Hub server
      # in order to provide real time notifications when new vulnerabilities are reported.
      - name: Run Baseline Black Duck Scan (manual, workflow dispatch)
        if: ${{github.event_name == 'workflow_dispatch'}}
        uses: matthewb66/blackduck-scan-directguidance@v4
        with:
          url: ${{ secrets.BLACKDUCK_URL }}
          token: ${{ secrets.BLACKDUCK_API_TOKEN }}
          mode: intelligent
          
      # Runs a Black Duck rapid scan for pull request/commit/push
      - name: Run Black Duck security scan on PR/commit/push
        uses: matthewb66/blackduck-scan-directguidance@v4
        with:
          url: ${{ secrets.BLACKDUCK_URL }}
          token: ${{ secrets.BLACKDUCK_API_TOKEN }}
        env:
          # Pass the GitHub token to the script in order to create PRs
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}        
```

## Secondary Package Managers - Usage

If you are scanning a project using at least one secondary package manager (see list above), then you need to deploy this utility as a Python package.
The fix Pull Request operation mode is not supported for secondary package managers, and any upgrade guidance is limited to the individual package (will not include upgrading any vulnerable child dependencies).

```yaml
  - name: Set up Python 3.9
    uses: actions/setup-python@v2
    with:
      python-version: 3.9

  - name: Install dependencies
    run: |
      python -m pip install --upgrade pip
      pip install -i https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple blackduck_scan_directguidance
  - name: Run DirectGuidance Scan
    run: |
      blackduck-scan-directguidance --token ${{ secrets.BLACKDUCK_API_TOKEN }} --url ${{ secrets.BLACKDUCK_URL }} --upgrade_major true
```

# Support

For questions and comments, please contact us via the [Polaris Integrations Forum](https://community.synopsys.com/s/topic/0TO2H000000gM3oWAE/polaris-integrations).

# FAQs
## How to set the BD project/version names in scans
The project and version names are not required for Rapid scans unless you want to compare the scan against a previous Full scan.
If so, use the `detect_opts` paramater to specify additional scan arguments, for example:
```yaml
    - name: Black Duck security scan
      uses: matthewb66/blackduck-scan-directguidance@v4
      with:
        url: ${{ secrets.BLACKDUCK_URL }}
        token: ${{ secrets.BLACKDUCK_API_TOKEN }}
        upgrade_major: true
        detect_opts: detect.project.name=MYPROJECT,detect.project.version.name=MYVERSION
      env:
        GITHUB_TOKEN: ${{ github.token }}
```

## The scan is empty
Black Duck Rapid scan looks for supported package manager config files in the top-level folder of the repo.
If your project only has config files in sub-folders, use the parameter `detect_opts` to specify the scan option `detect.detector.search.depth=1`. Change the depth depending on the folder depth to traverse (a value of 1 would indicate 1 level of sub-folders).

## Cannot connect to Black Duck server due to certificate issues
Set the parameter `trustcert` to `true` to accept the unsigned server certificate

## How to output SARIF and Fix PR or Comment on PR operation modes together
By default the action event-type defines what operation mode will be run.
Specifying the paramater `sarif` will stop the other operation modes from running.
If you wish to output SARIF in addition to comment on PR in the same step, use the following step logic:

```yaml
    - name: Black Duck security scan for Pull Request
      if: ${{github.event_name == 'pull_request'}}
      uses: matthewb66/blackduck-scan-directguidance@v4
      with:
        url: ${{ secrets.BLACKDUCK_URL }}
        token: ${{ secrets.BLACKDUCK_API_TOKEN }}
        comment_on_pr: true
        upgrade_major: true
        sarif: blackduck-sarif.json  
      env:
        GITHUB_TOKEN: ${{ github.token }}
```

If you wish to output SARIF in addition to fix PR in the same step, use the following step logic:

```yaml
    - name: Black Duck security scan for Pull Request
      if: ${{github.event_name == 'push'}}
      uses: matthewb66/blackduck-scan-directguidance@v4
      with:
        url: ${{ secrets.BLACKDUCK_URL }}
        token: ${{ secrets.BLACKDUCK_API_TOKEN }}
        fix_pr: true
        upgrade_major: true
        sarif: blackduck-sarif.json  
      env:
        GITHUB_TOKEN: ${{ github.token }}
```
