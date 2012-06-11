"""omnisync configuration module."""

import logging
import re

log = logging.getLogger("omnisync")

class Configuration:
    """Hold various configuration options."""

    def __init__(self, options):
        """Retrieve the configuration from the parser options."""
        if options.verbosity == 0:
            log.setLevel(logging.ERROR)
        elif options.verbosity == 1:
            log.setLevel(logging.INFO)
        elif options.verbosity == 2:
            log.setLevel(logging.DEBUG)
            log.debug("Debug logging on")
        self.delete = options.delete
        if options.attributes:
            self.requested_attributes = set(options.attributes)
        else:
            self.requested_attributes = set()
        self.dry_run = options.dry_run
        self.update = options.update
        if self.update:
            self.requested_attributes.add("mtime")
        self.recursive = options.recursive
        if options.exclude_files:
            self.exclude_files = re.compile(options.exclude_files)
        else:
            # An unmatchable regex, to save us from checking if this is set. Hopefully it's
            # not too slow.
            self.exclude_files = re.compile("^$")
        if options.include_files:
            self.include_files = re.compile(options.include_files)
            if not self.exclude_files:
                self.exclude_files = re.compile("")
        else:
            self.include_files = re.compile("^$")
        if options.exclude_dirs:
            self.exclude_dirs = re.compile(options.exclude_dirs)
        else:
            self.exclude_dirs = re.compile("^$")
        if options.include_dirs:
            self.include_dirs = re.compile(options.include_dirs)
            if not self.exclude_dirs:
                self.exclude_dirs = re.compile("")
        else:
            self.include_dirs = re.compile("^$")
        
        # access to remaining options and any options
        # that were set by plugins.
        self.full_options = options
        
        self.exclude_attributes = set()
        