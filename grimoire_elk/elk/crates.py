#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
#
# Copyright (C) 2015 Bitergia
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
#
# Authors:
#   Alvaro del Castillo San Felix <acs@bitergia.com>
#

import json
import logging

from dateutil import parser

from .enrich import Enrich, metadata


logger = logging.getLogger(__name__)


class CratesEnrich(Enrich):

    def get_field_author(self):
        return 'owner_user_data'

    def get_elastic_mappings(self):

        mapping = """
        {
            "properties": {
                "description_analyzed": {
                  "type": "string",
                  "index":"analyzed"
                  }
           }
        } """

        return {"items":mapping}

    def get_identities(self, item):
        """ Return the identities from an item """
        identities = []

        field = self.get_field_author()
        identities.append(self.get_sh_identity(item, field))

        return identities

    def get_project_repository(self, eitem):
        return str(eitem['space'])

    # def get_users_data(self, item):
    #     """ If user fields are inside the global item dict """
    #     if 'data' in item:
    #         users_data = item['data']['version']
    #     else:
    #         # the item is directly the data (kitsune answer)
    #         users_data = item
    #     return users_data

    def get_sh_identity(self, item, identity_field=None):
        identity = {}

        user = item  # by default a specific user dict is expected
        if 'data' in item and isinstance(item, dict):
            users = item['data'][identity_field]['users']
            if not users:
                return identity
            else:
                user = users[0]

        identity['username'] = None
        identity['email'] = None
        identity['name'] = None
        if 'login' in user:
            identity['username'] = user['login']
        if 'name' in user:
            identity['name'] = user['name']

        return identity

    @metadata
    def get_rich_item(self, item):
        eitem = {}

        for f in self.RAW_FIELDS_COPY:
            if f in item:
                eitem[f] = item[f]
            else:
                eitem[f] = None
        # The real data
        page = item['data']

        # data fields to copy
        copy_fields = ["id", "homepage", "name", "repository", "downloads",
                       "description", "recent_downloads", "max_version",
                       "keywords", "categories", "badges", "versions",
                       "updated_at"]

        for f in copy_fields:
            if f in page:
                eitem[f] = page[f]
            else:
                eitem[f] = None
        # Fields which names are translated
        map_fields = {"description": "description_analyzed"}
        for fn in map_fields:
            eitem[map_fields[fn]] = page[fn]

        if self.sortinghat:
            eitem.update(self.get_item_sh(item))

        if self.prjs_map:
            eitem.update(self.get_item_project(eitem))

        eitem.update(self.get_grimoire_fields(eitem['updated_at'], "crates"))

        return eitem
