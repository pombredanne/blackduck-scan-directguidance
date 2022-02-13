import re
import os

from bdscan import classComponent


class NugetComponent(classComponent.Component):
    def __init__(self, compid, name, version, ns):
        super().__init__(compid, name, version, ns)

    def get_http_name(self):
        bdio_name = f"http:" + re.sub(":", "/", self.compid)
        return bdio_name

    @staticmethod
    def normalise_dep(dep):
        #
        # Replace / with :
        if dep.find('http:') == 0:
            dep = dep.replace('http:', '').replace('nuget/', 'nuget:')
        return dep

    def prepare_upgrade(self, index):
        proj_contents = ''
        if not os.path.isfile('test.csproj'):
            proj_contents = f'''<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <OutputType>Exe</OutputType>
    <TargetFramework>netcoreapp3.1</TargetFramework>
  </PropertyGroup>'''

        proj_contents += f'''  <ItemGroup>
    <PackageReference Include="{self.name}" Version="{self.potentialupgrades[index]}" />
  </ItemGroup>
'''
        try:
            with open('test.csproj', "w") as fp:
                fp.write(proj_contents)
        except Exception as e:
            print(e)
            return False
        return True

    @staticmethod
    def finalise_upgrade():
        try:
            with open('test.csproj', "a") as fp:
                fp.write('</Project>\n')
        except Exception as e:
            print(e)
        return
