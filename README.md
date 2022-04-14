# Community Black Duck GitHub Scan Action

## Overview

This is a community supported [GitHub Action](https://github.com/features/actions) for launching Black Duck SCA (OSS vulnerability analysis) scans as part of a GitHub CI/CD workflow, offering a number of workflow use cases:
- Run Black Duck Synopsys Detect scans within a GitHub Action
- For `Pull Requests`, optionally leave comments on a pull request that identify components violating configured security policies and offer upgrade guidance (all supported package managers)
- For `Commits/Pushes`, identify the direct dependencies violating security policies and optionally create new fix pull requests with available upgrades including for vulnerable child dependencies (primary package managers only - see below)
- Optionally report only newly introduced security policy violations (as compared against the last FULL scan)
- Optionally export Black Duck security policy violations via SARIF for subsequent import as code scanning alerts in GitHub (requires Advanced Security subscription in GitHub)
- Break the build if security policies are not met

Black Duck RAPID scan policies are used to determine vulnerabilities to be reported/fixed, allowing specific vulnerability severities and types to be covered. See the Black Duck User Guide within your server for more information on configuring policies.

This script is provided under an OSS license (specified in the LICENSE file) and has been developed by Synopsys field engineers as a contribution to the Synopsys user community. Please direct questions and comments to the [Black Duck Integrations Forum](https://community.synopsys.com/s/topic/0TO34000000gGZnGAM/black-duck-integrations) in the Synopsys user community.

## Quick Start Guide

Follow these quick start steps to implement this utility in a GitHub repository as a GitHub Action.

1. Add GitHub Repository secrets (Settings-->Secrets-->Actions:
   1. `BLACKDUCK_URL` with the Black Duck server URL
   2. `BLACKDUCK_API_TOKEN` with the Black Duck API token
   
2. Create at least 1 security policy for RAPID scan in the Black Duck server:
   1. Use `Manage-->Policy Management`
   2. Ensure `Scan Mode` is set to `Rapid` (if you wish to use incremental scanning set both `Rapid` and `Full` scan types)
   3. Add a `Component Conditions` check for vulnerabilities (for example `Highest Vulnerability Score >= 7.0`)
   
3. Create a new Action in your GitHub repository:
   1. Select `Actions` tab
   2. If no Actions defined, then select `set up a workflow yourself` or select `New Workflow` to add a new Action
   3. Delete the entire `jobs:` section in the YAML and replace with relevant `jobs:` section for this Action - see next step
   
4. Check the package managers used in your repository:
   1. If only primary package managers are used (npm, lerna, yarn, pnpm, nuget, maven) then use the [YAML for primary package managers](#Overall-Example-Yaml:-Primary-Package-Managers) below
   2. If one or more secondary package managers are used (including Conan, Conda, Dart, GoLang, Hex, Pypi) then use the [YAML for secondary package managers](#Overall-Example-Yaml:-Secondary-Package-Managers) below
   
5. OPTIONAL The Black Duck project and version names used for the scan will be extracted from Git by default; if you want to define specific project and version names see the answer in the FAQ section below

6. Commit the action configuration YAML file (note that the Black Duck Action should run immediately due to the commit of a new file, but there will be no security scan as no package manager file was changed)

7. Manually run an intelligent (full) scan by selecting `Actions-->Select your new workflow-->Click on Run workflow option` within GitHub

8. Thereafter, where a package manager config file is changed within a Pull Request or Commit/push to the master/main branch, the Black Duck Action should scan for security policy violations and update comments or create Fix PRs

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

The utility can support multiple package managers in a single project, although you need to ensure you choose the correct deployment mode (for primary or secondary package managers) based on the full list. For example, if you have a project using `Maven`, `npm` and `Pypi`, you will need to use the secondary package manager operation mode throughout (installing the utility as a pip package), unless you exclude the secondary package managers by specifying Synopsys Detect options (in this case `pypi`).

The following table shows the functionality available for the supported package managers:

| Package Manager | Comment on Pull Request | Create Fix PRs for vulnerable direct dependencies | Output SARIF for code security check | Run intelligent (full) scan |
|-----|---|---|---|---|
| | Event Type: _pull_request_ | Event Type: _push_ | Event Types: _all_ | Event Types: _all_ |
| | Scan Type: _rapid_ | Scan Type: _rapid_ | Scan Type: _rapid_ | Scan Type: _intelligent_ |
| npm    | yes | yes | yes | yes |
| lerna  | yes | yes | yes | yes |
| yarn   | yes | yes | yes | yes |
| pnpm   | yes | yes | yes | yes |
| nuget  | yes | yes | yes | yes |
| maven  | yes | yes | yes | yes |
| conan  | yes |  | yes | yes |
| conda  | yes |  | yes | yes |
| dart   | yes |  | yes | yes |
| golang | yes |  | yes | yes |
| hex    | yes |  | yes | yes |
| pypi   | yes |  | yes | yes |

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

The following step would need to be added to a Github Action for projects using the primary package managers and will run as a Docker action:

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

The `sarif` parameter is used to indicate that a SARIF file should be created. Note that specifying the `sarif` parameter will stop the other operation modes (`fix_pr` or `comment_on_pr`) from running automatically.
See the FAQs below for how to run the other operation modes in addition to SARIF output.

The following step would need to be added to a Github Action to create the SARIF file `blackduck-sarif.json` and will run as a Docker action:

```yaml
    - name: Black Duck security scan SARIF
      uses: matthewb66/blackduck-scan-directguidance@v4
      with:
        bd_url: ${{ secrets.BLACKDUCK_URL }}
        bd_token: ${{ secrets.BLACKDUCK_API_TOKEN }}
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

The Black Duck Scanning action has a number of input parameters that can be passed using `with`. All input parameters have default values that should ensure reasonable default behavior.

| Property            | Default              | Description                                                                                                                                                                                                            |
|---------------------|----------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| bd_url              |                  | The Black Duck server URL (for example `https://server.blackduck.synopsys.com`)                                                                                                                                        |
| bd_token            |                 | The Black Duck API token (create under `User-->My Access Tokens` in the server UI)                                                                                                                                     |
| bd_trustcert        | false                | Trust the certificate from the BD server (required if certificate is not fully signed)                                                                                                                                 |
| mode                | rapid                | Run either an `intelligent` scan (comprehensive, will update project version in BD server) or `rapid` scan (runs in seconds, ephemeral - use this to support the main functions of this action)                        |
| project             |                  | Black Duck project name. Not required for Rapid scans, but can be specified for BOM comparison against a previous full scan when `incremental_results` is set to true. |
| version             |                  | Black Duck version name. Not required for Rapid scans, but can be specified for BOM comparison against a previous full scan when `incremental_results` is set to true. |
| comment_on_pr       | false                | Leave a comment on the pull request with the reported issues - if specified and set to true, will override the automatic detection of the event type and stop fix PRs from being created                               |
| fix_pr              | false                | Generate a fix pull request if a vulnerable component has an available upgrade path; if specified and set to true, will override the automatic detection of the event type and stop PR comments from being created |
| upgrade_major       | false                | Include upgrades that are beyond the current major version of the component being used - note, this can introduce a breaking change if the component's APIs are sufficiently different                                 |
| sarif               | blackduck-sarif.json | Output results in SARIF file suitable for import into GitHub as code scanning alerts                                                                                                                                   |
| incremental_results | false                | Set to `true` to filter the output to only report on newly introduced components (uses the `--detect.blackduck.rapid.compare.mode=BOM_COMPARE` option and compares configured policies against the previous full scan)   |
| output_folder       | blackduck-output     | Temporary location to create output scan data (will be deleted after scan completion                                                                                                                                   |
| debug               | 0                    | Set to value `9` to see debug messages from the action                                                                                                                                                                 |
| no_files_check      | false                | Skip the validation of the changed files - by default this check will terminate the action if no package manager config files have been changed in the commit/pull request                                             |
| detect_opts         |                  | Specify Synopsys Detect scan options in a comma-delimited list without leading hyphens (e.g. `detect.detector.buildless=true,detect.maven.buildless.legacy.mode=false`)                                                | 

## Secondary Package Managers - Usage

If you are scanning a project which uses at least one secondary package manager (see list above), then you need to deploy this utility as a Python package.
The fix Pull Request operation mode is not supported for secondary package managers, and any upgrade guidance is limited to the individual package (will not include upgrading any vulnerable child dependencies).

The following YAML extract will add the scan utility as a step running as a python package installed locally:

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
         blackduck-scan-directguidance --bd_url ${{ secrets.BLACKDUCK_URL }} --bd_token ${{ secrets.BLACKDUCK_API_TOKEN }} --upgrade_major true
       env:
          # Pass the GitHub token to the script in order to create PRs
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

You may also need to add the option `--bd_trustcert true` to trust the server SSL certificate if not authenticated.

# Support

For questions and comments, please contact us via the [Black Duck Integrations Forum](https://community.synopsys.com/s/topic/0TO34000000gGZnGAM/black-duck-integrations).
Issues can also be raised in GitHub.

Specify the action parameter `debug: 9` to output full logs from the action execution and include logs within the issue or community post.

#Overall Example Yaml: Primary Package Managers

The following YAML file shows the configuration of the scan action for primary package managers including the ability to run a full (intelligent) scan manually:

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
          bd_url: ${{ secrets.BLACKDUCK_URL }}
          bd_token: ${{ secrets.BLACKDUCK_API_TOKEN }}
          mode: intelligent
        env:
          GITHUB_TOKEN: ${{ github.token }}
          
      # Runs a Black Duck rapid scan for pull request/commit/push
      - name: Run Black Duck security scan on PR/commit/push
        if: ${{github.event_name != 'workflow_dispatch'}}
        uses: matthewb66/blackduck-scan-directguidance@v4
        with:
          bd_url: ${{ secrets.BLACKDUCK_URL }}
          bd_token: ${{ secrets.BLACKDUCK_API_TOKEN }}
          upgrade_major: true
        env:
          # Pass the GitHub token to the script in order to create PRs
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}        
```

#Overall Example Yaml: Secondary Package Managers

The following YAML file shows the usage of the scan action for secondary package managers including the ability to run a full (intelligent) scan manually:

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
        
      # Install Python 3.9 for Black Duck Action
      - name: Set up Python 3.9
        uses: actions/setup-python@v2
        with:
          python-version: 3.9
   
      # Install Dependencies for Black Duck Action
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -i https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple blackduck_scan_directguidance
 
      # Run manual full/intelligent scan
      - name: Run Black Duck Full Scan
        if: ${{github.event_name == 'workflow_dispatch'}}
        run: |
          blackduck-scan-directguidance --bd_url ${{ secrets.BLACKDUCK_URL }} --bd_token ${{ secrets.BLACKDUCK_API_TOKEN }} --mode intelligent
        env:
          # Pass the GitHub token to the script in order to create PRs
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}        

      # Run Black Duck rapid scan for pull request/commit/push
      - name: Run Black Duck Directguidance Scan
        if: ${{github.event_name != 'workflow_dispatch'}}
        run: |
          blackduck-scan-directguidance --bd_url ${{ secrets.BLACKDUCK_URL }} --bd_token ${{ secrets.BLACKDUCK_API_TOKEN }} --upgrade_major true
        env:
          # Pass the GitHub token to the script in order to create PRs
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}        
 ```

# FAQs

## There are no results shown
Rapid scans report security policy violations (not all vulnerabilities).
Ensure you have created security policy violations configured for RAPID scan mode in the Black Duck server

The Black Duck dependency scan looks for supported package manager config files in the top-level folder of the repo.
If your project only has config files in sub-folders, use the action parameter `detect_opts: detect.detector.search.depth=1`. Change the depth depending on the folder depth to traverse (for example a value of 1 would indicate depth 1 of sub-folders).

## Cannot connect to Black Duck server due to certificate issues
Check the `bd_url` parameter. Also try setthing the action parameter `trustcert: true` to accept the unsigned server certificate.

## How to set the BD project/version names in scans
The project and version names are not required for Rapid scans unless you want to compare the scan against a previous Full scan.
If so, use the `project` and/or `version` action parameters to specify, for example:
```yaml
    - name: Black Duck Rapid security scan
      uses: matthewb66/blackduck-scan-directguidance@v4
      with:
        bd_url: ${{ secrets.BLACKDUCK_URL }}
        bd_token: ${{ secrets.BLACKDUCK_API_TOKEN }}
        upgrade_major: true
        project: PROJECT
        version: VERSION
      env:
        GITHUB_TOKEN: ${{ github.token }}
```

## How to output SARIF and Fix PR or Comment on PR operation modes together
By default the action event-type defines what operation mode will be run.
Specifying the paramater `sarif` will stop the other operation modes from running.
If you wish to output SARIF in addition to comment on PR in the same step, use the following step logic:

```yaml
    - name: Black Duck Rapid security scan for Pull Request
      if: ${{github.event_name == 'pull_request'}}
      uses: matthewb66/blackduck-scan-directguidance@v4
      with:
        bd_url: ${{ secrets.BLACKDUCK_URL }}
        bd_token: ${{ secrets.BLACKDUCK_API_TOKEN }}
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
        bd_url: ${{ secrets.BLACKDUCK_URL }}
        bd_token: ${{ secrets.BLACKDUCK_API_TOKEN }}
        fix_pr: true
        upgrade_major: true
        sarif: blackduck-sarif.json  
      env:
        GITHUB_TOKEN: ${{ github.token }}
```

## Incremental scan using incremental_results option returns no results

This parameter uses the Synopsys Detect BOM_COMPARE mode to compare a Rapid scan against the results of a previous Intelligent (full) scan.

To use this mode, you will need to ensure that security policies are configured for *both* Rapid and Full scan types. See the Synopsys Detect [documentation](https://detect.synopsys.com/doc) for more details.
