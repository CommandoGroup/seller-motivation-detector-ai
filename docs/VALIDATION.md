# Validation

Test the changed seam and sibling checks that touch changed files. The existing `tests/browser/` reports describe earlier source checks, not the current production deployment.

Run the actual Flask app, then check its form and results at 1280 and 390 pixels, including the embedded member page. Verify keyboard focus, reduced motion, readable contrast and no horizontal overflow. Use the delivered members interface as the visual comparison.

Analyze a transcript and download its PDF. Upload audio and poll the returned job until its completed analysis appears. Repeated polls must never alternate between a valid result and 404.

Use actual UI actions so requests come from the tool's own JavaScript. For exports, require a successful response whose bytes start with `%PDF-` and open the PDF. Never substitute source-string assertions for executed behavior.

For styling changes, remove the actual `tool.css` link, require the focused browser presentation assertion to exit nonzero, then restore the source byte-identically. Keep positive and negative evidence bound to the source SHA.

## Shared audio status

Run `python tools/proof_jobs.py report.json`. It executes the real background sender and Flask receiver with only the AI provider boundary substituted, cross-process reads, partial updates and retention cleanup. Its isolated process-storage negative must exit 1, then restore `job_queue.py` byte-identically. Keep the JSON result with release evidence. The test makes no paid provider request. A live upload still needs a real audio-to-result round trip.
