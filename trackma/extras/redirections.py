# This file is part of Trackma.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

SUPPORTED_APIS = ['mal', 'kitsu', 'anilist']
SUPPORTED_MEDIATYPES = ['anime']


def supports(api, mediatype):
    return api in SUPPORTED_APIS and mediatype in SUPPORTED_MEDIATYPES


def parse_anime_relations(filename, api, last=None):
    """
    Support for Taiga-style anime relations file.
    Thanks to erengy and all the contributors.
    Database under the public domain.

    https://github.com/erengy/anime-relations
    """
    (src_grp, dst_grp) = (SUPPORTED_APIS.index(api) + 1, SUPPORTED_APIS.index(api) + 6)

    def log(*args, **kwargs):
        print("[redirections.py]", *args, **kwargs)

    def get_eps(m, i):
        return (int(m.group(i)),
                int((m.group(i + 1) or m.group(i)).replace("?", "-1")))

    with open(filename) as f:
        import re

        relations = {'meta': {}}

        id_pattern = r"(\d+|[\?~])\|(\d+|[\?~])\|(\d+|[\?~])"
        ep_pattern = r"(\d+)-?(\d+|\?)?"
        full = r'- {0}:{1} -> {0}:{1}(!)?'.format(id_pattern, ep_pattern)
        _re = re.compile(full)
        del id_pattern, ep_pattern, full

        rules_mode = False

        for line in f:
            line = line.strip()

            if not line:
                continue
            if line[0] == '#':
                continue

            if not rules_mode:

                if line == "::rules":
                    rules_mode = True
                    continue

                if line.startswith("::"):
                    continue

                m = re.match("- *(\S+): *(\S+)", line)

                if not m:
                    log("Not recognized: " + line)
                    continue

                prop, value = m.groups()
                relations['meta'][prop] = value

                if prop == "version" and not value.startswith("1.3"):
                    # If the version is different, maybe we can't handle it
                    log("anime-relations.txt version is not 1.3.x",
                          " - some errors can happen")

                elif prop == "last_modified" and isinstance(last, str):
                    # "YYYY-MM-DD" can be compared directly
                    if value <= last:
                        return None
                continue

            # Rules Mode

            m = _re.match(line)

            if not m:
                log("Not recognized: " + line)
                continue

            # Source
            src_id = int(m.group(src_grp).replace("?", "-1"))
            if src_id == -1: continue
            src_eps = get_eps(m, 4)

            # Destination
            dst_id = int(m.group(dst_grp).replace("~", str(src_id)))
            dst_eps = get_eps(m, 9)

            # Save relation
            relations.setdefault(src_id, []) # type: ignore
            relations[src_id].append((src_eps, dst_id, dst_eps)) # type: ignore

            # Handle self-redirecting rules
            if m.group(11) == '!':
                relations.setdefault(dst_id, [])
                relations[dst_id].append((src_eps, dst_id, dst_eps))

        return relations
