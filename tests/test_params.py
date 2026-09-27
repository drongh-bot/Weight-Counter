# tests/test_params.py
"""Params 三组结构：默认值、组间独立、params_from 自动分组。"""

from app.models.params import FixedParams, Params, StartParams, params_from, pick


class TestDefaults:
    def test_start_defaults(self):
        s = StartParams()
        assert (s.initial_min_weight, s.tolerance_percent, s.stability_threshold) == (
            0.5,
            20.0,
            0.02,
        )
        assert (s.max_batch_pieces, s.initial_single_pieces, s.decimal_places) == (
            1,
            5,
            2,
        )

    def test_fixed_defaults(self):
        f = FixedParams()
        assert (f.stability_short_win, f.stability_long_win) == (5, 10)
        assert (f.port, f.baud_rate, f.encoding) == ("COM1", 9600, "utf-8")
        assert f.splitter_sizes == [400, 600]

    def test_top_level_defaults(self):
        p = Params()
        assert p.target_pieces == 100
        assert isinstance(p.start, StartParams)
        assert isinstance(p.fixed, FixedParams)


class TestGroupsAreIndependent:
    """每次构造都要拿到全新的子对象 —— 否则测试之间会互相污染。"""

    def test_sub_objects_are_not_shared(self):
        a, b = Params(), Params()
        a.start.tolerance_percent = 99.0
        assert b.start.tolerance_percent == 20.0

    def test_splitter_sizes_uses_default_factory(self):
        a, b = Params(), Params()
        a.fixed.splitter_sizes.append(1)
        assert b.fixed.splitter_sizes == [400, 600]


class TestParamsFrom:
    def test_routes_each_field_to_its_group(self):
        p = params_from(
            tolerance_percent=15.0,  # → start
            stability_long_win=20,  # → fixed
            target_pieces=7,  # → 顶层
        )
        assert p.start.tolerance_percent == 15.0
        assert p.fixed.stability_long_win == 20
        assert p.target_pieces == 7

    def test_unspecified_fields_fall_back_to_defaults(self):
        p = params_from(tolerance_percent=15.0)
        assert p.start.decimal_places == 2  # 没传 → 默认
        assert p.fixed.port == "COM1"

    def test_unknown_field_is_dropped(self):
        """pick 按 dataclass 字段名挑，认不出的键直接丢掉，不抛异常。"""
        p = params_from(no_such_field=1)
        assert p.start == StartParams()
        assert p.fixed == FixedParams()

    def test_pick_only_returns_requested_class_fields(self):
        flat = {"tolerance_percent": 15.0, "stability_long_win": 20, "zzz": 1}
        assert pick(flat, StartParams) == {"tolerance_percent": 15.0}
        assert pick(flat, FixedParams) == {"stability_long_win": 20}
