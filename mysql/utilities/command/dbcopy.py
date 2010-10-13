#!/usr/bin/env python
#
# Copyright (c) 2010, Oracle and/or its affiliates. All rights reserved.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307 USA
#

"""
This file contains the copy database operation which ensures a database
is exactly the same among two servers.
""" 

import sys
import MySQLdb
from mysql.utilities.common import MySQLUtilError

def copy_db(src_val, dest_val, db_list, options):
    """ Copy a database
    
    This method will copy a database and all of its objects and data from
    one server (source) to another (destination). Options are available to
    selectively ignore each type of object. The force parameter is
    used to permit the copy to overwrite an existing destination database
    (default is to not overwrite).
    
    src_val[in]        a dictionary containing connection information for the
                       source including:
                       (user, password, host, port, socket)
    dest_val[in]       a dictionary containing connection information for the
                       destination including:
                       (user, password, host, port, socket)
    options[in]        a dictionary containing the options for the copy:
                       (skip_tables, skip_views, skip_triggers, skip_procs,
                       skip_funcs, skip_events, skip_grants, skip_create,
                       skip_data, copy_dir, verbose, force, silent,
                       connections, and debug)

    Notes:
        copy_dir - a directory to use for temporary files (default is None)
        force    - if True, the database on the destination will be dropped
                   if it exists (default is False)
        silent   - do not print any information during operation 
                   (default is False)
                       
    Returns bool True = success, False = error
    """
    
    from mysql.utilities.common import Database
    from mysql.utilities.common import connect_servers
    
    try:
        servers = connect_servers(src_val, dest_val,
                                  options.get("silent", False), "5.1.30")
        #print servers
    except MySQLUtilError, e:
        raise e

    source = servers[0]
    destination = servers[1]

    cloning = (src_val == dest_val) or dest_val is None
                            
    # Check user permissions on source and destination for all databases
    for db_name in db_list:
        try:
            source_db = Database(source, db_name[0])
            if destination is None:
                dest = source
            else:
                dest = destination
            if db_name[1] is None:
                db = db_name[0]
            else:
                db = db_name[1]
            dest_db = Database(dest, db)

            source_db.check_read_access(src_val["user"], src_val["host"],
                                        options.get("skip_views", False),
                                        options.get("skip_procs", False),
                                        options.get("skip_funcs", False),
                                        options.get("skip_grants", False))
            dest_db.check_write_access(dest_val["user"], dest_val["host"],
                                       options.get("skip_views", False),
                                       options.get("skip_procs", False),
                                       options.get("skip_funcs", False),
                                       options.get("skip_grants", False))
        except MySQLUtilError, e:
            raise e
            
    for db_name in db_list:

        # Error is source db and destination db are the same and we're cloning
        if destination is None and db_name[0] == db_name[1]:
            raise MySQLUtilError("Destination database name is same as "
                                 "source - source = %s, destinion = %s" %
                                 (db_name[0], db_name[1]))
    
        # Display copy message
        if not options.get("silent", False):
            msg = "# Copying database %s " % db_name[0]
            if db_name[1]:
                msg += "renamed as %s" % (db_name[1])
            print msg
        
        # Get a Database class instance
        db = Database(source, db_name[0], options)
        
        # Error is source database does not exist
        if not db.exists():
            raise MySQLUtilError("Source database does not exist - %s" %
                                 db_name[0])

        # Perform the copy
        db.init()
        try:
            db.copy(db_name[1], None, options, destination,
                    options.get("connections", False))
        except MySQLUtilError, e:
            raise e
            
    if not options.get("silent", False):
        print "#...done."
    return True