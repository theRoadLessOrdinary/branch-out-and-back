# Branch Out and Back

An Inkscape extension for embroidery paths. It folds a branch into its trunk so the two stitch out as one continuous line: up the trunk to the junction, out along the branch to its tip, back along the same line to the junction, then on along the rest of the trunk.

Menu: **Extensions > Map's Edge Tools > Embroidery > Stitch Paths > Branch Out and Back** (extension ID `maps_edge.branch_out_and_back`). It is also a button on the [Map's Edge Tool Panel](https://github.com/theRoadLessOrdinary/maps-edge-panel).

## Using it

1. Switch to the Node tool (N).
2. Select exactly two nodes:
   - the end node of the branch, at the end that attaches to the trunk, and
   - the node on the trunk where the branch attaches.
3. Run **Branch Out and Back**.

- The branch is whichever of the two nodes is an end node of an open path. It may be drawn in either direction.
- The two nodes are joined directly, with no connecting segment. If they are not in exactly the same place, both move to the point halfway between them, and their handles move with them.
- The result keeps the trunk's object, id and style. The branch object is removed.

It has no dialog, so it runs the moment it is picked and can be bound to a key in **Edit > Preferences > Interface > Keyboard Shortcuts** (search for its name).

## Requirements

- Inkscape 1.x (developed and used on Inkscape 1.4.4, Flatpak, on Linux; other platforms have not been tried)

## Install

Copy the files in this repository into a folder of their own inside Inkscape's user extensions directory, then restart Inkscape. To find that directory, open **Edit > Preferences > System** and look at **User extensions**. Typical locations:

| Install type | User extensions folder |
|---|---|
| Linux (native) | `~/.config/inkscape/extensions/` |
| Linux (Flatpak) | `~/.var/app/org.inkscape.Inkscape/config/inkscape/extensions/` |
| macOS | `~/Library/Application Support/org.inkscape.Inkscape/config/inkscape/extensions/` |
| Windows | `%APPDATA%\inkscape\extensions\` |

For example, on native Linux:

```bash
git clone https://github.com/theRoadLessOrdinary/branch-out-and-back.git \
    ~/.config/inkscape/extensions/branch-out-and-back
```

To uninstall, delete the folder and restart Inkscape.
