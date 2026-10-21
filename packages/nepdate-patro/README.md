# nepdate-patro

Tithi, public holidays and events for the Bikram Sambat calendar, as a separate distribution
from the core [`nepdate-core`](https://pypi.org/project/nepdate-core/) package. It is part of the
[NepDate](https://github.com/sanamhub/nepdate-python) family; the data comes from the hub
[`sanamhub/nepdate`](https://github.com/sanamhub/nepdate).

```console
pip install --pre nepdate-patro
```

`nepdate-patro` depends on the core package, so `nepdate-core` arrives with it. The import name is
`nepdate_patro`. `--pre` is needed while only pre-releases exist (0.1.0-beta.1 is `0.1.0b1` on
PyPI). The data is informational, not an official calendar.

```python
>>> from nepdate import NepaliDate
>>> from nepdate_patro import coverage, info, public_holidays
>>> day = info(NepaliDate(2081, 1, 1))
>>> day.tithi.label()
'Panchami'
>>> [event.label() for event in day.events]
['New Year', 'Mesh Sankranti', 'Bisket Jatra']
>>> coverage().start
NepaliDate(2077, 1, 1)
>>> len(list(public_holidays()))
294

```

`info` returns one prebuilt, immutable `CalendarInfo` per day. A date outside the coverage
returns the same empty object, so it never raises. The data currently covers BS 2077-01-01 to
2084-08-20.

The full API is in [docs/API.md](https://github.com/sanamhub/nepdate-python/blob/main/docs/API.md),
and the core package is in [nepdate-core](https://github.com/sanamhub/nepdate-python).
