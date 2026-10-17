"""The 64 benchmark dates of ``shared/spec/BENCHMARK.md``, computed and committed.

``DATES_BS`` and ``DATES_PATRO`` are literals so the benchmark inputs do not change with the
calendar tables. ``computed_bs``, ``computed_ad``, ``computed_text`` and ``computed_patro``
recompute them from ``_calendar.py`` and the patro coverage; a test checks that both agree.
"""

from __future__ import annotations

import datetime
from bisect import bisect_right

from nepdate._calendar import MONTH_NUM, MONTH_START_ORD, MONTH_YEAR, ORDINAL_OFFSET
from nepdate_patro._tables import COVERAGE_FIRST, COVERAGE_LAST

DATES_BS: tuple[tuple[int, int, int], ...] = (
    (2000, 1, 1),
    (2001, 6, 7),
    (2002, 11, 20),
    (2004, 4, 28),
    (2005, 10, 7),
    (2007, 3, 17),
    (2008, 8, 25),
    (2010, 2, 7),
    (2011, 7, 13),
    (2012, 12, 26),
    (2014, 6, 1),
    (2015, 11, 15),
    (2017, 4, 22),
    (2018, 10, 2),
    (2020, 3, 12),
    (2021, 8, 19),
    (2023, 2, 2),
    (2024, 7, 7),
    (2025, 12, 21),
    (2027, 5, 27),
    (2028, 11, 9),
    (2030, 4, 17),
    (2031, 9, 26),
    (2033, 3, 7),
    (2034, 8, 14),
    (2036, 1, 27),
    (2037, 7, 2),
    (2038, 12, 16),
    (2040, 5, 22),
    (2041, 11, 4),
    (2043, 4, 12),
    (2044, 9, 21),
    (2046, 3, 1),
    (2047, 8, 8),
    (2049, 1, 22),
    (2050, 6, 27),
    (2051, 12, 10),
    (2053, 5, 16),
    (2054, 10, 28),
    (2056, 4, 6),
    (2057, 9, 15),
    (2059, 2, 27),
    (2060, 8, 3),
    (2062, 1, 16),
    (2063, 6, 22),
    (2064, 12, 5),
    (2066, 5, 11),
    (2067, 10, 22),
    (2069, 4, 1),
    (2070, 9, 10),
    (2072, 2, 22),
    (2073, 7, 28),
    (2075, 1, 11),
    (2076, 6, 16),
    (2077, 11, 29),
    (2079, 5, 6),
    (2080, 10, 17),
    (2082, 3, 27),
    (2083, 9, 5),
    (2085, 2, 17),
    (2086, 7, 23),
    (2088, 1, 4),
    (2089, 6, 10),
    (2090, 11, 24),
)

DATES_AD: tuple[datetime.date, ...] = (
    datetime.date(1943, 4, 14),
    datetime.date(1944, 9, 22),
    datetime.date(1946, 3, 3),
    datetime.date(1947, 8, 12),
    datetime.date(1949, 1, 20),
    datetime.date(1950, 7, 1),
    datetime.date(1951, 12, 10),
    datetime.date(1953, 5, 20),
    datetime.date(1954, 10, 29),
    datetime.date(1956, 4, 8),
    datetime.date(1957, 9, 17),
    datetime.date(1959, 2, 26),
    datetime.date(1960, 8, 6),
    datetime.date(1962, 1, 15),
    datetime.date(1963, 6, 26),
    datetime.date(1964, 12, 4),
    datetime.date(1966, 5, 15),
    datetime.date(1967, 10, 24),
    datetime.date(1969, 4, 3),
    datetime.date(1970, 9, 12),
    datetime.date(1972, 2, 21),
    datetime.date(1973, 8, 1),
    datetime.date(1975, 1, 10),
    datetime.date(1976, 6, 20),
    datetime.date(1977, 11, 29),
    datetime.date(1979, 5, 10),
    datetime.date(1980, 10, 18),
    datetime.date(1982, 3, 29),
    datetime.date(1983, 9, 7),
    datetime.date(1985, 2, 15),
    datetime.date(1986, 7, 27),
    datetime.date(1988, 1, 5),
    datetime.date(1989, 6, 15),
    datetime.date(1990, 11, 24),
    datetime.date(1992, 5, 4),
    datetime.date(1993, 10, 13),
    datetime.date(1995, 3, 24),
    datetime.date(1996, 9, 1),
    datetime.date(1998, 2, 10),
    datetime.date(1999, 7, 22),
    datetime.date(2000, 12, 30),
    datetime.date(2002, 6, 10),
    datetime.date(2003, 11, 19),
    datetime.date(2005, 4, 29),
    datetime.date(2006, 10, 8),
    datetime.date(2008, 3, 18),
    datetime.date(2009, 8, 27),
    datetime.date(2011, 2, 5),
    datetime.date(2012, 7, 16),
    datetime.date(2013, 12, 25),
    datetime.date(2015, 6, 5),
    datetime.date(2016, 11, 13),
    datetime.date(2018, 4, 24),
    datetime.date(2019, 10, 3),
    datetime.date(2021, 3, 13),
    datetime.date(2022, 8, 22),
    datetime.date(2024, 1, 31),
    datetime.date(2025, 7, 11),
    datetime.date(2026, 12, 20),
    datetime.date(2028, 5, 30),
    datetime.date(2029, 11, 8),
    datetime.date(2031, 4, 19),
    datetime.date(2032, 9, 27),
    datetime.date(2034, 3, 8),
)

DATES_TEXT: tuple[str, ...] = (
    "2000/01/01",
    "2001/06/07",
    "2002/11/20",
    "2004/04/28",
    "2005/10/07",
    "2007/03/17",
    "2008/08/25",
    "2010/02/07",
    "2011/07/13",
    "2012/12/26",
    "2014/06/01",
    "2015/11/15",
    "2017/04/22",
    "2018/10/02",
    "2020/03/12",
    "2021/08/19",
    "2023/02/02",
    "2024/07/07",
    "2025/12/21",
    "2027/05/27",
    "2028/11/09",
    "2030/04/17",
    "2031/09/26",
    "2033/03/07",
    "2034/08/14",
    "2036/01/27",
    "2037/07/02",
    "2038/12/16",
    "2040/05/22",
    "2041/11/04",
    "2043/04/12",
    "2044/09/21",
    "2046/03/01",
    "2047/08/08",
    "2049/01/22",
    "2050/06/27",
    "2051/12/10",
    "2053/05/16",
    "2054/10/28",
    "2056/04/06",
    "2057/09/15",
    "2059/02/27",
    "2060/08/03",
    "2062/01/16",
    "2063/06/22",
    "2064/12/05",
    "2066/05/11",
    "2067/10/22",
    "2069/04/01",
    "2070/09/10",
    "2072/02/22",
    "2073/07/28",
    "2075/01/11",
    "2076/06/16",
    "2077/11/29",
    "2079/05/06",
    "2080/10/17",
    "2082/03/27",
    "2083/09/05",
    "2085/02/17",
    "2086/07/23",
    "2088/01/04",
    "2089/06/10",
    "2090/11/24",
)

DATES_PATRO: tuple[tuple[int, int, int], ...] = (
    (2077, 1, 1),
    (2077, 2, 14),
    (2077, 3, 26),
    (2077, 5, 7),
    (2077, 6, 20),
    (2077, 8, 4),
    (2077, 9, 18),
    (2077, 11, 3),
    (2077, 12, 18),
    (2078, 1, 31),
    (2078, 3, 13),
    (2078, 4, 26),
    (2078, 6, 7),
    (2078, 7, 20),
    (2078, 9, 5),
    (2078, 10, 19),
    (2078, 12, 4),
    (2079, 1, 18),
    (2079, 2, 31),
    (2079, 4, 12),
    (2079, 5, 25),
    (2079, 7, 7),
    (2079, 8, 21),
    (2079, 10, 6),
    (2079, 11, 21),
    (2080, 1, 5),
    (2080, 2, 18),
    (2080, 3, 30),
    (2080, 5, 11),
    (2080, 6, 24),
    (2080, 8, 8),
    (2080, 9, 22),
    (2080, 11, 8),
    (2080, 12, 22),
    (2081, 2, 5),
    (2081, 3, 17),
    (2081, 4, 30),
    (2081, 6, 11),
    (2081, 7, 25),
    (2081, 9, 9),
    (2081, 10, 24),
    (2081, 12, 9),
    (2082, 1, 22),
    (2082, 3, 4),
    (2082, 4, 16),
    (2082, 5, 29),
    (2082, 7, 11),
    (2082, 8, 25),
    (2082, 10, 10),
    (2082, 11, 25),
    (2083, 1, 9),
    (2083, 2, 22),
    (2083, 4, 3),
    (2083, 5, 16),
    (2083, 6, 29),
    (2083, 8, 12),
    (2083, 9, 27),
    (2083, 11, 12),
    (2083, 12, 26),
    (2084, 2, 9),
    (2084, 3, 22),
    (2084, 5, 3),
    (2084, 6, 16),
    (2084, 7, 30),
)


def _serial(year: int, month: int, day: int) -> int:
    """Return the BS serial of a date from the generated month starts.

    Args:
        year: The BS year.
        month: The BS month, 1 through 12.
        day: The BS day.

    Returns:
        The BS serial, the ordinal minus ``ORDINAL_OFFSET``.
    """
    return MONTH_START_ORD[(year - 1901) * 12 + month - 1] + day - 1 - ORDINAL_OFFSET


def _from_serial(serial: int) -> tuple[int, int, int]:
    """Build a BS date from a serial using the generated month starts.

    Args:
        serial: The BS serial.

    Returns:
        ``(year, month, day)``.
    """
    ordinal = serial + ORDINAL_OFFSET
    index = bisect_right(MONTH_START_ORD, ordinal) - 1
    return (MONTH_YEAR[index], MONTH_NUM[index], ordinal - MONTH_START_ORD[index] + 1)


def _sample(
    first: tuple[int, int, int], last: tuple[int, int, int]
) -> tuple[tuple[int, int, int], ...]:
    """Return the 64 dates from ``first`` to ``last`` at the BENCHMARK step.

    Args:
        first: The first BS date.
        last: The last BS date.

    Returns:
        64 BS dates at serial ``s0 + i * ((s1 - s0) // 63)``.
    """
    s0 = _serial(*first)
    s1 = _serial(*last)
    step = (s1 - s0) // 63
    return tuple(_from_serial(s0 + i * step) for i in range(64))


def computed_bs() -> tuple[tuple[int, int, int], ...]:
    """Recompute the 64 core dates from ``_calendar.py``.

    Returns:
        The core dates, in benchmark order.
    """
    return _sample((2000, 1, 1), (2090, 12, 30))


def computed_ad() -> tuple[datetime.date, ...]:
    """Recompute the Gregorian equivalents of the core dates.

    Returns:
        The AD dates, in benchmark order.
    """
    return tuple(
        datetime.date.fromordinal(MONTH_START_ORD[(y - 1901) * 12 + m - 1] + d - 1)
        for y, m, d in computed_bs()
    )


def computed_text() -> tuple[str, ...]:
    """Format the core dates as ``YYYY/MM/DD``.

    Returns:
        The 64 text inputs, in benchmark order.
    """
    return tuple(f"{y:04d}/{m:02d}/{d:02d}" for y, m, d in computed_bs())


def computed_patro() -> tuple[tuple[int, int, int], ...]:
    """Recompute the 64 patro dates from the coverage range.

    Returns:
        The patro dates, in benchmark order.
    """
    first = _from_serial(COVERAGE_FIRST - ORDINAL_OFFSET)
    last = _from_serial(COVERAGE_LAST - ORDINAL_OFFSET)
    return _sample(first, last)
