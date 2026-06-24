import unittest

from deezer import AppleTrackMetadata, DeezerCandidate, DeezerAuthenticationError, arl_from_browser_cookie, arl_from_callback, cbc_secret_from_script, score_candidate, normalize


class DeezerMatchingTests(unittest.TestCase):
    def setUp(self):
        self.track = AppleTrackMetadata('Song Name (feat. Guest)', 'Main Artist', 'Album Name', 210)

    def test_normalization_removes_accents_and_feature_credit(self):
        self.assertEqual(normalize('Beyoncé - Song (feat. X)'), 'beyonce song')

    def test_exact_candidate_is_high_confidence(self):
        candidate = DeezerCandidate(1, 'Song Name', 'Main Artist', 'Album Name', 211)
        self.assertGreaterEqual(score_candidate(self.track, candidate), 80)

    def test_wrong_artist_is_rejected(self):
        candidate = DeezerCandidate(1, 'Song Name', 'Different Artist', 'Album Name', 210)
        self.assertLess(score_candidate(self.track, candidate), 80)

    def test_large_duration_difference_loses_duration_credit(self):
        close = DeezerCandidate(1, 'Song Name', 'Main Artist', 'Album Name', 211)
        long = DeezerCandidate(2, 'Song Name', 'Main Artist', 'Album Name', 600)
        self.assertGreater(score_candidate(self.track, close), score_candidate(self.track, long))

    def test_callback_link_extracts_session_without_exposing_raw_input(self):
        self.assertEqual(arl_from_callback('deezer://login/a1b2c3d4/callback'), 'a1b2c3d4')

    def test_non_deezer_callback_is_rejected(self):
        with self.assertRaises(DeezerAuthenticationError):
            arl_from_callback('https://example.test/callback')

    def test_browser_session_cookie_is_validated(self):
        self.assertEqual(arl_from_browser_cookie({'name': 'arl', 'value': 'a1b2c3d4'}), 'a1b2c3d4')
        with self.assertRaises(DeezerAuthenticationError):
            arl_from_browser_cookie(None)

    def test_current_web_player_decoder_shape_is_supported(self):
        script = 'const first=[0x61,0x39,0x76,0x30,0x77,0x35,0x65,0x67],second=[0x31,0x6e,0x66,0x7a,0x63,0x38,0x6c,0x34];'
        self.assertEqual(cbc_secret_from_script(script), 'g4el58wc0zvf9na1')


if __name__ == '__main__':
    unittest.main()
