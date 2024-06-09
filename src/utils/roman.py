#!/usr/bin/env python
'''Roman numeric class'''


class RomanNumeric:
    '''A utility class for Roman Numeric

    Roman Numeric Syntax:

    1. The value of the symbol is added to itself, as many times as it is repeated.
       For example, II, XX and XXX equals 2, 20 and 30, respectively.

    2. A symbol can be repeated only for three times. For example XXX (30) and
       CC (200) are valid while XXXX and CCCC are invalid.

    3. Symbols V, L, and D are never repeated.

    4. When a symbol of smaller value appears after a symbol of greater value,
       its values will be added. For Example,  VI = V + I = 5 + 1 = 6.

    5. When a symbol of a smaller value appears before a greater value symbol,
       it will be subtracted. For Example,  IX = X – I = 10 – 1 = 9.

    6. The symbols V, L, and D are never subtracted, as they are not written
       before a greater value symbol.

    7. The symbol I can be subtracted from V and X only and symbol X can be
       subtracted from symbols L, C and M only.
    '''
    valid_chars = {'I': 1, 'V': 5, 'X': 10, 'L': 50,
                   'C': 100, 'D': 500, 'M': 1000}

    def _contain_invalid_chars(self, txt: str) -> bool:
        '''Check if txt is a valid Roman numeric

        Args:
            txt (str): the string to check if any invalid character is present

        Return:
            True if a non-Roman numeric character is present; otherwise, False
        '''
        # Check if txt contains any invalid characters
        if any(t not in self.valid_chars for t in txt.upper()):
            return True
        return False

    def is_valid(self, txt: str) -> bool:
        '''Check if txt is a valid Roman numeric

        Args:
            txt (str): the string to check if it is a valid Roman numeric

        Return:
            True if the input is a valid Roman numeric; otherwise, False
        '''
        return self.to_int(txt) is not None

    def to_int(self, txt: str) -> int:
        '''Convert from txt containing a valid Roman numeric to an integer

        Args:
            txt (str): the Roman numeric string to be converted to an integer

        Return:
            An integer if the input is a valid Roman numeric; otherwise, None.
        '''
        if self._contain_invalid_chars(txt):
            return None
        txt = txt.upper()
        total = prev_char_value = cur_word_value = cur_char_count = 0
        max_repeat = 3
        for cur_char in txt:
            cur_val = self.valid_chars[cur_char]
            if prev_char_value == 0:
                # The first character
                cur_char_count += 1
                cur_word_value = cur_val
                prev_char_value = cur_val
            elif cur_val == prev_char_value:
                # Repeating characters
                if cur_val in [5, 50, 500]:
                    return None
                if cur_char_count < max_repeat:
                    cur_char_count += 1
                    cur_word_value += cur_val
                else:
                    # The current char repeats more than 3 times
                    return None
            elif cur_val > prev_char_value:
                # The value of the previous word is less than the current
                # character. We need to deduct the value of the previous
                # word from the value of the current character.
                if prev_char_value in [5, 50, 500]:
                    return None
                if (prev_char_value == 1 and cur_val not in [5, 10]) or \
                        (prev_char_value == 10 and
                         cur_val not in [50, 100, 1000]):
                    return None
                cur_char_count = 1
                cur_word_value = cur_val - cur_word_value
                prev_char_value = cur_val
            elif cur_val < prev_char_value:
                # The value of the previous word is greater than the current
                # character. Add the value of the previous word to total
                total += cur_word_value
                cur_char_count = 1
                cur_word_value = cur_val
                prev_char_value = cur_val
        total += cur_word_value
        return total

    def to_roman(self, num: int) -> str:
        '''TODO: Convert from an integer to a Roman numeric'''


def test_roman_numeric():
    '''The test function for the RomanNumeric class'''
    test_vector = {
        'III': 3,
        'IIII': None,
        'VII': 7,
        'LXXX': 80,
        'MCCC': 1300,
        'LXIX': 69,
        'MCMLXXXIV': 1984,
    }

    for txt, value in test_vector.items():
        assert value == RomanNumeric().to_int(txt)


if __name__ == '__main__':
    test_roman_numeric()
