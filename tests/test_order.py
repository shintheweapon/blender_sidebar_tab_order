# Tests of order.py: Blender's insertion rule and the planned tab order.

import unittest

from src import order
from src.order import PanelInfo


def build(panels):
    """Register panels one by one, as Blender would, from an empty list."""
    result = []
    for panel in panels:
        result = order.insert(result, panel)
    return result


class InsertTest(unittest.TestCase):
    def test_same_order_goes_to_the_end(self):
        result = build([PanelInfo('A', 'a'), PanelInfo('B', 'b'), PanelInfo('C', 'c')])
        self.assertEqual([p.idname for p in result], ['A', 'B', 'C'])

    def test_lower_order_goes_before_higher(self):
        result = build([PanelInfo('A', 'a', order=5), PanelInfo('B', 'b', order=0)])
        self.assertEqual([p.idname for p in result], ['B', 'A'])

    def test_no_header_panel_skips_panels_with_a_header(self):
        result = build([PanelInfo('A', 'a'), PanelInfo('B', 'b', no_header=True)])
        self.assertEqual([p.idname for p in result], ['B', 'A'])

    def test_no_header_panel_stops_at_an_earlier_no_header_panel(self):
        result = build([PanelInfo('A', 'a', no_header=True), PanelInfo('B', 'b'),
                        PanelInfo('C', 'c', no_header=True)])
        self.assertEqual([p.idname for p in result], ['A', 'C', 'B'])


class TabOrderTest(unittest.TestCase):
    def test_tabs_follow_their_first_top_level_panel(self):
        panels = [PanelInfo('A1', 'a'), PanelInfo('B1', 'b'), PanelInfo('A2', 'a'),
                  PanelInfo('C1', 'c', parent_id='A1'), PanelInfo('C2', 'c')]
        self.assertEqual(order.tab_order(panels), ['a', 'b', 'c'])

    def test_only_shown_panels_place_a_tab(self):
        panels = [PanelInfo('A1', 'a'), PanelInfo('B1', 'b'), PanelInfo('A2', 'a')]
        self.assertEqual(order.tab_order(panels, shown={'B1', 'A2'}), ['b', 'a'])


class FinalTabsTest(unittest.TestCase):
    def test_item_first_then_wanted_then_the_rest(self):
        tabs = order.final_tabs(['View', 'Gone', 'Tool'], ['Tool', 'Item', 'View', 'New'])
        self.assertEqual(tabs, ['Item', 'View', 'Tool', 'New'])

    def test_item_stays_first_when_listed_later(self):
        self.assertEqual(order.final_tabs(['Tool', 'Item'], ['Item', 'Tool']), ['Item', 'Tool'])


class PlannedOrderTest(unittest.TestCase):
    def test_rank_then_own_order(self):
        self.assertEqual(order.planned_order(2, 7), 2007)

    def test_own_order_is_held_inside_the_step(self):
        self.assertEqual(order.planned_order(1, 5000), 1999)
        self.assertEqual(order.planned_order(1, -3), 1000)


class SimulateTest(unittest.TestCase):
    # Like the sidebar: Item's C panels first (never moved), Tool with a
    # panel without header, MMD and Renamer with their own bl_order
    PANELS = [
        PanelInfo('VIEW3D_PT_transform', 'Item'),
        PanelInfo('ITEM_PT_py', 'Item'),
        PanelInfo('TOOL_PT_active', 'Tool', no_header=True),
        PanelInfo('TOOL_PT_a', 'Tool'),
        PanelInfo('MMD_PT_a', 'MMD', order=1),
        PanelInfo('MMD_PT_b', 'MMD', order=11),
        PanelInfo('MMD_PT_child', 'MMD', parent_id='MMD_PT_a'),
        PanelInfo('REN_PT_a', 'Renamer', order=0),
        PanelInfo('REN_PT_b', 'Renamer', order=3),
    ]

    def run_plan(self, wanted, fixed=('VIEW3D_PT_transform',)):
        panels = build(self.PANELS)
        tabs = order.final_tabs(wanted, order.tab_order(panels))
        movable = [p for p in panels if p.idname not in fixed]
        sequence = order.registration_sequence(movable, tabs)
        return tabs, order.simulate(panels, sequence, tabs)

    def test_renamer_before_mmd_despite_their_own_orders(self):
        tabs, result = self.run_plan(['Renamer', 'MMD', 'Tool'])
        shown = {p.idname for p in result} - {'TOOL_PT_active'}
        self.assertEqual(order.tab_order(result, shown=shown), ['Item', 'Renamer', 'MMD', 'Tool'])

    def test_order_inside_a_tab_is_kept(self):
        _, result = self.run_plan(['MMD'])
        mmd = [p.idname for p in result if p.category == 'MMD' and not p.parent_id]
        self.assertEqual(mmd, ['MMD_PT_a', 'MMD_PT_b'])

    def test_sub_panels_come_after_their_parent(self):
        panels = build(self.PANELS)
        sequence = order.registration_sequence(panels, ['MMD'])
        names = [p.idname for p in sequence]
        self.assertLess(names.index('MMD_PT_a'), names.index('MMD_PT_child'))

    def test_a_shown_panel_without_header_pulls_its_tab_forward(self):
        # A known limit, as in Blender without this add-on: Tool's panel
        # without a header goes ahead of every panel with one, Item's C
        # panels too, so Tool comes first while that panel is shown
        tabs, result = self.run_plan(['Renamer', 'MMD', 'Tool'])
        self.assertEqual(order.tab_order(result), ['Tool', 'Item', 'Renamer', 'MMD'])


if __name__ == '__main__':
    unittest.main()
