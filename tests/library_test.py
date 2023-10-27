import pytest
import numpy as np

from footballdata.library import (
    year_at_season_start_list,
    get_season_years,
)


class Test_get_season_years:
    def test_normal_case(self):
        year = 2010
        expected_result = "2010-2011"
        result = get_season_years(year)

        assert result == expected_result

    def test_two_digits_input(self):
        year = 10
        with pytest.raises(KeyError):
            get_season_years(year)

    def test_no_int_year(self):
        year_0 = "2010"
        expected_result = "2010-2011"
        result = get_season_years(year_0)
        assert result == expected_result

        year_1 = [2010]
        with pytest.raises(TypeError):
            get_season_years(year_1)

    def test_incorrect_year(self):
        year = 1000
        with pytest.raises(KeyError):
            get_season_years(year)


class Test_year_at_season_start_list:
    def test_normal_case(self):
        """Test the normal case when the user gives correct input"""
        year_range = "2010-2020"
        expected_result = np.array(
            [2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019]
        )
        result = np.array(year_at_season_start_list(year_range=year_range))

        assert expected_result.size == result.size
        assert np.array_equal(result, expected_result)

    def test_incorrect_type(self):
        year_range = [2019, 2022]
        with pytest.raises(TypeError):
            year_at_season_start_list(year_range=year_range)

    def test_reverse_range(self):
        """Test the case where the last year of the range is not greater than the first."""
        year_range = "2010-2009"
        with pytest.raises(KeyError):
            year_at_season_start_list(year_range=year_range)

    def test_wrong_input_format(self):
        """Test the case where the format of the year range was wrong."""
        year_range = "2010/2015"
        with pytest.raises(KeyError):
            year_at_season_start_list(year_range=year_range)
