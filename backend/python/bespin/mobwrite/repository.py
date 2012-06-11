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

"""
A mini VCS that stores a history of the changes to a file.
For more information, see:
* https://wiki.mozilla.org/Labs/Bespin/DesignDocs/TimeMachine

The features of this repository are:
* lightweight: ie easy to code in the first instance
* upgradable: so the disk format can evolve to be more efficient
* potentially performant: file reads could be O(n) on history length

It is not however:
* distributed
* non-linear. There is no DAG

The on disk format is a series of lines as follows

 hex(time):owner:method:urlencode(comment):data

For example

 4aa51a00:joewalker:int:example command:data
 4aa61e8f:joewalker:int:another example:more data

Where:
* hex(time): an 8 character string (for the next few years) following the
    python way of using seconds since the epoch e.g. 4aa61e8f
* owner: is the bespin username of the change creator
* method: is one of [int|ext|delta|zint|zext]
  Currently the only supported value is 'int' however the following are planned
** int: The contents is stored in the data field (at the end of the line)
** ext: The contents are written to a file whose name is in the data field
** delta: The contents are the value of the previous record with the change
      in the delta field applied
** zint|zext: As int|ext except the contents are compresses with zlib
* comment: A comment (where possible) for the change
* data: As interpreted by the 'method' field
"""

# TODO: We should extract a revision class that holds the data returned by
# _parse_history_line i.e: the data on what the file was like at one point in
# time.

# TODO: Implement methods other than 'int'

import time
import urllib
from bespin.utils import BadValue
import logging

log = logging.getLogger("repository")

class Repository(object):
    """ A class to contain access to an edit history of a file, stored on
    the local filesystem rather than a VCS """

    def __init__(self, path):
        self.path = path
        self.log_file = path + ".log"

    def get_history(self):
        """ Retrieve a list of records that describe the files history. The
        on-disk format is described at the top of this file. The output history
        format is described in
        https://wiki.mozilla.org/Labs/Bespin/DesignDocs/TimeMachine """
        revisions = []
        file = open(self.log_file)
        line_num = 0
        try:
            for line in file:
                revision = self._parse_history_line(line, line_num)
                # For output we don't want the data member - it's too big
                del revision['contents']
                revisions.append(revision)
                line_num += 1
        finally:
            file.close()
        return revisions

    def get_contents(self, revision_id=None):
        """ Retrieve file data, at a given revision_id, or the most current if
        revision_id=None. """
        if revision is None:
            file = open(self.path, "r")
            try:
                return file.read()
            finally:
                file.close()
        else:
            file = open(self.log_file)
            line_num = 0
            try:
                for line in file:
                    revision = self._parse_history_line(line, line_num)
                    if revision.id == revision_id:
                        return revision.contents
            finally:
                file.close()
            raise BadValue("Unknown revision")

    def add_revision(self, contents, owner, description=''):
        """ Add a revision to the list of revisions that we already have for a
        file """
        encoded = self._encode(self.path, contents)
        line = ":".join([
            hex(int(time.time()))[2:],
            owner,
            encoded.method,
            urllib.quote(description, " "),
            encoded.data
        ])
        file = open(self.log_file, "a")
        # It would be good if we could make this more atomic
        try:
            encoded.write()
            file.write(line)
            file.write("\n")
        finally:
            file.close()

    def _parse_history_line(self, line, line_num):
        """ Take a line in the format specified in the file header and turn it
        into a record as specified by the time-machine external interface
        (without doing the json conversion step). See also:
        https://wiki.mozilla.org/Labs/Bespin/DesignDocs/TimeMachine """
        [time, owner, method, description, data] = line.split(":")
        return {
            'source': 'undo',
            'date': int(time, 16),
            'id': 'undo:' + str(line_num),
            'owner': owner,
            'description': urllib.unquote(description),
            'contents': self._decode(method, data)
        }

    def _encode(self, path, contents):
        """ Decide what encoding method to use for some file contents and return
        data to be stored in the data field """
        return InternalEncoding(contents)

    def _decode(self, method, contents):
        """ Dispatch the decode to the relevant class """
        if method == "int":
            return InternalEncoding.decode(contents)
        else:
            raise BadValue("Illegal encoding")


class InternalEncoding(object):
    """ The simplest encoding that just stores the whole data in the data field.
    See the file header for more """
    method = "int"

    def __init__(self, contents):
        """ We just url-encode to get rid of : and control chars. We leave space
        unencoded for readability """
        self.data = urllib.quote(contents, " ")

    @classmethod
    def decode(cls, contents):
        """ decoding is simpler than encoding because it doesn't ever need a
        separate write step, so it's done with a static """
        return "xx"

    def write(self):
        """ Internal data has no external writing needs so the write function is
        a no-op """
        pass


if __name__ == "__main__":
    """ Some simple tests """
    repository = Repository("/Users/joe/Projects/mozilla/bespin/workspace/devfiles/joewalker/.SampleProject-mobwrite/readme.txt")
    repository.add_revision("comments:the real file data", owner="joewalker", description="stuff goes here")
    revisions = repository.get_history()

    import simplejson
    print simplejson.dumps(revisions)
