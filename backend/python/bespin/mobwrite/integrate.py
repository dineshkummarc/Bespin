#  ***** BEGIN LICENSE BLOCK *****
# Version: MPL 1.1
#
# The contents of this file are subject to the Mozilla Public License Version
# 1.1 (the "License"); you may not use this file except in compliance with
# the License. You may obtain a copy of the License at
# http://www.mozilla.org/MPL/
#
# Software distributed under the License is distributed on an "AS IS" basis,
# WITHOUT WARRANTY OF ANY KIND, either express or implied. See the License
# for the specific language governing rights and limitations under the License.
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

from bespin.database import User, get_project
import logging

log = logging.getLogger("mobwrite.integrate")


def get_username_from_handle(handle):
    """The handle added by the user (in controllers.py) is of the form
    {User.username}:{ip address}, which is what is expected for reporting on
    collaborators, but error messages just want the username part"""
    (requester, sep, ipstr) = handle.partition(':')
    return requester


class Access:
    """Constants for use by Persister"""
    Denied = 1
    ReadOnly = 2
    ReadWrite = 3


class Persister:
    """A plug-in for mobwrite_daemon that diverts calls to Bespin"""

    def load(self, name):
        """Load a temporary file by extracting the project from the filename
        and calling project.get_temp_file"""
        try:
            (project, path) = self._split(name)
            log.debug("loading temp file for: %s/%s", project.name, path)
            bytes = project.get_temp_file(path)
            # mobwrite gets things into unicode by doing bytes.encode("utf-8")
            # which uses the 'strict' error handling technique, which raises
            # on failure. Since we're not tracking content-type on the server
            # we could have anything at this point so, and we don't want to die
            # so we fudge the issue by ignoring things that are not utf-8
            return bytes.decode("utf-8", "ignore")
        except:
            log.exception("Error in Persister.load() for name=%s", name)
            return ""

    def save(self, name, contents, username=None):
        """Load a temporary file by extracting the project from the filename
        and calling project.save_temp_file"""
        try:
            (project, path) = self._split(name)
            log.debug("%s is saving to temp file for: %s/%s", username, project.name, path)
            project.save_temp_file(path, contents)
        except:
            log.exception("Error in Persister.save() for name=%s", name)

    def check_access(self, name, handle):
        """Check to see what level of access user has over an owner's project.
        Returns one of: Access.Denied, Access.ReadOnly or Access.ReadWrite
        Note that if user==owner then no check of project_name is performed, and
        Access.ReadWrite is returned straight away"""
        try:
            (user_name, project_name, path) = name.split("/", 2)

            requester = get_username_from_handle(handle)
            user = User.find_user(requester)
            owner = User.find_user(user_name)

            if user == owner:
                return Access.ReadWrite
            if user != owner:
                if owner.is_project_shared(project_name, user, require_write=True):
                    return Access.ReadWrite
                if owner.is_project_shared(project_name, user, require_write=False):
                    return Access.ReadOnly
                else:
                    return Access.Denied
        except:
            log.exception("Error in Persister.check_access() for name=%s, handle=%s", 
                            name, handle)
            return Access.Denied

    def _split(self, name):
        """Cut a name into the username, projectname, path parts and lookup
        a project under the given user"""
        (user_name, project_name, path) = name.split("/", 2)
        user = User.find_user(user_name)
        project = get_project(user, user, project_name)
        return (project, path)
