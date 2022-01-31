"""
Implemetation of Constrained Cubic Spline Interpolation in Python
Returns zero if division by zero occurs
Contains all CCSI formulae and helper functions.
Can be executed to run a Test of all formulae."""

import xlwings as xw


def simple_slope(i: int, x: list[float], y: list[float]) -> float:
    """Return simple rise over_run slope of line from (xi,yi) to (xi+1, yi+1)"""
    return (y[i + 1] - y[i]) / (x[i + 1] - x[i])


def f_prime(i: int, x: list[float], y: list[float]) -> float:
    if i == 0:
        return f_prime_first(x, y)
    if i == len(x) - 1:
        return f_prime_last(x, y)
    return 2 / (simple_slope(i, y, x) + simple_slope(i - 1, y, x))


def f_prime_first(x: list[float], y: list[float]) -> float:
    return ((3/2) * simple_slope(0, x, y)) - (f_prime(1, x, y) / 2)


def f_prime_last(x: list[float], y: list[float]) -> float:
    n = len(x) - 1
    return ((3 / 2) * simple_slope(n - 1, x, y)) - (f_prime(n - 1, x, y) / 2)


def f_prime2_prev(i: int, x: list[float], y: list[float]) -> float:
    xi = x[i]
    prev_x = x[i - 1]

    n1 = (2 * f_prime(i, x, y)) + (4 * f_prime(i - 1, x, y))
    d1 = xi - prev_x

    n2 = 6 * (y[i] - y[i - 1])
    d2 = (xi - prev_x) ** 2

    return n2/d2 - n1/d1


def f_prime2(i: int, x: list[float], y: list[float]) -> float:
    xi = x[i]
    prev_x = x[i - 1]

    n1 = (4 * f_prime(i, x, y)) + (2 * f_prime(i - 1, x, y))
    n2 = 6 * (y[i] - y[i - 1])
    d1 = xi - prev_x
    d2 = (xi - prev_x) ** 2

    return n1/d1 - n2/d2


def d(i: int, x: list[float], y: list[float]) -> float:
    num = f_prime2(i, x, y) - f_prime2_prev(i, x, y)
    den = 6 * (x[i] - x[i - 1])

    return num / den


def c(i: int, x: list[float], y: list[float]) -> float:
    xi = x[i]
    prev_x = x[i - 1]

    num = xi * f_prime2_prev(i, x, y) - prev_x * f_prime2(i, x, y)
    denom = 2 * (xi - prev_x)

    return num / denom


def b(i: int, x: list[float], y: list[float]) -> float:
    xi = x[i]
    prev_x = x[i - 1]
    yi = y[i]
    prev_y = y[i - 1]

    num = (yi - prev_y) - c(i, x, y) * ((xi ** 2) - (prev_x ** 2)) - d(i, x, y) * ((xi ** 3) - (prev_x ** 3))
    denom = xi - prev_x

    return num / denom


def a(i: int, x: list[float], y: list[float]) -> float:
    prev_x = x[i - 1]
    prev_y = y[i - 1]

    return prev_y - (b(i, x, y) * prev_x) - (c(i, x, y) * (prev_x ** 2)) - (d(i, x, y) * (prev_x ** 3))


def f(x_val: float, x: list[float], y: list[float]) -> float:
    """Full Constrained Cubic Spline Interpolation function.
    x_val: any float value to be used to derive an output
    x: a list of floats in the domain of f
    y: a list of floats in the range of f **must have the same cardinality as x**"""

    n = len(x)
    i = None
    if x_val < x[0]:
        i = 0
    elif x_val >= x[-1]:
        i = n - 1
    else:
        for j in range(1, n):
            if x_val <= x[j]:
                i = j
                break
        if i is None:
            i = n - 1

    try:
        return a(i, x, y) + (b(i, x, y) * x_val) + (c(i, x, y) * (x_val ** 2)) + (d(i, x, y) * (x_val ** 3))
    except ZeroDivisionError:
        return 0


if __name__ == "__main__":


    book = xw.Book("Book2.xlsx")
    sheet = book.sheets["Sheet1"]

    # src_row = 737
    row = 2

    for m in range(5):
        output = [[], [], [], [], [], []]
        # src_offset = m * 21
        offset = m * 9
        # sheet.range(f"A{row + offset}").value = src_sheet.range(f"C{src_row + src_offset}").value
        # sheet.range(f"B{row + offset}").value = \
        #     src_sheet.range(f"M{src_row + src_offset}:W{src_row + 7 + src_offset}").value

        x_list = sheet.range(f"O{row + 1 + offset}:O{row + 7 + offset}").value
        y_list = sheet.range(f"P{row + 1 + offset}:P{row + 7 + offset}").value

        for r in range(1, 7):
            p = r - 1
            output[p].append(f_prime(r, x_list, y_list))
            output[p].append(f_prime(r - 1, x_list, y_list))
            output[p].append(f_prime2_prev(r, x_list, y_list))
            output[p].append(f_prime2(r, x_list, y_list))
            output[p].append(d(r, x_list, y_list))
            output[p].append(c(r, x_list, y_list))
            output[p].append(b(r, x_list, y_list))
            output[p].append(a(r, x_list, y_list))

        sheet.range(f"Q{row + 2 + offset}:X{row + 7 + offset}").value = output
