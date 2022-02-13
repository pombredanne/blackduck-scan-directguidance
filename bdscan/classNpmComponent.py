import re
import os
import shutil

from bdscan import classComponent


class NpmComponent(classComponent.Component):
    def __init__(self, compid, name, version, ns):
        super().__init__(compid, name, version, ns)
        self.pm = 'npm'

    def get_http_name(self):
        bdio_name = f"http:" + re.sub(":", "/", self.compid, 1)
        return bdio_name

    @staticmethod
    def normalise_dep(dep):
        #
        # Replace / with :
        # return dep.replace('/', ':').replace('http:', '')
        dep = dep.replace('http:', '').replace(':', '|').replace('/', '|')
        # Check format matches 'npmjs:component/version'
        slash = dep.split('|')
        if len(slash) == 3:
            return f"{slash[0]}:{slash[1]}/{slash[2]}"
        return ''

    def prepare_upgrade(self, index):
        if shutil.which("npm") is None:
            print('BD-Scan-Action: ERROR: Unable to find npm executable to install packages - unable to test upgrades')
            return

        cmd = f"npm install {self.name}@{self.potentialupgrades[index]} --package-lock-only >/dev/null 2>&1"
        # cmd = f"npm install {comp}@{upgrade_version} --package-lock-only"
        # print(cmd)
        ret = os.system(cmd)

        if ret == 0:
            return True
        return False

    def get_projfile_linenum(self, filename):
        namestring = f'"{self.name.lower()}":'
        try:
            with open(filename, 'r') as f:
                for (i, line) in enumerate(f):
                    if namestring in line.lower():
                        return i
        except Exception as e:
            return -1
        return -1

