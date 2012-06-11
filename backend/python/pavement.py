#  ***** BEGIN LICENSE BLOCK *****
# Version: MPL 1.1
# 
# The contents of this file are subject to the Mozilla Public License  
# Version
# 1.1 (the "License"); you may not use this file except in compliance  
# with
# the License. You may obtain a copy of the License at
# http://www.mozilla.org/MPL/
# 
# Software distributed under the License is distributed on an "AS IS"  
# basis,
# WITHOUT WARRANTY OF ANY KIND, either express or implied. See the  
# License
# for the specific language governing rights and limitations under the
# License.
# 
# The Original Code is Bespin.
# 
# The Initial Developer of the Original Code is Mozilla.
# Portions created by the Initial Developer are Copyright (C) 2009
# the Initial Developer. All Rights Reserved.
# 
# Contributor(s):
# 
# ***** END LICENSE BLOCK *****
# 

import re
import os

from setuptools import find_packages
from paver.setuputils import find_package_data

from paver.easy import *
from paver import setuputils
setuputils.install_distutils_tasks()


execfile(os.path.join('bespin', '__init__.py'))

options(
    setup=Bunch(
        name="BespinServer",
        version=VERSION,
        packages=find_packages(),
        package_data=find_package_data('bespin', 'bespin', 
                                only_in_packages=False),
        entry_points="""
[console_scripts]
bespin_worker=bespin.queue:process_queue
queue_stats=bespin.queuewatch:command
telnet_mobwrite=bespin.mobwrite.mobwrite_daemon:process_mobwrite
bespin_mobwrite=bespin.mobwrite.mobwrite_web:start_server
"""
    )
)

@task
@needs(['sdist'])
def production():
    """Gets things ready for production."""
    non_production_packages = set(["py", "WebTest", "boto", "virtualenv", 
                                  "Paver", "BespinServer", "nose",
                                  "path", "httplib2",
                                  "MySQL-python"])
    production = path("production")
    production_requirements = production / "requirements.txt"
    
    libs_dest = production / "libs"
    libs_dest.rmtree()
    libs_dest.mkdir()
    
    sdist_file = path("dist/BespinServer-%s.tar.gz" % options.version)
    sdist_file.move(libs_dest)
    
    ext_dir = path("ext")
    external_libs = []
    for f in ext_dir.glob("*"):
        f.copy(libs_dest)
        name = f.basename()
        name = name[:name.index("-")]
        non_production_packages.add(name)
        external_libs.append("libs/%s" % (f.basename()))
        
    lines = production_requirements.lines() if production_requirements.exists() else []
    
    requirement_pattern = re.compile(r'^(.*)==')
    
    i = 0
    found_packages = set()
    while i < len(lines):
        rmatch = requirement_pattern.match(lines[i])
        if rmatch:
            name = rmatch.group(1)
            found_packages.add(name)
            deleted = False
            for npp in non_production_packages:
                if name == npp or "BespinServer-tip" in npp:
                    del lines[i]
                    deleted = True
                    break
            if deleted:
                continue
        i+=1
    
    lines.append("libs/BespinServer-%s.tar.gz" % options.version)
    
    # path.py doesn't install properly via pip/easy_install
    lines.append("http://pypi.python.org/packages/source/p/path.py/"
        "path-2.2.zip#md5=941660081788282887f652510d80e64e")
        
    lines.append("http://httplib2.googlecode.com/files/httplib2-0.4.0.tar.gz")
    
    lines.append("http://pypi.python.org/packages/source/"
        "M/MySQL-python/MySQL-python-1.2.3c1.tar.gz")
    
    lines.extend(external_libs)
    production_requirements.write_lines(lines)
    
    call_pavement("production/pavement.py", "bootstrap")
    
