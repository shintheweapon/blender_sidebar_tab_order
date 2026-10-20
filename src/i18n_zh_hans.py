# Simplified Chinese (zh_HANS) translations of the add-on's texts; plain Python.
# Keys are (context, English text) as bpy.app.translations expects; the
# English texts must match the code exactly (tests check this). The words
# follow Blender's own zh_HANS translation: 侧栏, 标签, 条目, 应用, 刷新.

from typing import Dict, Tuple

from . import messages

# Contexts used by Blender: '*' for most texts, 'Operator' for operator labels
DEFAULT = '*'
OPERATOR = 'Operator'

# Operator labels, also looked up under the operator context
LABELS = {
    "Refresh List": "刷新列表",
    "Apply": "应用",
    "Move Tab": "移动标签",
}

_TEXTS = {
    **LABELS,
    "Add new sidebar tabs to the end of the list and remove tabs that no longer exist":
        "把新的侧栏标签加到列表末尾，并移除已不存在的标签",
    "Move the selected tab up or down the list": "在列表中上移或下移所选标签",
    "Put the sidebar tabs in the order of the list": "按列表的顺序排列侧栏标签",
    "Active Tab": "活动标签",
    "Up": "上",
    "Down": "下",
    messages.APPLIED: "已应用 {count} 个侧栏标签的顺序",
    messages.FAILED: "{count} 个面板无法重新注册：{names}",
    messages.LISTED: "列表中有 {count} 个标签",
    messages.PINNED: "条目始终在最前：它的主要面板内置于 Blender",
}


def table() -> Dict[Tuple[str, str], str]:
    """
    Build the translation table to register with Blender.

    Returns
    -------
    dict
        ``{(context, English): Chinese}``. Every text is under the default
        context; the operator labels are also under the operator context,
        where Blender looks them up for buttons.
    """
    entries = {(DEFAULT, english): chinese for english, chinese in _TEXTS.items()}
    for english, chinese in LABELS.items():
        entries[(OPERATOR, english)] = chinese
    return entries
