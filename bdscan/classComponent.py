import re
import os

from bdscan import utils


# from bdscan import globals


class Component:
    md_comp_vulns_hdr = \
        "\n| Parent | Child Component | Vulnerability | Score |  Policy Violated | Description | Current Ver |\n" \
        "| --- | --- | --- | --- | --- | --- | --- |\n"

    def __init__(self, compid, name, version, ns):
        self.ns = ns
        self.pm = ns
        self.org = ''  # Used in Maven
        self.name = name
        self.version = version
        self.compid = compid
        self.inbaseline = False
        self.projfiles = []
        self.projfilelines = []
        self.compdata = []
        self.versions = []
        self.upgradeguidance = []
        self.potentialupgrades = []
        self.goodupgrade = ''
        self.origins = {}
        self.children = []
        self.vulns = {}
        self.childvulns = {}
        self.maxvulnscore = 0
        self.maxchildvulnscore = 0
        self.vulnsummary = []

    def set_data(self, fieldname, data):
        if fieldname == 'projfiles':
            self.projfiles.append(data)
        elif fieldname == 'compdata':
            self.compdata = data
        elif fieldname == 'versions':
            self.versions = data
        elif fieldname == 'upgradeguidance':
            self.upgradeguidance = data
        elif fieldname == 'goodupgrade':
            self.goodupgrade = data
        elif fieldname == 'inbaseline':
            self.inbaseline = True
        elif fieldname == 'projfiles':
            self.projfiles.append(data)
        elif fieldname == 'projfilelines':
            self.projfilelines.append(data)
        elif fieldname == 'children':
            self.children = data
        elif fieldname == 'maxvulnscore':
            self.maxvulnscore = data
        elif fieldname == 'maxchildvulnscore':
            self.maxchildvulnscore = data
        elif fieldname == 'vulnsummary':
            self.vulnsummary.append(data)

    def add_vuln(self, vulnid, data):
        self.vulns[vulnid] = data

    def add_child_vuln(self, vulnid, data):
        self.childvulns[vulnid] = data

    def set_origins(self, ver, data):
        self.origins[ver] = data

    def check_ver_origin(self, ver):
        if len(self.origins) > 0 and ver in self.origins.keys():
            for over in self.origins[ver]:
                if 'originName' in over and 'originId' in over and over['originName'] == self.ns:
                    # 'org.springframework:spring-aop:3.2.10.RELEASE'
                    a_over = re.split('[:/]', over['originId'])
                    if a_over[0] == self.name and a_over[1] == self.version:
                        return True
        return False

    def find_upgrade_versions(self, upgrade_major):
        v_curr = utils.normalise_version(self.version)
        if v_curr is None:
            return

        future_vers = []
        for ver, url in self.versions[::-1]:
            v_ver = utils.normalise_version(ver)
            if v_ver is None:
                continue

            if self.check_ver_origin(ver):
                future_vers.append([ver, url])

        def find_next_ver(verslist, major, minor, patch):
            foundver = ''
            found_rels = [1000, -1, -1]

            for ver, url in verslist:
                v_ver = utils.normalise_version(ver)
                if major < v_ver.major < found_rels[0]:
                    found_rels = [v_ver.major, v_ver.minor, v_ver.patch]
                    foundver = ver
                elif v_ver.major == major:
                    if v_ver.minor > found_rels[1] and v_ver.minor > minor:
                        found_rels = [major, v_ver.minor, v_ver.patch]
                        foundver = ver
                    elif v_ver.minor == found_rels[1] and v_ver.patch > found_rels[2] and v_ver.patch > patch:
                        found_rels = [major, v_ver.minor, v_ver.patch]
                        foundver = ver

            return foundver, found_rels[0]

        #
        # Find the initial upgrade (either latest in current version major range or guidance_short)
        v_guidance_short = utils.normalise_version(self.upgradeguidance[0])
        v_guidance_long = utils.normalise_version(self.upgradeguidance[1])
        foundvers = []
        if v_guidance_short is None:
            # Find final version in current major range
            verstring, guidance_major_last = find_next_ver(future_vers, v_curr.major, v_curr.minor, v_curr.patch)
        else:
            verstring = self.upgradeguidance[0]
            guidance_major_last = v_guidance_short.major + 1
        if verstring != '':
            foundvers.append(verstring)

        if v_guidance_long is None:
            # Find final minor version in next major range
            verstring, guidance_major_last = find_next_ver(future_vers, guidance_major_last, -1, -1)
        else:
            verstring = self.upgradeguidance[1]
            guidance_major_last = v_guidance_long.major
        if verstring != '' and upgrade_major:
            foundvers.append(verstring)

        if upgrade_major:
            while len(foundvers) <= 3:
                verstring, guidance_major_last = find_next_ver(future_vers, guidance_major_last + 1, -1, -1)
                if verstring == '':
                    break
                foundvers.append(verstring)

        self.potentialupgrades = foundvers

    def prepare_upgrade(self, index):
        return

    def md_table(self):
        # md_comp_vulns_table = self.md_comp_vulns_hdr[:]
        md_comp_vulns_table = []
        for vulnid in self.vulns.keys():
            md_comp_vulns_table.append(self.vulns[vulnid])
        for vulnid in self.childvulns.keys():
            # sep = " | "
            md_comp_vulns_table.append(self.childvulns[vulnid])

        # sort the table here

        sep = ' | '
        md_table_string = ''
        for row in md_comp_vulns_table:
            md_table_string += '| ' + sep.join(row) + ' |\n'

        md_table_string = self.md_comp_vulns_hdr + md_table_string
        return md_table_string

    def shorttext(self):
        if len(self.vulns) > 0 and len(self.childvulns) > 0:
            shorttext = f"The direct dependency {self.name}/{self.version} has {len(self.vulns)} vulnerabilities " \
                        f"(max score {self.maxvulnscore}) and {len(self.childvulns)} vulnerabilities in child " \
                        f"dependencies (max score {self.maxchildvulnscore})."
        elif len(self.vulns) > 0 and len(self.childvulns) == 0:
            shorttext = f"The direct dependency {self.name}/{self.version} has {len(self.vulns)} vulnerabilities " \
                        f"(max score {self.maxvulnscore})."
        elif len(self.childvulns) > 0:
            shorttext = f"The direct dependency {self.name}/{self.version} has {len(self.childvulns.keys())} " \
                        f"vulnerabilities in child dependencies (max score {self.maxchildvulnscore})."
        else:
            shorttext = ''
        return shorttext

    def longtext(self):
        shorttext = self.shorttext()
        # md_comp_vulns_table = self.md_table()
        if len(self.vulns) > 0 and len(self.childvulns) > 0:
            longtext = f"{shorttext}\n\nList of direct vulnerabilities:\n{','.join(self.vulns.keys())}\n\n" \
                       f"List of indirect vulnerabilities:\n{','.join(self.childvulns.keys())} "
        elif len(self.vulns) > 0 and len(self.childvulns) == 0:
            longtext = f"{shorttext}\n\nList of direct vulnerabilities:\n{','.join(self.vulns.keys())}"
        elif len(self.childvulns) > 0:
            longtext = f"{shorttext}\n\nList of indirect vulnerabilities:\n{','.join(self.childvulns.keys())}"
        else:
            longtext = ''
        return longtext

    def longtext_md(self):
        shorttext = self.shorttext()
        md_table = self.md_table()
        longtext_md = shorttext + "\n\n" + md_table
        return longtext_md

    def get_projfile(self, projstring, allpoms):
        import urllib.parse
        arr = projstring.split('/')
        if len(arr) < 4:
            return ''

        projfile = urllib.parse.unquote(arr[3])
        if os.path.isfile(projfile):
            print(f'BD-Scan-Action: INFO: Found project file {projfile}')
            return utils.remove_cwd_from_filename(projfile)

    def get_projfile_linenum(self, filename):
        # if comp_ns == 'maven':
        #     return Mavenutils.get_pom_line(comp, ver, filename)
        # else:
        try:
            with open(filename, 'r') as f:
                for (i, line) in enumerate(f):
                    if self.name.lower() in line.lower():
                        return i
        except Exception as e:
            return -1
        return -1

    # def get_package_file(self):
    #     for package_file in self.projfiles:
    #         line = self.get_projfile_linenum(package_file)
    #         if line > 0:
    #             globals.printdebug(f"DEBUG: '{self.name}': PKG file'{package_file}' Line {line}")
    #             return utils.remove_cwd_from_filename(package_file), line
    #     return "Unknown", 0

    def md_summary_table_row(self):
        # | Direct Dependency | Changed | Num Direct Vulns | Max Direct Vuln Severity | Num Indirect Vulns
        # | Max Indirect Vuln Severity | Upgrade to |",
        if self.inbaseline:
            changed = 'No'
        else:
            changed = 'Yes'
        table = [
            f"{self.name}/{self.version}",
            changed,
            f"{len(self.vulns.keys())}",
            f"{self.maxvulnscore}",
            f"{len(self.childvulns.keys())}",
            f"{self.maxchildvulnscore}",
            f"{self.goodupgrade}"
        ]
        return table

    def upgrade_dependency(self):
        print(f'BD-Scan-Action: WARNING: Unable to upgrade component {self.name}/{self.version} - unsupported package '
              f'manager')
        return

    @staticmethod
    def finalise_upgrade():
        return

    @staticmethod
    def parse_compid(compid):
        arr = re.split('[:/]', compid)
        if len(arr) == 3:
            return arr[0], arr[1], arr[2]
        else:
            return '', '', ''
