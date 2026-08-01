from app.views.widgets.piece_table import PieceTable


class TestPieceTable:
    def test_update_newest_on_top(self, qapp):
        table = PieceTable(decimal_places=2)
        table.update_piece_weights([10.0, 20.0, 30.0])

        assert table.rowCount() == 3
        assert table.item(0, 0).text() == "30.00"
        assert table.item(1, 0).text() == "20.00"
        assert table.item(2, 0).text() == "10.00"
        assert table.verticalHeaderItem(0).text() == "3"

    def test_update_same_data_skips_rebuild(self, qapp):
        table = PieceTable()
        table.update_piece_weights([1.0, 2.0])
        item = table.item(0, 0)

        table.update_piece_weights([1.0, 2.0])
        assert table.item(0, 0) is item

    def test_update_empty_resets(self, qapp):
        table = PieceTable()
        table.update_piece_weights([1.0, 2.0])
        table.update_piece_weights([])
        assert table.rowCount() == 0
        assert table._piece_weights == []

    def test_set_decimal_places_reformats(self, qapp):
        table = PieceTable(decimal_places=2)
        table.update_piece_weights([10.5])
        assert table.item(0, 0).text() == "10.50"

        table.set_decimal_places(3)
        assert table.item(0, 0).text() == "10.500"
