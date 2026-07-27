#!/usr/bin/env python3
"""
Unit tests for parse_series.py.

Run:
    python3 scripts/test_parse_series.py
    python3 scripts/test_parse_series.py -v
"""

import os
import sys
import unittest

# Ensure we can import parse_series from the same directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from parse_series import parse_subject, slugify_subject, group_series


class TestParseSubject(unittest.TestCase):
    """Tests for parse_subject() — covers PATCH prefix, tip-bot, stable, replies."""

    # --- Basic PATCH prefixes ---

    def test_patch_no_version_no_seq(self):
        r = parse_subject('[PATCH] sched: foo')
        self.assertEqual(r['kind'], 'patch')
        self.assertEqual(r['base_subject'], 'sched: foo')
        self.assertEqual(r['version'], 1)
        self.assertIsNone(r['seq'])
        self.assertIsNone(r['total'])
        self.assertEqual(r['flags'], [])

    def test_patch_with_version(self):
        r = parse_subject('[PATCH v2] sched: foo')
        self.assertEqual(r['kind'], 'patch')
        self.assertEqual(r['base_subject'], 'sched: foo')
        self.assertEqual(r['version'], 2)
        self.assertIsNone(r['seq'])
        self.assertEqual(r['flags'], [])

    def test_patch_with_version_and_seq(self):
        r = parse_subject('[PATCH v3 1/7] sched: foo')
        self.assertEqual(r['kind'], 'patch')
        self.assertEqual(r['base_subject'], 'sched: foo')
        self.assertEqual(r['version'], 3)
        self.assertEqual(r['seq'], 1)
        self.assertEqual(r['total'], 7)
        self.assertEqual(r['flags'], [])

    # --- Flags position variations (Problem 4 fix) ---

    def test_patch_flags_after_seq(self):
        r = parse_subject('[PATCH v2 3/7 RFC] sched: foo')
        self.assertEqual(r['kind'], 'patch')
        self.assertEqual(r['base_subject'], 'sched: foo')
        self.assertEqual(r['version'], 2)
        self.assertEqual(r['seq'], 3)
        self.assertEqual(r['total'], 7)
        self.assertEqual(r['flags'], ['RFC'])

    def test_patch_flags_before_version(self):
        r = parse_subject('[PATCH RFC v2 1/4] sched: foo')
        self.assertEqual(r['kind'], 'patch')
        self.assertEqual(r['base_subject'], 'sched: foo')
        self.assertEqual(r['version'], 2)
        self.assertEqual(r['seq'], 1)
        self.assertEqual(r['total'], 4)
        self.assertEqual(r['flags'], ['RFC'])

    def test_patch_flags_before_version_and_seq(self):
        r = parse_subject('[PATCH RESEND v3 2/7] sched: foo')
        self.assertEqual(r['kind'], 'patch')
        self.assertEqual(r['base_subject'], 'sched: foo')
        self.assertEqual(r['version'], 3)
        self.assertEqual(r['seq'], 2)
        self.assertEqual(r['total'], 7)
        self.assertEqual(r['flags'], ['RESEND'])

    def test_patch_multiple_flags(self):
        r = parse_subject('[PATCH RFC RESEND v2 1/4] sched: foo')
        self.assertEqual(r['kind'], 'patch')
        self.assertEqual(r['base_subject'], 'sched: foo')
        self.assertEqual(r['version'], 2)
        self.assertEqual(r['seq'], 1)
        self.assertEqual(r['total'], 4)
        self.assertIn('RFC', r['flags'])
        self.assertIn('RESEND', r['flags'])
        self.assertEqual(len(r['flags']), 2)

    def test_patch_flags_only_no_version(self):
        r = parse_subject('[PATCH RESEND] sched: foo')
        self.assertEqual(r['kind'], 'patch')
        self.assertEqual(r['base_subject'], 'sched: foo')
        self.assertEqual(r['version'], 1)
        self.assertEqual(r['flags'], ['RESEND'])

    def test_patch_wip_flag(self):
        r = parse_subject('[PATCH WIP v2 1/4] sched: foo')
        self.assertEqual(r['kind'], 'patch')
        self.assertEqual(r['version'], 2)
        self.assertEqual(r['flags'], ['WIP'])

    # --- tip-bot notifications ---

    def test_tip_notification(self):
        r = parse_subject('[tip: sched/urgent] sched: fix foo')
        self.assertEqual(r['kind'], 'tip')
        self.assertEqual(r['branch'], 'sched/urgent')
        self.assertEqual(r['base_subject'], 'sched: fix foo')

    def test_tip_with_spaces(self):
        r = parse_subject('  [tip: sched/core ]   sched: bar')
        self.assertEqual(r['kind'], 'tip')
        self.assertEqual(r['branch'], 'sched/core')
        self.assertEqual(r['base_subject'], 'sched: bar')

    # --- stable-commit bot ---

    def test_stable_patch_stable(self):
        r = parse_subject('[patch stable] sched: fix foo')
        self.assertEqual(r['kind'], 'stable')
        self.assertEqual(r['base_subject'], 'sched: fix foo')

    def test_stable_for_stable(self):
        r = parse_subject('[for stable] sched: fix foo')
        self.assertEqual(r['kind'], 'stable')
        self.assertEqual(r['base_subject'], 'sched: fix foo')

    def test_stable_plain(self):
        r = parse_subject('[stable 5.15] sched: fix foo')
        self.assertEqual(r['kind'], 'stable')
        self.assertEqual(r['base_subject'], 'sched: fix foo')

    # --- Reply / discussion (Problem 5 fix) ---

    def test_reply_to_patch_strips_prefix(self):
        """Re: [PATCH v2 1/7] sched: foo should strip PATCH prefix for grouping."""
        r = parse_subject('Re: [PATCH v2 1/7] sched: foo')
        self.assertEqual(r['kind'], 'other')
        self.assertEqual(r['base_subject'], 'sched: foo')
        self.assertEqual(r['version'], 2)
        self.assertEqual(r['seq'], 1)
        self.assertEqual(r['total'], 7)

    def test_reply_to_patch_with_flags(self):
        """Re: [PATCH RFC v3 2/4] sched: foo should extract flags too."""
        r = parse_subject('Re: [PATCH RFC v3 2/4] sched: foo')
        self.assertEqual(r['kind'], 'other')
        self.assertEqual(r['base_subject'], 'sched: foo')
        self.assertEqual(r['version'], 3)
        self.assertEqual(r['seq'], 2)
        self.assertEqual(r['total'], 4)
        self.assertEqual(r['flags'], ['RFC'])

    def test_fwd_reply(self):
        r = parse_subject('Fwd: sched: foo discussion')
        self.assertEqual(r['kind'], 'other')
        self.assertEqual(r['base_subject'], 'sched: foo discussion')

    def test_plain_discussion(self):
        r = parse_subject('sched: foo discussion')
        self.assertEqual(r['kind'], 'other')
        self.assertEqual(r['base_subject'], 'sched: foo discussion')

    def test_multiple_re_prefixes(self):
        r = parse_subject('Re: Re: sched: foo discussion')
        self.assertEqual(r['kind'], 'other')
        self.assertEqual(r['base_subject'], 'sched: foo discussion')

    # --- Edge cases ---

    def test_empty_subject(self):
        r = parse_subject('')
        self.assertEqual(r['kind'], 'other')
        self.assertEqual(r['base_subject'], '')

    def test_whitespace_only_subject(self):
        r = parse_subject('   ')
        self.assertEqual(r['kind'], 'other')
        self.assertEqual(r['base_subject'], '')

    def test_patch_case_insensitive(self):
        r = parse_subject('[patch v2] sched: foo')
        self.assertEqual(r['kind'], 'patch')
        self.assertEqual(r['version'], 2)


class TestSlugifySubject(unittest.TestCase):
    """Tests for slugify_subject()."""

    def test_basic(self):
        self.assertEqual(
            slugify_subject('sched/fair: fix load balance'),
            'sched-fair-fix-load-balance',
        )

    def test_uppercase(self):
        self.assertEqual(
            slugify_subject('SCHED/FAIR: Fix Load Balance'),
            'sched-fair-fix-load-balance',
        )

    def test_brackets_and_colons(self):
        self.assertEqual(
            slugify_subject('[sched]: fix foo'),
            'sched-fix-foo',
        )

    def test_multiple_separators(self):
        self.assertEqual(
            slugify_subject('sched///fair:::  fix'),
            'sched-fair-fix',
        )

    def test_leading_trailing_dashes(self):
        self.assertEqual(
            slugify_subject('---sched: foo---'),
            'sched-foo',
        )

    def test_truncation(self):
        long_subject = 'a' * 100
        result = slugify_subject(long_subject)
        self.assertLessEqual(len(result), 60)

    def test_truncation_at_word_boundary(self):
        long_subject = 'sched-aaa-' + 'b' * 70
        result = slugify_subject(long_subject)
        self.assertLessEqual(len(result), 60)
        self.assertFalse(result.endswith('-'))

    def test_empty_string(self):
        self.assertEqual(slugify_subject(''), '')

    def test_only_special_chars(self):
        self.assertEqual(slugify_subject('///:::---'), '')

    def test_numbers_preserved(self):
        self.assertEqual(
            slugify_subject('sched v2 1/7'),
            'sched-v2-1-7',
        )


class TestGroupSeries(unittest.TestCase):
    """Tests for group_series() — series grouping logic."""

    def test_same_author_same_subject_different_versions(self):
        """v1 and v2 of same subject by same author should group together."""
        entries = [
            {'subject': '[PATCH v1] sched: foo', 'author': 'Alice'},
            {'subject': '[PATCH v2] sched: foo', 'author': 'Alice'},
        ]
        result = group_series(entries)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['base_subject'], 'sched: foo')
        self.assertEqual(result[0]['author'], 'Alice')
        self.assertEqual(result[0]['current_version'], 2)
        self.assertEqual(len(result[0]['versions']), 2)

    def test_different_authors_same_subject_not_grouped(self):
        """Same subject by different authors should NOT group together."""
        entries = [
            {'subject': '[PATCH] sched: foo', 'author': 'Alice'},
            {'subject': '[PATCH] sched: foo', 'author': 'Bob'},
        ]
        result = group_series(entries)
        self.assertEqual(len(result), 2)

    def test_tip_reply_groups_with_patch(self):
        """tip-bot reply should group with the original patch series."""
        entries = [
            {'subject': '[PATCH] sched: foo', 'author': 'Alice'},
            {'subject': '[tip: sched/urgent] sched: foo', 'author': 'tip-bot'},
        ]
        result = group_series(entries)
        self.assertEqual(len(result), 1)
        self.assertTrue(result[0]['has_tip'])
        self.assertIn('sched/urgent', result[0]['tip_branches'])

    def test_stable_reply_groups_with_patch(self):
        """stable-commit reply should group with the original patch series."""
        entries = [
            {'subject': '[PATCH] sched: foo', 'author': 'Alice'},
            {'subject': '[patch stable] sched: foo', 'author': 'stable-bot'},
        ]
        result = group_series(entries)
        self.assertEqual(len(result), 1)
        self.assertTrue(result[0]['has_stable'])

    def test_reply_to_patch_groups_correctly(self):
        """Re: [PATCH v2 1/7] sched: foo should group with the patch series
        (Problem 5 fix — reply strips PATCH prefix for grouping)."""
        entries = [
            {'subject': '[PATCH v2 1/7] sched: foo', 'author': 'Alice'},
            {'subject': 'Re: [PATCH v2 1/7] sched: foo', 'author': 'Bob'},
        ]
        result = group_series(entries)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['base_subject'], 'sched: foo')
        self.assertEqual(len(result[0]['versions']), 2)

    def test_multiple_versions_sorted(self):
        """Versions should be sorted by version number."""
        entries = [
            {'subject': '[PATCH v3] sched: foo', 'author': 'Alice'},
            {'subject': '[PATCH v1] sched: foo', 'author': 'Alice'},
            {'subject': '[PATCH v2] sched: foo', 'author': 'Alice'},
        ]
        result = group_series(entries)
        versions = result[0]['versions']
        self.assertEqual(versions[0]['version'], 1)
        self.assertEqual(versions[1]['version'], 2)
        self.assertEqual(versions[2]['version'], 3)
        self.assertEqual(result[0]['current_version'], 3)

    def test_slug_generated(self):
        entries = [
            {'subject': '[PATCH] sched/fair: fix load balance', 'author': 'Alice'},
        ]
        result = group_series(entries)
        self.assertEqual(result[0]['slug'], 'sched-fair-fix-load-balance')

    def test_result_sorted_by_base_subject(self):
        entries = [
            {'subject': '[PATCH] zzz: last', 'author': 'Alice'},
            {'subject': '[PATCH] aaa: first', 'author': 'Bob'},
        ]
        result = group_series(entries)
        self.assertEqual(result[0]['base_subject'], 'aaa: first')
        self.assertEqual(result[1]['base_subject'], 'zzz: last')

    def test_empty_entries(self):
        result = group_series([])
        self.assertEqual(result, [])

    def test_mixed_series(self):
        """Complex scenario: two patch series + tip-bot + reply."""
        entries = [
            {'subject': '[PATCH v1] sched: foo', 'author': 'Alice'},
            {'subject': '[PATCH v2 1/3] sched: foo', 'author': 'Alice'},
            {'subject': 'Re: [PATCH v2 1/3] sched: foo', 'author': 'Bob'},
            {'subject': '[tip: sched/urgent] sched: foo', 'author': 'tip-bot'},
            {'subject': '[PATCH] sched: bar', 'author': 'Charlie'},
        ]
        result = group_series(entries)
        self.assertEqual(len(result), 2)
        # Find the 'sched: foo' series
        foo_series = [s for s in result if s['base_subject'] == 'sched: foo'][0]
        self.assertTrue(foo_series['has_tip'])
        self.assertEqual(foo_series['current_version'], 2)
        # Should have v1, v2 patch + 1 reply = 3 versions
        self.assertEqual(len(foo_series['versions']), 3)


if __name__ == '__main__':
    unittest.main(verbosity=2)
