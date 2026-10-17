# Sidebar Tab Order: puts the 3D Viewport sidebar's tabs in an order chosen in
# the add-on's preferences

import bpy

from . import i18n_zh_hans, prefs

# Seconds after start-up before the saved order is applied, so add-ons
# enabled after this one have registered their panels
START_DELAY = 0.5


def _apply_saved() -> None:
    """Fill the list on first use, otherwise apply the saved order."""
    context = bpy.context
    if __package__ not in context.preferences.addons:
        return None
    if prefs.saved_order(context):
        prefs.apply(context)
    else:
        prefs.refresh(context)
    return None


def register():
    """Register the translations, the preferences and the start-up timer."""
    bpy.app.translations.register(__name__, {'zh_HANS': i18n_zh_hans.table()})
    for cls in prefs.CLASSES:
        bpy.utils.register_class(cls)
    bpy.app.timers.register(_apply_saved, first_interval=START_DELAY, persistent=True)


def unregister():
    """Unregister everything added by :func:`register`."""
    if bpy.app.timers.is_registered(_apply_saved):
        bpy.app.timers.unregister(_apply_saved)
    for cls in reversed(prefs.CLASSES):
        bpy.utils.unregister_class(cls)
    bpy.app.translations.unregister(__name__)
