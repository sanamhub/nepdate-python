# P3: Formatting and parsing

Read first: `shared/spec/FORMATTING.md`, `shared/spec/PARSING.md`, `docs/API.md` (formatting,
parse), PARITY D-04, D-05, D-06, D-15.

## Tasks

### P3-01 Names and digits
Name tuples per FORMATTING §1. `to_nepali_digits` with `str.maketrans` over `"0123456789"`.
AC: `to_nepali_digits(2081) == "२०८१"`.

### P3-02 `__str__`, `__repr__`, `isoformat`, `short`, `long`
Own formatter; never `strftime` (its flags differ by OS and `%B` depends on the locale).
Per ADR-0002 §4: name tuples and precomputed digit strings (`_DAY_NE_PAD`, `_DAY_NE`, 33 entries
each, and `_YEAR_NE`, 299 entries, built once at import with `str.translate`; ASCII versions the
same way), and each format is one f-string over table lookups. No `str.translate`, `join` or
`int` to `str` conversion per call for Nepali output.
AC: golden `dates.tsv` columns `to_string`, `unicode`, `long_en`, `long_en_weekday`, `long_ne`,
`long_ne_weekday`, `dmy_dash_nopad`.

### P3-03 `format` and `__format__` (FORMATTING §5)
The pattern is tokenised once per distinct pattern (`functools.lru_cache(maxsize=128)`; safe
under free-threading). `format(d, "")` is `str(d)`.
AC: golden `format-pattern.tsv` (451 rows), skipping only D-04 rows (pattern has an `MMM` token, a
run of exactly three `M`, and the `bs` month is 3 or 6; FORMATTING §6) with a comment naming D-04;
the FORMATTING §5 examples.

### P3-04 Strict `parse` (PARSING §1)
A left-to-right scanner written as PARSING §1 says, step by step, so the error kinds come out in the
spec's order (with a regex that order is hard to reproduce). In front of the scanner, the fast
path of ADR-0002 §5: if `s.isascii()` and `s.split("/")` (then `"-"`) gives exactly three
non-empty groups of at most 4 characters each, all ASCII digits (`isdigit()` is safe here only
because `isascii()` was checked first), validate the three ints and build the date; otherwise, and
for every error, call the scanner. Mixed separators, leading or trailing separators and Devanagari
digits all go to the scanner, which accepts them per PARSING §1. In the scanner a digit is a
character in `"0123456789"` or in U+0966..U+096F, tested explicitly, never `\d` or `str.isdigit()`
(they accept every Unicode digit); at most 4 digits per group.
AC: the `strict` column of every row of `shared/spec/vectors/parse.tsv` (57 rows; `ERR:<Kind>` maps
to `ErrorKind`, for example `ERR:WrongGroupCount` to `WRONG_GROUP_COUNT`); `parse("٢٠٨٠/٠٥/١٥")`
(Arabic-Indic digits) raises `INVALID_CHARACTER`; hypothesis: arbitrary text raises only
`NepDateError`; hypothesis: for any text, the fast path either declines or returns the same date
as the scanner alone (the test calls the private scanner directly).
`shared/spec/vectors/csharp-golden/parse.tsv` is not a test target: it records C# behaviour that
D-05 and D-06 change (PARSING, intro).

### P3-05 `parse_lenient` (PARSING §2)
NFC-normalise, strip U+200C/U+200D, then the closed month-name list from the spec.
AC: the `lenient` column of every row of `shared/spec/vectors/parse.tsv`; hypothesis: arbitrary text
raises only `NepDateError`.

### P3-06 C# catalogue rows
`tests/test_csharp_catalog.py`: one test per catalogue row tagged phase 3 (`00-ROADMAP.md`, "C# test
catalogue").

## Checkpoint (stop here for review)

The reviewer checks:
- [ ] `uv run python scripts/ci.py` ends with `ci: 7/7 gates passed`.
- [ ] No `strftime`, `strptime` or locale call anywhere in `src/nepdate/`.
- [ ] `long`, `short` and `__str__` use the precomputed tables; no per-call `translate` or `join`
      for Nepali digits.
- [ ] The strict parser's error kinds come only from the scanner; the fast-path property test
      exists and runs in gate 3.
- [ ] No `\d`, `str.isdigit()` or `int()` on text that is not already known to be ASCII digits
      (`int()` accepts every Unicode digit and `_`).
- [ ] A quick `timeit` of B5 and B6 on the 64 dates is within the ADR-0002 §8 targets on CPython
      3.13, or the PR says by how much it misses.
- [ ] Every C# catalogue row tagged phase 3 has a test named after its `id` or a comment naming the
      deviation (D-04, D-05, D-06 rows say so).
