#!/usr/bin/env python3
"""
Branch Out and Back

Folds a branch into its trunk so the two stitch out as one continuous line:
up the trunk to the junction, out along the branch to its tip, back along
the exact same line to the junction, then on along the rest of the trunk.

In the Node tool (N), select exactly two nodes, then run this:
  - the end node of the branch (the end that attaches to the trunk), and
  - the node on the trunk where it attaches.

The branch is whichever of the two is an end node of an open path. The two
nodes are joined directly, with no connecting segment. If they are not in
exactly the same place, both move to the point halfway between them (their
handles move with them). The branch may be drawn in either direction. The
result keeps the trunk's object, id and style; the branch object is removed.

No dialog, so it can be bound to a keyboard shortcut in Preferences >
Interface > Keyboard Shortcuts.
"""
import inkex
from inkex import EffectExtension, PathElement
from inkex.paths import Arc, Curve, Move, Path, ZoneClose

NODETYPES = "sodipodi:nodetypes"

HOW_TO = (
    "Switch to the Node tool (N) and select exactly two nodes: the end node "
    "of the branch, and the node on the trunk where it attaches. Then run "
    "this again."
)
ARC_TROUBLE = (
    "{}: this path has an arc segment at or before the selected node, and "
    "Inkscape numbers the nodes of arc segments differently from how they "
    "are stored, so the selection cannot be trusted. Move any node of the "
    "path a little and back (Inkscape then rewrites the arc as Beziers), "
    "then run this again."
)


def same_point(a, b, tol=1e-6):
    return abs(a[0] - b[0]) < tol and abs(a[1] - b[1]) < tol


def end_point(cmd):
    return (cmd.args[-2], cmd.args[-1])


def format_cmd(cmd):
    return " ".join([cmd.letter] + [f"{v:.10g}" for v in cmd.args])


def shifted(cmd, delta, first=False, last=False):
    """A copy of cmd with its first handle and/or its end point (and the
    handle belonging to that end point) moved by delta."""
    args = list(cmd.args)
    if first and isinstance(cmd, Curve):
        args[0] += delta[0]
        args[1] += delta[1]
    if last:
        args[-2] += delta[0]
        args[-1] += delta[1]
        if isinstance(cmd, Curve):
            args[2] += delta[0]
            args[3] += delta[1]
    return type(cmd)(*args)


def plain(path):
    """Commands of a path as absolute, non-shorthand, without the close."""
    cmds = path.to_absolute().to_non_shorthand()
    return [c for c in cmds if not isinstance(c, ZoneClose)]


class Subpath:
    """One subpath as a list of absolute commands. cmds[0] is the Move, and
    node i is the end point of cmds[i]."""

    def __init__(self):
        self.cmds = []
        self.closed = False

    def point(self, i):
        return end_point(self.cmds[i])

    @property
    def returns_to_start(self):
        return len(self.cmds) > 1 and same_point(self.point(-1), self.point(0))

    @property
    def nodetype_count(self):
        if self.closed and not self.returns_to_start:
            return len(self.cmds) + 1
        return len(self.cmds)

    def is_end(self, i):
        return not self.closed and i in (0, len(self.cmds) - 1)


class PathData:
    """An element's path split into subpaths, with its node types when the
    stored string matches the path."""

    def __init__(self, elem):
        self.elem = elem
        self.subs = []
        for cmd in elem.path.to_absolute().to_non_shorthand():
            if isinstance(cmd, Move):
                self.subs.append(Subpath())
                self.subs[-1].cmds.append(cmd)
            elif isinstance(cmd, ZoneClose):
                if self.subs:
                    self.subs[-1].closed = True
            elif self.subs:
                self.subs[-1].cmds.append(cmd)
        types = elem.get(NODETYPES)
        self.types = None
        if types is not None and len(types) == sum(s.nodetype_count for s in self.subs):
            self.types = []
            at = 0
            for s in self.subs:
                self.types.append(types[at : at + s.nodetype_count])
                at += s.nodetype_count

    def write(self):
        if not self.subs:
            self.elem.delete()
            return
        out = []
        for s in self.subs:
            out.extend(s.cmds)
            if s.closed:
                out.append(ZoneClose())
        self.elem.set("d", " ".join(format_cmd(c) for c in out))
        if self.types is not None:
            self.elem.set(NODETYPES, "".join(self.types))
        else:
            self.elem.set(NODETYPES, None)


class BranchOutAndBack(EffectExtension):
    def effect(self):
        picks = []
        for sel in self.options.selected_nodes:
            try:
                elem_id, sp, node = sel.rsplit(":", 2)
                picks.append((elem_id, int(sp), int(node)))
            except ValueError:
                continue
        if len(picks) != 2:
            raise inkex.AbortExtension(HOW_TO)
        if picks[0][:2] == picks[1][:2]:
            raise inkex.AbortExtension(
                "Both selected nodes are on the same path. " + HOW_TO
            )

        data = {}
        chosen = []
        for elem_id, sp, node in picks:
            if elem_id not in data:
                elem = self.svg.getElementById(elem_id)
                if not isinstance(elem, PathElement):
                    raise inkex.AbortExtension(HOW_TO)
                if elem.get("inkscape:original-d") is not None:
                    raise inkex.AbortExtension(
                        f"{elem_id}: has a path effect, which this does not handle."
                    )
                data[elem_id] = PathData(elem)
            pd = data[elem_id]
            if sp >= len(pd.subs):
                raise inkex.AbortExtension(HOW_TO)
            sub = pd.subs[sp]
            # Inkscape shows an arc segment as several Bezier pieces, so a node
            # number past an arc cannot be matched to a stored node. Node 0 can.
            if node != 0 and any(isinstance(c, Arc) for c in sub.cmds[: node + 1]):
                raise inkex.AbortExtension(ARC_TROUBLE.format(elem_id))
            if node >= len(sub.cmds):
                raise inkex.AbortExtension(HOW_TO)
            chosen.append((pd, sp, node))

        ends = [pd.subs[sp].is_end(node) for pd, sp, node in chosen]
        if ends[0] == ends[1]:
            if ends[0]:
                raise inkex.AbortExtension(
                    "Both selected nodes are end nodes, so there is no telling "
                    "which path is the branch. The trunk's node has to be one "
                    "with trunk on both sides of it."
                )
            raise inkex.AbortExtension(
                "Neither selected node is the end node of an open path, so "
                "there is no branch end to attach. " + HOW_TO
            )
        branch, trunk = (chosen[0], chosen[1]) if ends[0] else (chosen[1], chosen[0])
        self.join(trunk, branch)
        for pd in data.values():
            pd.write()

    def join(self, trunk, branch):
        t_pd, t_sp, k = trunk
        b_pd, b_sp, b_node = branch
        t_sub = t_pd.subs[t_sp]
        b_sub = b_pd.subs[b_sp]

        # The branch, in the trunk's own coordinates, starting at the junction.
        out = Path(b_sub.cmds)
        b_types = b_pd.types[b_sp] if b_pd.types is not None else None
        if b_node != 0:
            out = out.reverse()
            if b_types is not None:
                b_types = b_types[::-1]
        if b_pd.elem is not t_pd.elem:
            out = out.transform(
                -t_pd.elem.composed_transform() @ b_pd.elem.composed_transform()
            )
        out = plain(out)

        # Both selected nodes go to the point halfway between them.
        p_t = t_sub.point(k)
        p_b = end_point(out[0])
        junction = ((p_t[0] + p_b[0]) / 2.0, (p_t[1] + p_b[1]) / 2.0)
        d_t = (junction[0] - p_t[0], junction[1] - p_t[1])
        d_b = (junction[0] - p_b[0], junction[1] - p_b[1])

        out[0] = Move(*junction)
        if len(out) > 1:
            out[1] = shifted(out[1], d_b, first=True)
        back = plain(Path(out).reverse())

        cmds = t_sub.cmds
        closes_on_node = k == 0 and t_sub.closed and t_sub.returns_to_start
        cmds[k] = shifted(cmds[k], d_t, last=True)
        if k + 1 < len(cmds):
            cmds[k + 1] = shifted(cmds[k + 1], d_t, first=True)
        if closes_on_node:
            cmds[-1] = shifted(cmds[-1], d_t, last=True)
        t_sub.cmds = cmds[: k + 1] + out[1:] + back[1:] + cmds[k + 1 :]

        # Node types: the junction (both visits) and the tip become corners.
        if t_pd.types is not None and b_types is not None and not t_sub.closed:
            inner = b_types[1:-1]
            t_types = t_pd.types[t_sp]
            t_pd.types[t_sp] = (
                t_types[:k] + "c" + inner + "c" + inner[::-1] + "c" + t_types[k + 1 :]
            )
        else:
            t_pd.types = None

        # Take the branch out of its own object.
        if b_pd.elem is t_pd.elem:
            keep = [i for i in range(len(b_pd.subs)) if i != b_sp]
            b_pd.subs = [b_pd.subs[i] for i in keep]
            if b_pd.types is not None:
                b_pd.types = [b_pd.types[i] for i in keep]
        else:
            del b_pd.subs[b_sp]
            if b_pd.types is not None:
                del b_pd.types[b_sp]


if __name__ == "__main__":
    BranchOutAndBack().run()
