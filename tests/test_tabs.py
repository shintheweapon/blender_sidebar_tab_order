# Tests of tabs.py and prefs.py inside Blender, with fake sidebar panels.

import unittest
from unittest import mock

import bpy

from src import messages, order, prefs, tabs

PACKAGE = 'src'


def panel(idname, category, parent='', bl_order=None, label=None):
    """Make a sidebar panel class with the given tab, parent and order."""
    attributes = {
        'bl_idname': idname,
        'bl_space_type': 'VIEW_3D',
        'bl_region_type': 'UI',
        'bl_category': category,
        'bl_label': label or idname,
        'draw': lambda self, context: None,
    }
    if parent:
        attributes['bl_parent_id'] = parent
    if bl_order is not None:
        attributes['bl_order'] = bl_order
    return type(idname, (bpy.types.Panel,), attributes)


class FakePanels(unittest.TestCase):
    def setUp(self):
        self.classes = [
            panel('TEST_PT_a', 'Test A'),
            panel('TEST_PT_a_child', 'Test A', parent='TEST_PT_a'),
            panel('TEST_PT_b', 'Test B', bl_order=5),
            panel('TEST_PT_c', 'Test C'),
        ]
        for cls in self.classes:
            bpy.utils.register_class(cls)
        addons = bpy.context.preferences.addons
        if PACKAGE not in addons.keys():
            addons.new().module = PACKAGE
        self.addCleanup(lambda: addons.remove(addons[PACKAGE]) if PACKAGE in addons.keys() else None)

    def tearDown(self):
        for cls in reversed(self.classes):
            if cls.is_registered:
                bpy.utils.unregister_class(cls)


class ApplyOrderTest(FakePanels):
    def test_every_panel_is_registered_again(self):
        before = {tabs.idname(cls) for cls in tabs.sidebar_panels()}
        final, failed = tabs.apply_order(['Test C', 'Test B', 'Test A'])
        after = {tabs.idname(cls) for cls in tabs.sidebar_panels()}
        self.assertEqual(failed, [])
        self.assertEqual(before, after)

    def test_final_order_puts_item_first_then_the_wanted_tabs(self):
        final, _ = tabs.apply_order(['Test C', 'Test B', 'Test A'])
        self.assertEqual(final[0], 'Item')
        self.assertEqual(final[1:4], ['Test C', 'Test B', 'Test A'])

    def test_sub_panel_keeps_its_parent(self):
        tabs.apply_order(['Test C', 'Test A'])
        child = self.classes[1]
        self.assertTrue(child.is_registered)
        self.assertEqual(child.bl_rna.identifier, 'TEST_PT_a_child')
        self.assertEqual(child.bl_parent_id, 'TEST_PT_a')

    def test_own_bl_order_is_restored_on_the_class(self):
        tabs.apply_order(['Test B'])
        self.assertEqual(self.classes[2].bl_order, 5)
        self.assertNotIn('bl_order', self.classes[0].__dict__)

    def test_a_panel_that_fails_is_reported_and_the_rest_apply(self):
        register = bpy.utils.register_class

        def failing(cls):
            if cls is self.classes[2]:
                raise RuntimeError("refused")
            register(cls)

        with mock.patch.object(bpy.utils, 'register_class', failing):
            final, failed = tabs.apply_order(['Test C', 'Test B', 'Test A'])
        self.assertEqual(failed, ['TEST_PT_b: refused'])
        self.assertFalse(self.classes[2].is_registered)
        for index in (0, 1, 3):
            self.assertTrue(self.classes[index].is_registered)


class PreferencesTest(FakePanels):
    def test_refresh_lists_item_first_and_the_new_tabs(self):
        names = prefs.refresh(bpy.context)
        self.assertEqual(names[0], 'Item')
        for tab in ('Test A', 'Test B', 'Test C'):
            self.assertIn(tab, names)
        self.assertEqual(prefs.saved_order(bpy.context), names)

    def test_refresh_keeps_the_saved_order_and_drops_gone_tabs(self):
        items = prefs.preferences(bpy.context).tabs
        items.clear()
        for name in ('Test C', 'Gone', 'Test A'):
            items.add().name = name
        names = prefs.refresh(bpy.context)
        self.assertEqual(names[:3], ['Item', 'Test C', 'Test A'])
        self.assertNotIn('Gone', names)

    def test_move_keeps_pinned_tabs_first(self):
        prefs.refresh(bpy.context)
        p = prefs.preferences(bpy.context)
        p.active = 1
        self.assertEqual(bpy.ops.tab_order.move(direction='UP'), {'CANCELLED'})
        self.assertEqual(p.tabs[0].name, 'Item')
        second = p.tabs[2].name
        p.active = 2
        self.assertEqual(bpy.ops.tab_order.move(direction='UP'), {'FINISHED'})
        self.assertEqual(p.tabs[1].name, second)

    def test_apply_operator_reports_the_count(self):
        prefs.refresh(bpy.context)
        self.assertEqual(bpy.ops.tab_order.apply(), {'FINISHED'})


class MessagesTest(unittest.TestCase):
    def test_every_message_has_a_chinese_entry(self):
        from src import i18n_zh_hans
        table = i18n_zh_hans.table()
        for template in messages.templates().values():
            self.assertIn(('*', template), table)


if __name__ == '__main__':
    unittest.main()
