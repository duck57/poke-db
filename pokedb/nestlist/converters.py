"""
URL converters for use in urls.py
"""


class FourDigitYearConverter:
    """
    Unused but taken right from the Django documentation as an example
    """

    regex = "[0-9]{4}"

    def to_python(self, value):
        return int(value)

    def to_url(self, value):
        return "%04d" % value


class FloatConverter:
    regex = "[+-]?[\d\.\d]+"

    def to_python(self, value):
        return float(value)

    def to_url(self, value):
        return f"{value:.8}"


class RomanNumeralConverter:
    regex = "[MDCLXVImdclxvi]+"

    def to_python(self, value):
        return str(value)

    def to_url(self, value):
        return "{}".format(value)
