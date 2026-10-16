import unittest
import base64
import io
from ingestion import detect_events, review_document, validate_observations


class IngestionTests(unittest.TestCase):
    def test_transaction_types_stay_distinct(self):
        text = 'Bank A amalgamation effective 1 April 2019. Loan book purchase approved. NBFC acquisition of control. Demerger. Capital raise.'
        kinds = {e['type'] for e in detect_events(text)}
        self.assertEqual(kinds, {'amalgamation', 'loan_book_purchase', 'acquisition', 'demerger', 'capital_raise'})

    def test_extracted_numbers_never_auto_approved(self):
        out = review_document(dict(text='Gross NPA 100 crore at 31 March 2020', unit='INR crore', period='2020-03-31', entity='Bank A', source_url='https://example.org/report'))
        self.assertEqual(out['status'], 'needs_review')
        self.assertFalse(out['validation']['eligible_for_analysis'])
        self.assertTrue(out['numbers'])

    def test_required_source_and_reconciliation_checks(self):
        row = dict(id='a', entity='A', period='2020-03-31', metric='gnpa', value=2, unit='INR crore', basis='standalone', sourceId='s', locator='page 3', reviewed=True)
        source = dict(id='s', url='https://example.org', publishedDate='2020-05-01', extractionMethod='manual', retrievedAt='2026-10-16')
        checks = dict(unit=True, period=True, subtotal=True, source_reconciliation=True)
        self.assertEqual(validate_observations([row], [source], checks), [])
        self.assertTrue(validate_observations([dict(row, value=float('nan'))], [source], checks))
        self.assertTrue(validate_observations([dict(row, reviewed=False)], [source], checks))
        self.assertTrue(validate_observations([row], [source], dict(checks, subtotal=False)))
        self.assertTrue(validate_observations([dict(row, sourceId='missing')], [source], checks))

    def test_incompatible_or_duplicate_rows_fail(self):
        self.assertTrue(validate_observations([dict(id='a')], [], {}))

    def test_pdf_requires_real_pdf(self):
        with self.assertRaises(ValueError):
            review_document(dict(file_name='sample.pdf', file_base64='bm90IHBkZg=='))

    def test_source_link_rejects_script_url(self):
        with self.assertRaises(ValueError):
            review_document(dict(text='hello', source_url='javascript:alert(1)'))

    def test_optional_pdf_review_retains_human_gate(self):
        try:
            from pypdf import PdfWriter
        except ImportError:
            self.skipTest('Optional pypdf is not installed')
        writer=PdfWriter()
        writer.add_blank_page(width=300,height=300)
        buffer=io.BytesIO()
        writer.write(buffer)
        result=review_document(dict(file_name='blank.pdf',file_base64=base64.b64encode(buffer.getvalue()).decode()))
        self.assertEqual(result['pages'],1)
        self.assertFalse(result['validation']['eligible_for_analysis'])


if __name__ == '__main__':
    unittest.main()
