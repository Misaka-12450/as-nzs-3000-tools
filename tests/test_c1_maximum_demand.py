import pytest

from src.as_nzs_3000.c1_maximum_demand import C1A1, C1A2, IncorrectLoadGroupException


class TestC1A1:
    def test_max_demand_1_to_20_points(self):
        load = C1A1(rating=10, num_load=20)
        assert load.maximum_demand_a == 3

    def test_max_demand_21_points(self):
        load = C1A1(rating=10, num_load=21, rating_type="W")
        assert load.maximum_demand_a == 5

    def test_max_demand_40_points(self):
        load = C1A1(rating=10, num_load=40, rating_type="W")
        assert load.maximum_demand_a == 7

    def test_str(self):
        load = C1A1(rating=10, num_load=20, rating_type="W")
        print(str(load))


class TestC1A2:
    def test_str(self):
        load = C1A2(rating=50, num_load=21, rating_type="W")
        print(str(load))

    def test_under_1000w_raises_exception(self):
        with pytest.raises(IncorrectLoadGroupException) as exc_info:
            C1A2(rating=10, num_load=21, rating_type="W")
        assert exc_info.value.correct_group is C1A1
