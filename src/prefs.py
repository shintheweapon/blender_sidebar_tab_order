# The add-on's preferences: the saved tab order, its list, and the commands
# that refresh, move and apply it.

from typing import List

import bpy

from . import messages, order, tabs


class TAB_ORDER_tab(bpy.types.PropertyGroup):
    """One sidebar tab in the saved order; its ``name`` is the category."""


class TAB_ORDER_UL_tabs(bpy.types.UIList):
    """The saved tab order, one row per tab."""

    def draw_item(self, context, layout, data, item, icon, active_data, active_property, index):
        row = layout.row()
        row.label(text=item.name, icon='PINNED' if item.name in order.PINNED else 'NONE')


class TAB_ORDER_preferences(bpy.types.AddonPreferences):
    bl_idname = __package__

    tabs: bpy.props.CollectionProperty(type=TAB_ORDER_tab)
    active: bpy.props.IntProperty(name="Active Tab", default=0)

    def draw(self, context):
        layout = self.layout
        layout.label(text=messages.PINNED, icon='INFO')
        row = layout.row()
        row.template_list('TAB_ORDER_UL_tabs', '', self, 'tabs', self, 'active', rows=10)
        column = row.column(align=True)
        column.operator(TAB_ORDER_OT_move.bl_idname, text="", icon='TRIA_UP').direction = 'UP'
        column.operator(TAB_ORDER_OT_move.bl_idname, text="", icon='TRIA_DOWN').direction = 'DOWN'
        row = layout.row()
        row.operator(TAB_ORDER_OT_refresh.bl_idname, icon='FILE_REFRESH')
        row.operator(TAB_ORDER_OT_apply.bl_idname, icon='CHECKMARK')


def preferences(context: bpy.types.Context) -> TAB_ORDER_preferences:
    """
    Get this add-on's preferences.

    Parameters
    ----------
    context : bpy.types.Context
        The current context.

    Returns
    -------
    TAB_ORDER_preferences
        The preferences of this add-on.
    """
    return context.preferences.addons[__package__].preferences


def saved_order(context: bpy.types.Context) -> List[str]:
    """
    Read the saved tab order.

    Parameters
    ----------
    context : bpy.types.Context
        The current context.

    Returns
    -------
    list of str
        The tab names, first to last.
    """
    return [item.name for item in preferences(context).tabs]


def refresh(context: bpy.types.Context) -> List[str]:
    """
    Bring the saved order up to date with the tabs that exist now.

    Tabs that no longer exist are removed and new tabs are added at the end;
    the pinned tabs are kept first.

    Parameters
    ----------
    context : bpy.types.Context
        The current context.

    Returns
    -------
    list of str
        The saved order after the refresh.
    """
    prefs = preferences(context)
    names = order.final_tabs(saved_order(context), tabs.sidebar_tabs())
    prefs.tabs.clear()
    for name in names:
        prefs.tabs.add().name = name
    prefs.active = min(prefs.active, max(len(names) - 1, 0))
    context.preferences.is_dirty = True
    return names


def apply(context: bpy.types.Context):
    """
    Put the sidebar's tabs in the saved order.

    Parameters
    ----------
    context : bpy.types.Context
        The current context.

    Returns
    -------
    tuple of (list of str, list of str)
        What :func:`tabs.apply_order` returns.
    """
    result = tabs.apply_order(saved_order(context))
    for window in context.window_manager.windows:
        for area in window.screen.areas:
            if area.type == 'VIEW_3D':
                area.tag_redraw()
    return result


def _text(template: str, **fields) -> str:
    """
    Fill a message template from :mod:`messages`, in the interface language
    when Blender translates reports.

    Parameters
    ----------
    template : str
        One of the templates in :mod:`messages`.
    **fields
        Values for its named fields.

    Returns
    -------
    str
        The message.
    """
    return bpy.app.translations.pgettext_rpt(template).format(**fields)


class TAB_ORDER_OT_refresh(bpy.types.Operator):
    bl_idname = "tab_order.refresh"
    bl_label = "Refresh List"
    bl_description = "Add new sidebar tabs to the end of the list and remove tabs that no longer exist"
    bl_options = {'INTERNAL'}

    def execute(self, context):
        names = refresh(context)
        self.report({'INFO'}, _text(messages.LISTED, count=len(names)))
        return {'FINISHED'}


class TAB_ORDER_OT_move(bpy.types.Operator):
    bl_idname = "tab_order.move"
    bl_label = "Move Tab"
    bl_description = "Move the selected tab up or down the list"
    bl_options = {'INTERNAL'}

    direction: bpy.props.EnumProperty(items=(('UP', "Up", ""), ('DOWN', "Down", "")))

    def execute(self, context):
        prefs = preferences(context)
        index = prefs.active
        target = index - 1 if self.direction == 'UP' else index + 1
        pinned = len([item for item in prefs.tabs if item.name in order.PINNED])
        if not (pinned <= index < len(prefs.tabs) and pinned <= target < len(prefs.tabs)):
            return {'CANCELLED'}
        prefs.tabs.move(index, target)
        prefs.active = target
        context.preferences.is_dirty = True
        return {'FINISHED'}


class TAB_ORDER_OT_apply(bpy.types.Operator):
    bl_idname = "tab_order.apply"
    bl_label = "Apply"
    bl_description = "Put the sidebar tabs in the order of the list"
    bl_options = {'INTERNAL'}

    def execute(self, context):
        final, failed = apply(context)
        if failed:
            self.report({'WARNING'}, _text(
                messages.FAILED, count=len(failed), names="; ".join(failed)))
        else:
            self.report({'INFO'}, _text(messages.APPLIED, count=len(final)))
        return {'FINISHED'}


CLASSES = (
    TAB_ORDER_tab,
    TAB_ORDER_UL_tabs,
    TAB_ORDER_OT_refresh,
    TAB_ORDER_OT_move,
    TAB_ORDER_OT_apply,
    TAB_ORDER_preferences,
)
