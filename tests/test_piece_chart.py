from app.views.widgets.piece_chart import PieceChart


class TestPieceChart:
    def test_update_sets_scatter_count(self, qapp):
        chart = PieceChart(decimal_places=2)
        chart.show()
        chart.update_piece_weights([10.0, 20.0, 30.0])

        assert len(chart._piece_weights) == 3
        assert chart.scatter.data is not None
        assert len(chart.scatter.data) == 3

    def test_update_same_data_skips(self, qapp):
        chart = PieceChart()
        chart.show()
        chart.update_piece_weights([1.0, 2.0])
        data_before = chart.scatter.data

        chart.update_piece_weights([1.0, 2.0])
        assert chart.scatter.data is data_before

    def test_update_empty_resets(self, qapp):
        chart = PieceChart()
        chart.show()
        chart.update_piece_weights([1.0, 2.0])
        chart.update_piece_weights([])

        assert chart._piece_weights == []
        assert len(chart.scatter.data) == 0
        assert chart.scrollbar.isHidden()

    def test_update_empty_while_hidden_clears_scatter(self, qapp):
        """隐藏时清空数据也要清散点，避免再次显示残留（B8）。"""
        chart = PieceChart()
        chart.show()
        chart.update_piece_weights([1.0, 2.0])
        assert len(chart.scatter.data) == 2
        chart.hide()
        chart.update_piece_weights([])
        assert chart._piece_weights == []
        assert len(chart.scatter.data) == 0
        chart.show()
        assert len(chart.scatter.data) == 0

    def test_set_decimal_places(self, qapp):
        chart = PieceChart(decimal_places=2)
        chart.set_decimal_places(3)
        assert chart._decimal_places == 3
        assert chart.plot.getAxis("top").decimals == 3
        assert chart.plot.getAxis("bottom").decimals == 3
