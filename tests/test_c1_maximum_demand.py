import pytest

import as_nzs_3000_tools.c1_maximum_demand as c1


class TestLoadGroupA1:
    def test_max_demand_1_to_20_points(self):
        load = c1.LoadGroupA1(rating=10, num_load=20)
        assert load.maximum_demand_a == 3

    def test_max_demand_21_points(self):
        load = c1.LoadGroupA1(rating=10, num_load=21, rating_type="W")
        assert load.maximum_demand_a == 5

    def test_max_demand_40_points(self):
        load = c1.LoadGroupA1(rating=10, num_load=40, rating_type="W")
        assert load.maximum_demand_a == 5

    def test_str(self):
        load = c1.LoadGroupA1(rating=10, num_load=20, rating_type="W")
        print(str(load))


class TestLoadGroupA2:
    def test_str(self):
        load = c1.LoadGroupA2(rating=50, num_load=21, rating_type="W")
        print(str(load))

    def test_under_1000w_raises_exception(self):
        with pytest.raises(c1.IncorrectLoadGroupException) as exc_info:
            c1.LoadGroupA2(rating=10, num_load=21, rating_type="W")
        assert exc_info.value.correct_group is c1.LoadGroupA1


class TestLoadGroupE:
    def test_str(self):
        load = c1.LoadGroupE(
            rating=6000, num_load=1, rating_type="W", num_living_units=1
        )
        print(str(load))
