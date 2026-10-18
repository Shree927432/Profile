---
title: GST invoice reconciliation for accountants
year: 2026
summary: Matches a client's books against the GST portal so a chartered accountant stops doing it by hand.
tags: [python, pandas, streamlit]
links:
  live: ""
  source: https://github.com/Shree927432/Reconcile_X
cover: ""
featured: true
order: 2
---

Every month a chartered accountant in India has to check that the invoices in a client's books match what suppliers reported to the GST portal. Invoice numbers are typed differently on each side, company names carry different suffixes, amounts come with commas and rupee signs. The work is tedious and the mistakes are expensive. I know the accountants, so I built the tool.

The first version was a script with pandas: load both sheets, normalise the fields, report what is missing on each side, and write the reminder message to send the client. The second, ReconcileX, is a small web app. Upload the Tally export and the GSTR-2B export, and it blocks candidate pairs, scores them on invoice number, supplier name, GSTIN and amount, and sorts the matches into perfect, strong and probable, with a spreadsheet to download.

What I learned: the cleaning is the product. Most of the code is about what a human types into an invoice-number field. It was also my first real lesson in dependency hell, which now lives as a monkey patch at the top of the file, with a comment.
