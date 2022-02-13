import re
import os
# import shutil
import tempfile
import hashlib
import sys
import json

from BlackDuckUtils import Utils
from bdscan import classMavenComponent
from bdscan import classNugetComponent
from bdscan import classNpmComponent
from bdscan import globals


class ComponentList:
    md_directdeps_header = [
        "",
        "## SUMMARY Direct Dependencies with vulnerabilities:",
        "",
        f"| Direct Dependency | Num Direct Vulns | Max Direct Vuln Severity | Num Indirect Vulns "
        f"| Max Indirect Vuln Severity | Upgrade to |",
        "| --- | --- | --- | --- | --- | --- |"
    ]

    def __init__(self):
        self.compids = []
        self.components = []

    def add(self, compid):
        if compid in self.compids:
            return self.components[self.compids.index(compid)]

        arr = re.split('[/:]', compid)

        ns = arr[0]
        if ns == 'npmjs':
            component = classNpmComponent.NpmComponent(compid, arr[1], arr[2], ns)
        elif ns == 'nuget':
            component = classNugetComponent.NugetComponent(compid, arr[1], arr[2], ns)
        elif ns == 'maven':
            component = classMavenComponent.MavenComponent(compid, arr[1], arr[2], arr[3], ns)
        else:
            raise ValueError(f'Unsupported package manager {ns}')
        self.components.append(component)
        self.compids.append(compid)

        return component

    def set_data_in_comp(self, compid, fieldname, data):
        if compid in self.compids:
            index = self.compids.index(compid)
            comp = self.components[index]
            comp.set_data(fieldname, data)

    def add_origins_to_comp(self, compid, ver, data):
        if compid in self.compids:
            index = self.compids.index(compid)
            comp = self.components[index]
            comp.set_origins(ver, data)

    def get_component(self, compid):
        if compid in self.compids:
            return self.components[self.compids.index(compid)]
        return None

    def find_upgrade_versions(self, upgrade_major):
        for comp in self.components:
            comp.find_upgrade_versions(upgrade_major)

    def validate_upgrades(self):
        detect_jar = Utils.get_detect_jar()
        bd_output_path = 'upgrade-tests'

        detect_connection_opts = [
            f'--blackduck.url={globals.args.url}',
            f'--blackduck.api.token={globals.args.token}',
            "--detect.blackduck.scan.mode=RAPID",
            "--detect.detector.buildless=true",
            # detect_connection_opts.append("--detect.maven.buildless.legacy.mode=false")
            f"--detect.output.path={bd_output_path}",
            "--detect.cleanup=false"
        ]
        if globals.args.trustcert:
            detect_connection_opts.append('--blackduck.trust.cert=true')

        max_upgrade_count = 0
        for comp in self.components:
            if len(comp.potentialupgrades) > max_upgrade_count:
                max_upgrade_count = len(comp.potentialupgrades)
        upgrade_index = 0
        while upgrade_index <= max_upgrade_count:
            print(f'BD-Scan-Action: Validating upgrades cycle {upgrade_index+1} ...')
            # dirname = "snps-upgrade-" + direct_name + "-" + direct_version
            dirname = tempfile.TemporaryDirectory()
            # os.mkdir(dirname)
            origdir = os.getcwd()
            os.chdir(dirname.name)

            test_upgrade_list = []
            test_origdeps_list = []
            for comp in self.components:
                if comp.goodupgrade == '' and len(comp.potentialupgrades) > upgrade_index:
                    if comp.prepare_upgrade(upgrade_index):

                        test_upgrade_list.append([comp.org, comp.name, comp.potentialupgrades[upgrade_index]])
                        test_origdeps_list.append(comp.compid)

            pm_list = []
            for comp in self.components:
                if comp.pm not in pm_list:
                    pm_list.append(comp.pm)
                    comp.finalise_upgrade()

            output = False
            if globals.debug > 0:
                output = True
            pvurl, projname, vername, retval = Utils.run_detect(detect_jar, detect_connection_opts, output)

            if retval == 3:
                # Policy violation returned
                rapid_scan_data, dep_dict, direct_deps_vuln = Utils.process_scan(
                    bd_output_path, globals.bd, [], incremental=False, upgrade_indirect=False
                )
                # process_scan(scan_folder, bd, baseline_comp_cache, incremental, upgrade_indirect):

                last_vulnerable_dirdeps = []
                for vulndep in direct_deps_vuln.components:
                    #
                    # find comp in depver_list
                    for upgradedep, origdep in zip(test_upgrade_list, test_origdeps_list):
                        if upgradedep[1] == vulndep.name:
                            # vulnerable_upgrade_list.append([origdep, upgradedep[2]])
                            last_vulnerable_dirdeps.append(origdep)
                            break
            elif retval != 0:
                # Other Detect failure - no upgrades determined
                last_vulnerable_dirdeps = []
                for upgradedep, origdep in zip(test_upgrade_list, test_origdeps_list):
                    # vulnerable_upgrade_list.append([origdep, upgradedep[2]])
                    last_vulnerable_dirdeps.append(origdep)
            else:
                # Detect returned 0
                # All tested upgrades not vulnerable
                last_vulnerable_dirdeps = []

            for lcomp in self.components:
                if (lcomp.compid in test_origdeps_list and lcomp.compid not in last_vulnerable_dirdeps and
                        len(lcomp.potentialupgrades) >= upgrade_index and lcomp.goodupgrade == ''):
                    lcomp.set_data('goodupgrade', lcomp.potentialupgrades[upgrade_index])
            os.chdir(origdir)
            dirname.cleanup()
            upgrade_index += 1

        return

    def check_in_baselineproj(self, baseline_data):
        for basecomp in baseline_data:
            for baseorig in basecomp['origins']:
                if baseorig['externalNamespace'] != '':
                    basecompid = f"{baseorig['externalNamespace']}:{baseorig['externalId']}"
                else:
                    basecompid = baseorig['externalId']
                if basecompid in self.compids:
                    comp = self.get_component(basecompid)
                    comp.set_data('inbaseline', True)
                break

    # def check_projfiles(self):
    #     for comp in self.components:
    #         package_file, package_line = comp.get_package_file()
    #         if package_file == 'Unknown' or package_line <= 0:
    #             # component doesn't exist in pkgfile - skip
    #             continue
    #         package_file = Utils.remove_cwd_from_filename(package_file)
    #         if package_file not in comp.projfiles:
    #             comp.set_data('projfiles', package_file)
    #             comp.set_data('projfilelines', package_line)

    def get_children(self, dep_dict):
        for comp in self.components:
            children = []
            for alldep in dep_dict.keys():
                if comp.compid in dep_dict[alldep]['directparents']:
                    children.append(alldep)
            comp.set_data('children', children)

    def calc_vulns(self, rapid_scan_data):
        for comp in self.components:
            max_vuln_severity = 0
            max_vuln_severity_children = 0
            existing_vulns = []
            existing_vulns_children = []

            for rscanitem in rapid_scan_data['items']:
                child = False
                parent = False
                if rscanitem['componentIdentifier'] == comp.compid:
                    parent = True
                else:
                    for childid in comp.children:
                        if rscanitem['componentIdentifier'] == childid:
                            child = True
                            break

                if not parent and not child:
                    continue

                for vuln in rscanitem['policyViolationVulnerabilities']:
                    # print(f"vuln={vuln}")
                    parent_name = '-'
                    parent_ver = '-'
                    if parent:
                        if vuln['name'] in existing_vulns:
                            continue
                        if max_vuln_severity < vuln['overallScore']:
                            max_vuln_severity = vuln['overallScore']
                    elif child:
                        if vuln['name'] in existing_vulns_children:
                            continue
                        if max_vuln_severity_children < vuln['overallScore']:
                            max_vuln_severity_children = vuln['overallScore']
                        parent_name = comp.name
                        parent_ver = comp.version
                    child_ns, child_name, child_ver = comp.parse_compid(rscanitem['componentIdentifier'])

                    desc = vuln['description'].replace('\n', ' ')
                    if len(desc) > 200:
                        desc = desc[:196]
                        desc += ' ...'
                    name = vuln['name']
                    link = f"{globals.args.url}/api/vulnerabilities/{name}/overview"
                    vulnname = f'<a href="{link}" target="_blank">{name}</a>'

                    vuln_item = [
                            f"{parent_name}/{parent_ver}",
                            f"{child_name}/{child_ver}",
                            vulnname,
                            str(vuln['overallScore']),
                            vuln['violatingPolicies'][0]['policyName'],
                            desc,
                        ]
                    if parent and vuln['name'] not in existing_vulns:
                        comp.add_vuln(name, vuln_item)
                        comp.set_data('maxvulnscore', max_vuln_severity)
                    if child and vuln['name'] not in existing_vulns_children:
                        comp.add_child_vuln(name, vuln_item)
                        comp.set_data('maxchildvulnscore', max_vuln_severity_children)

            # Sort the tables
            # vuln_list = sorted(vuln_list, key=itemgetter(3), reverse=True)
            # vuln_list_children = sorted(vuln_list_children, key=itemgetter(3), reverse=True)
        return

    def write_sarif(self, sarif_file):
        sarif_result = []
        sarif_tool_rule = []

        for comp in self.components:
            # md_comp_vulns_table = comp.md_table()
            projfile = ''
            projfileline = 0
            if len(comp.projfiles) > 0:
                projfile = comp.projfiles[0]
                projfileline = comp.projfilelines[0]

            sarif_result.append(
                {
                    'ruleId': comp.name,
                    'message': {
                        'text': comp.shorttext()
                    },
                    'locations': [
                        {
                            'physicalLocation': {
                                'artifactLocation': {
                                    'uri': projfile,
                                },
                                'region': {
                                    'startLine': projfileline,
                                }
                            }
                        }
                    ],
                    'partialFingerprints': {
                        'primaryLocationLineHash': hashlib.sha224(b"{compid}").hexdigest(),
                    }
                }
            )

            if comp.maxchildvulnscore >= 7 or comp.maxvulnscore >= 7:
                level = "error"
            elif comp.maxchildvulnscore >= 4 or comp.maxvulnscore >= 4:
                level = "warning"
            else:
                level = "note"

            if comp.goodupgrade != '':
                uhelp = f"{comp.longtext_md()}\n\nRecommended to upgrade to version {comp.goodupgrade}.\n\n"
            else:
                uhelp = f"{comp.longtext_md()}\n\nNo upgrade available at this time.\n\n"

            sarif_tool_rule.append(
                {
                    'id': comp.name,
                    'shortDescription': {
                        'text': comp.shorttext(),
                    },
                    'fullDescription': {
                        'text': comp.longtext(),
                    },
                    'help': {
                        'text': '',
                        'markdown': uhelp,
                    },
                    'defaultConfiguration': {
                        'level': level,
                    },
                    'properties': {
                        'tags': ["security"],
                        'security-severity': str(comp.maxvulnscore)
                    }
                }
            )

        code_security_scan_report = {
            '$schema': "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json",
            'version': "2.1.0",
            'runs': [
                {
                    'tool': {
                        'driver': {
                            'name': 'Synopsys Black Duck',
                            'organization': 'Synopsys',
                            'version': globals.scan_utility_version,
                            'rules': sarif_tool_rule,
                        }
                    },
                    'results': sarif_result,
                }
            ],
        }
        try:
            with open(sarif_file, "w") as fp:
                json.dump(code_security_scan_report, fp, indent=4)
        except Exception as e:
            print(f"BD-Scan-Action: ERROR: Unable to write to SARIF output file '{sarif_file} - '" + str(e))
            sys.exit(1)

        return

    def get_comments(self):
        md_comments = self.md_directdeps_header[:]
        md_comp_tables = []
        for comp in self.components:
            md_comments.extend(comp.md_summary_table_row())
            md_comp_tables.append(comp.md_table())

        md_comments.append("\n\nVulnerable Direct dependencies listed below:\n\n")
        md_comments.extend(md_comp_tables)

        return md_comments
