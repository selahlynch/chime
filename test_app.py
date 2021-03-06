import pytest
import pandas as pd

from app import (S_default, known_infections, known_cases, current_hosp, doubling_time, relative_contact_rate,
                 hosp_rate, icu_rate, vent_rate, hosp_los, icu_los, vent_los, market_share, S, initial_infections,
                 detection_prob, hospitalization_rates, I, R, beta, gamma, n_days, beta_decay,
                 projection_admits, alt)
from penn_chime.models import sir, sim_sir, sim_sir_df
from penn_chime.presentation import display_header, new_admissions_chart


# set up

# we just want to verify that st _attempted_ to render the right stuff
# so we store the input, and make sure that it matches what we expect
class MockStreamlit:
    def __init__(self):
        self.render_store = []
        self.markdown = self.just_store_instead_of_rendering
        self.latex = self.just_store_instead_of_rendering
        self.subheader = self.just_store_instead_of_rendering

    def just_store_instead_of_rendering(self, inp, *args, **kwargs):
        self.render_store.append(inp)
        return None

    def cleanup(self):
        """
        Call this after every test, unless you intentionally want to accumulate stuff-to-render
        """
        self.render_store = []


st = MockStreamlit()


# test presentation


def test_penn_logo_in_header():
    penn_css = '<link rel="stylesheet" href="https://www1.pennmedicine.org/styles/shared/penn-medicine-header.css">'
    display_header(st, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
    assert len(
        list(filter(lambda s: penn_css in s, st.render_store))
    ), "The Penn Medicine header should be printed"


def test_the_rest_of_header_shows_up():
    random_part_of_header = "implying an effective $R_t$ of"
    assert len(
        list(filter(lambda s: random_part_of_header in s, st.render_store))
    ), "The whole header should render"


st.cleanup()


@pytest.mark.xfail()
def test_header_fail():
    """
    Just proving to myself that these tests work
    """
    some_garbage = "ajskhlaeHFPIQONOI8QH34TRNAOP8ESYAW4"
    display_header(st, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
    assert len(
        list(filter(lambda s: some_garbage in s, st.render_store))
    ), "This should fail"
    st.cleanup()


# Test the math

def test_sir():
    """
    Someone who is good at testing, help
    """
    assert sir(100, 1, 0, 0.2, 0.5, 1) == (
        0.7920792079207921,
        0.20297029702970298,
        0.0049504950495049506,
    ), "This contrived example should work"

    # Certain things should *not* work
    with pytest.raises(TypeError) as E:
        sir("S", 1, 0, 0.2, 0.5, 1)
    assert str(E.value) == "can't multiply sequence by non-int of type 'float'"

    with pytest.raises(TypeError) as E:
        sir(100, "I", 0, 0.2, 0.5, 1)
    assert str(E.value) == "can't multiply sequence by non-int of type 'float'"

    with pytest.raises(TypeError) as E:
        sir(100, 1, "R", 0.2, 0.5, 1)
    assert str(E.value) == "unsupported operand type(s) for +: 'float' and 'str'"

    with pytest.raises(TypeError) as E:
        sir(100, 1, 0, "beta", 0.5, 1)
    assert str(E.value) == "bad operand type for unary -: 'str'"

    with pytest.raises(TypeError) as E:
        sir(100, 1, 0, 0.2, "gamma", 1)
    assert str(E.value) == "unsupported operand type(s) for -: 'float' and 'str'"

    with pytest.raises(TypeError) as E:
        sir(100, 1, 0, 0.2, 0.5, "N")
    assert str(E.value) == "unsupported operand type(s) for /: 'str' and 'float'"

    # Zeros across the board should fail
    with pytest.raises(ZeroDivisionError):
        sir(0, 0, 0, 0, 0, 0)


def test_sim_sir():
    """
    Rounding to move fast past decimal place issues
    """
    s, i, r = sim_sir(S, I, R, beta, gamma, n_days, beta_decay=beta_decay)
    assert round(s[0], 0) == 4119405
    assert round(i[0], 2) == 533.33
    assert round(r[0], 0) == 0.0
    assert round(s[-1], 2) == 3421436.31
    assert round(i[-1], 2) == 418157.62
    assert round(r[-1], 2) == 280344.40


def test_sim_sir_df():
    """
    Rounding to move fast past decimal place issues
    """
    df = sim_sir_df(S, I, R, beta, gamma, n_days, beta_decay=beta_decay)
    first = df.iloc[0]
    last = df.iloc[-1]
    assert round(first[0], 0) == 4119405
    assert round(first[1], 2) == 533.33
    assert round(first[2], 0) == 0.0
    assert round(last[0], 2) == 3421436.31
    assert round(last[1], 2) == 418157.62
    assert round(last[2], 2) == 280344.40


def test_initial_conditions():
    """
    Note: For the rates (ie hosp_rate) - just change the value, leave the "100" alone.
        Easier to change whole numbers than decimals.
    """
    assert current_hosp == known_cases
    assert doubling_time == 6
    assert relative_contact_rate == 0
    assert hosp_rate == 5 / 100
    assert icu_rate == 2 / 100
    assert vent_rate == 1 / 100
    assert hosp_los == 7
    assert icu_los == 9
    assert vent_los == 10
    assert market_share == 15 / 100
    assert S == S_default
    assert initial_infections == known_infections


def test_derived_variables():
    assert hospitalization_rates == (hosp_rate, icu_rate, vent_rate)
    assert detection_prob == initial_infections / (current_hosp / market_share / hosp_rate)


def test_new_admissions_chart():
    chart = new_admissions_chart(alt, projection_admits, n_days - 10)
    assert type(chart) == alt.Chart
    assert chart.data.iloc[1].Hospitalized < 1
    assert round(chart.data.iloc[49].ICU, 0) == 43
    with pytest.raises(TypeError):
        new_admissions_chart()

    empty_chart = new_admissions_chart(alt, pd.DataFrame(), -1)
    assert empty_chart.data.empty
