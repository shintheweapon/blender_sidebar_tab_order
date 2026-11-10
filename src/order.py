# How Blender orders sidebar tabs, and the plan that puts them in a wanted
# order; plain Python, no bpy, so it can be tested anywhere.
#
# Blender 4.5 keeps one list of panel types per region. rna_Panel_register
# (makesrna/intern/rna_ui.cc) inserts a new panel type by walking back from
# the end of that list: a panel with no header skips every panel with a
# header, and the walk stops at the first panel whose order is the same or
# lower; the new panel goes right after it (at the start when none stops it).
# region_panels_collect_categories (editors/screen/area.cc) then adds a tab
# for each category in the order its first top-level panel appears.

from typing import Dict, Iterable, List, NamedTuple, Optional, Sequence, Set

# Room per tab in the temporary orders: a panel's own order stays below it
STEP = 1000

# Tabs that always come first. The Item tab's Transform and Vertex Weights
# panels are made in C (view3d_buttons_register in
# editors/space_view3d/view3d_buttons.cc) at start-up, before any Python
# panel, and Python cannot register them again; bl_order cannot go below 0
# to get ahead of them.
PINNED = ('Item',)


class PanelInfo(NamedTuple):
    """
    What Blender's ordering reads from one panel type.

    Attributes
    ----------
    idname : str
        The panel's ``bl_idname``.
    category : str
        Its ``bl_category``, the tab it shows in.
    order : int
        Its ``bl_order``.
    no_header : bool
        True when ``bl_options`` has ``HIDE_HEADER``.
    parent_id : str
        Its ``bl_parent_id``; empty for a top-level panel.
    """
    idname: str
    category: str
    order: int = 0
    no_header: bool = False
    parent_id: str = ''


def insert(panels: Sequence[PanelInfo], new: PanelInfo) -> List[PanelInfo]:
    """
    Insert a panel type as Blender's ``rna_Panel_register`` does.

    Parameters
    ----------
    panels : sequence of PanelInfo
        The region's panel types, in list order.
    new : PanelInfo
        The panel type being registered.

    Returns
    -------
    list of PanelInfo
        A new list with ``new`` in the place Blender would put it.
    """
    index = len(panels) - 1
    while index >= 0:
        current = panels[index]
        if new.no_header and not current.no_header:
            index -= 1
            continue
        if current.order <= new.order:
            break
        index -= 1
    return list(panels[:index + 1]) + [new] + list(panels[index + 1:])


def tab_order(panels: Iterable[PanelInfo], shown: Optional[Set[str]] = None) -> List[str]:
    """
    List the tabs in the order Blender draws them.

    Parameters
    ----------
    panels : iterable of PanelInfo
        The region's panel types, in list order.
    shown : set of str, optional
        The idnames of the panels whose poll passes now; all when not given.
        A tab is placed by its first top-level panel that is shown.

    Returns
    -------
    list of str
        The categories, each once, in drawing order.
    """
    tabs: List[str] = []
    for panel in panels:
        if panel.parent_id or not panel.category:
            continue
        if shown is not None and panel.idname not in shown:
            continue
        if panel.category not in tabs:
            tabs.append(panel.category)
    return tabs


def final_tabs(wanted: Iterable[str], current: Iterable[str]) -> List[str]:
    """
    Combine the wanted order with the tabs that exist now.

    Parameters
    ----------
    wanted : iterable of str
        The saved order; tabs that no longer exist are left out.
    current : iterable of str
        The tabs that exist now, in their current order.

    Returns
    -------
    list of str
        The pinned tabs that exist (:data:`PINNED`), then the wanted tabs
        that exist, then the other current tabs in their current order.
    """
    current = list(current)
    tabs = [tab for tab in PINNED if tab in current]
    tabs += [tab for tab in dict.fromkeys(wanted) if tab in current and tab not in tabs]
    return tabs + [tab for tab in current if tab not in tabs]


def planned_order(rank: int, own: int) -> int:
    """
    Give a panel the temporary order that places its tab at ``rank``.

    Parameters
    ----------
    rank : int
        The tab's place in the final order, from 0.
    own : int
        The panel's own ``bl_order``; it keeps panels in their order inside
        the tab.

    Returns
    -------
    int
        ``rank * STEP + own``, with ``own`` held between 0 and ``STEP - 1``.
    """
    return rank * STEP + min(max(own, 0), STEP - 1)


def registration_sequence(panels: Sequence[PanelInfo], tabs: Sequence[str]) -> List[PanelInfo]:
    """
    List the panels to register again, in the order to register them.

    Parameters
    ----------
    panels : sequence of PanelInfo
        The region's panel types, in list order.
    tabs : sequence of str
        The tabs in their final order.

    Returns
    -------
    list of PanelInfo
        Tab by tab: the tab's top-level panels in list order, then their
        sub-panels, each after its parent. Unregister in the reverse order,
        so sub-panels go before their parents.
    """
    children: Dict[str, List[PanelInfo]] = {}
    for panel in panels:
        if panel.parent_id:
            children.setdefault(panel.parent_id, []).append(panel)
    sequence: List[PanelInfo] = []
    for tab in tabs:
        queue = [p for p in panels if not p.parent_id and p.category == tab]
        while queue:
            panel = queue.pop(0)
            sequence.append(panel)
            queue.extend(children.get(panel.idname, []))
    return sequence


def simulate(panels: Sequence[PanelInfo], sequence: Sequence[PanelInfo],
             tabs: Sequence[str]) -> List[PanelInfo]:
    """
    Predict the region's panel list after the panels are registered again.

    Parameters
    ----------
    panels : sequence of PanelInfo
        The region's panel types now.
    sequence : sequence of PanelInfo
        The panels to unregister and register again, in registration order.
    tabs : sequence of str
        The tabs in their final order, which gives each tab's rank.

    Returns
    -------
    list of PanelInfo
        The list after re-registration, each moved panel with its planned
        order for top-level panels.
    """
    moved = {p.idname for p in sequence}
    result = [p for p in panels if p.idname not in moved]
    rank = {tab: index for index, tab in enumerate(tabs)}
    for panel in sequence:
        if not panel.parent_id:
            panel = panel._replace(order=planned_order(rank[panel.category], panel.order))
        result = insert(result, panel)
    return result
