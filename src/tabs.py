# Reads the 3D Viewport sidebar's panels from Blender and registers them again
# so their tabs follow a wanted order (the plan comes from order.py).

from typing import Dict, Iterator, List, Sequence, Tuple, Type

import bpy

from . import order

SPACE = 'VIEW_3D'
REGION = 'UI'


def _subclasses(cls: type) -> Iterator[type]:
    for sub in cls.__subclasses__():
        yield sub
        yield from _subclasses(sub)


def idname(cls: Type[bpy.types.Panel]) -> str:
    """
    Give a registered panel class's id.

    Parameters
    ----------
    cls : type
        A registered panel class.

    Returns
    -------
    str
        The id Blender registered it under: ``bl_idname``, or the class name
        for a class without one.
    """
    return cls.bl_rna.identifier


def sidebar_panels() -> List[Type[bpy.types.Panel]]:
    """
    List the registered panel classes of the 3D Viewport sidebar.

    Returns
    -------
    list of type
        Every registered ``bpy.types.Panel`` subclass whose space is the 3D
        Viewport and whose region is the sidebar, each once, sorted by
        id (Blender's own list order is not readable from Python).
    """
    found: Dict[str, Type[bpy.types.Panel]] = {}
    for cls in _subclasses(bpy.types.Panel):
        if (getattr(cls, 'bl_space_type', '') == SPACE
                and getattr(cls, 'bl_region_type', '') == REGION
                and getattr(cls, 'is_registered', False)):
            found[idname(cls)] = cls
    return [found[name] for name in sorted(found)]


def info(cls: Type[bpy.types.Panel]) -> order.PanelInfo:
    """
    Read what Blender's ordering uses from a panel class.

    Parameters
    ----------
    cls : type
        A registered panel class.

    Returns
    -------
    order.PanelInfo
        Its idname, tab, order, header flag and parent.
    """
    return order.PanelInfo(
        idname=idname(cls),
        category=getattr(cls, 'bl_category', '') or '',
        order=int(getattr(cls, 'bl_order', 0) or 0),
        no_header='HIDE_HEADER' in getattr(cls, 'bl_options', set()),
        parent_id=getattr(cls, 'bl_parent_id', '') or '',
    )


def sidebar_tabs() -> List[str]:
    """
    List the sidebar's tabs.

    Returns
    -------
    list of str
        Each category with a top-level panel, once, in the order its first
        panel was found (see :func:`sidebar_panels`), which may differ from
        the drawn order.
    """
    return order.tab_order(info(cls) for cls in sidebar_panels())


def apply_order(wanted: Sequence[str]) -> Tuple[List[str], List[str]]:
    """
    Register the sidebar's panels again so their tabs follow ``wanted``.

    Every sidebar panel is unregistered, sub-panels before their parents,
    then registered again tab by tab in the final order, parents before
    sub-panels. Each top-level panel gets a temporary ``bl_order`` that
    places its tab (:func:`order.planned_order`); its own order is restored
    on the class afterwards, so Blender keeps the panel where it now is.

    Parameters
    ----------
    wanted : sequence of str
        The tabs in the wanted order. Tabs that do not exist are ignored;
        existing tabs not listed follow in their current order.

    Returns
    -------
    tuple of (list of str, list of str)
        The final tab order, and the ``bl_idname`` of each panel that failed
        to register again, with the error.
    """
    classes = {idname(cls): cls for cls in sidebar_panels()}
    panels = [info(cls) for cls in classes.values()]
    tabs = order.final_tabs(wanted, order.tab_order(panels))
    rank = {tab: index for index, tab in enumerate(tabs)}
    sequence = order.registration_sequence(panels, tabs)

    for panel in reversed(sequence):
        bpy.utils.unregister_class(classes[panel.idname])

    failed: List[str] = []
    for panel in sequence:
        cls = classes[panel.idname]
        own = cls.__dict__.get('bl_order')
        if not panel.parent_id:
            cls.bl_order = order.planned_order(rank[panel.category], panel.order)
        try:
            bpy.utils.register_class(cls)
        except Exception as error:  # noqa: BLE001 - report and carry on
            failed.append(f"{panel.idname}: {error}")
        finally:
            if not panel.parent_id:
                if own is not None:
                    cls.bl_order = own
                elif 'bl_order' in cls.__dict__:
                    del cls.bl_order
    return tabs, failed
