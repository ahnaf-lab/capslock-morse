import unittest

from capslock_morse.morse import Signal, encode, encode_char, encode_status


class EncodeCharTests(unittest.TestCase):
    def test_dot_letter_e(self):
        self.assertEqual(encode_char("E"), [Signal(True, 1)])

    def test_dash_letter_t(self):
        self.assertEqual(encode_char("T"), [Signal(True, 3)])

    def test_multi_symbol_letter_has_symbol_gaps(self):
        # S is three dots: on, gap, on, gap, on
        self.assertEqual(
            encode_char("S"),
            [
                Signal(True, 1),
                Signal(False, 1),
                Signal(True, 1),
                Signal(False, 1),
                Signal(True, 1),
            ],
        )

    def test_lowercase_is_accepted(self):
        self.assertEqual(encode_char("e"), encode_char("E"))

    def test_digit_is_encoded(self):
        # 0 is five dashes, separated by 1-unit symbol gaps.
        expected = [Signal(True, 3)]
        for _ in range(4):
            expected.append(Signal(False, 1))
            expected.append(Signal(True, 3))
        self.assertEqual(encode_char("0"), expected)

    def test_unsupported_character_raises(self):
        with self.assertRaises(ValueError):
            encode_char("@")


class EncodeTextTests(unittest.TestCase):
    def test_single_letter_word(self):
        self.assertEqual(encode("E"), [Signal(True, 1)])

    def test_two_letter_word_has_char_gap(self):
        # "SOS"-style two-letter word to check the inter-character gap size.
        signals = encode("ET")
        self.assertEqual(
            signals,
            [Signal(True, 1), Signal(False, 3), Signal(True, 3)],
        )

    def test_two_words_have_word_gap(self):
        signals = encode("E E")
        self.assertEqual(
            signals,
            [Signal(True, 1), Signal(False, 7), Signal(True, 1)],
        )

    def test_empty_text_returns_empty_sequence(self):
        self.assertEqual(encode(""), [])

    def test_encoding_is_deterministic(self):
        self.assertEqual(encode("PASS"), encode("PASS"))

    def test_result_is_list_of_signal_tuples(self):
        for signal in encode("HELLO"):
            self.assertIsInstance(signal, Signal)
            self.assertIsInstance(signal.on, bool)
            self.assertGreater(signal.units, 0)


class EncodeStatusTests(unittest.TestCase):
    def test_known_status_code_matches_plain_text_encoding(self):
        self.assertEqual(encode_status("PASS"), encode("PASS"))

    def test_status_lookup_is_case_insensitive(self):
        self.assertEqual(encode_status("pass"), encode_status("PASS"))

    def test_unknown_status_falls_back_to_literal_text(self):
        self.assertEqual(encode_status("HI"), encode("HI"))


if __name__ == "__main__":
    unittest.main()
