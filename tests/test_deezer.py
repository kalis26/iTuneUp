import unittest

from deezer import AppleTrackMetadata, DeezerCandidate, score_candidate, normalize


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


if __name__ == '__main__':
    unittest.main()
