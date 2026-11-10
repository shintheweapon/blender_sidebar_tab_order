# Every report text of the add-on, as templates with named fields; plain Python.
# The templates are also the keys of the translations.

APPLIED = "Applied the order of {count} sidebar tabs"
FAILED = "{count} panels could not be registered again: {names}"
LISTED = "The list has {count} tabs"
PINNED = "Item always comes first: its main panels are built into Blender"


def templates() -> dict:
    """
    List every message template of this module.

    Returns
    -------
    dict
        Constant name to template, for every upper-case string constant.
    """
    return {name: value for name, value in globals().items()
            if name.isupper() and isinstance(value, str)}
