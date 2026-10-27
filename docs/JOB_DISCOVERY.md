# Live opportunity discovery

Search → Find live opportunities reads published postings from selected public company boards. Supported providers are Lever's global Postings API and Greenhouse's Job Board API. No job-board credentials are needed, and your CV is not sent to these services.

The initial Woven by Toyota source is an example verified against a public feed, not an employer recommendation or an assessment of your suitability. Manage sources to choose companies you actually want to explore. Sources are stored in the local database and included in workspace backups.

## Search

1. Open Manage company job boards to add a provider, board slug (or supported public board URL), and company name. Up to five sources are allowed. Adding a source saves its configuration; a search verifies whether it responds.
2. Enter keyword alternatives separated by commas. All words in an alternative must appear somewhere in the title or description. For example, `computer vision, machine learning, perception` matches any of those three groups. Short terms such as AI and ML use word boundaries.
3. Optionally filter location/work style by a literal substring such as `Tokyo` or `remote`. This is not a geographic or commute-radius search. A long preference such as “Tokyo, Japan or remote” should be simplified for this filter.
4. Search the selected company boards. Results are sorted by company and title, not by estimated fit. The view shows source failures and source limits separately; no results is not evidence that no suitable jobs exist elsewhere.
5. Read the original posting and preview its text. Select Save opportunity to import its title, company, URL, description, and source reference into Tracker. The app rechecks the source at save time. Applying still happens through the employer.

Each search checks at most 500 postings per source and shows up to 50 matching results. Narrow keywords or location if the result limit is reached. Greenhouse returns its board as one response; the local connector uses the first 500 entries if a board exceeds that limit. Only supported public API hosts are requested; arbitrary URLs and LinkedIn scraping are not supported. Lever EU boards are not supported in this version.

## Saved postings

The full imported description is limited to 50,000 characters. It is a snapshot, not a live contract or guarantee that a role is still open. Verify the original before applying. Re-saving a source posting returns the existing role without overwriting your notes, status, or description. If the original URL was already captured manually, the existing role is linked to the source without replacing your work. Automatic refresh of saved descriptions is not implemented.

Your company label is entered in source settings; the API does not independently verify that display label. The posting link and provider/board identifiers retain provenance. Source errors should be resolved by checking the company's current careers page and supported board slug.

## Verification

Tests cover provider paging and normalization, keyword/location filters, failed sources, source validation, closed postings, duplicate saves, and preservation of manual records. A live check of the Woven by Toyota Lever feed returned postings and matching Tokyo results. No live job was saved automatically to the user's tracker. Browser layout has not been visually verified.

Official references:

- Lever Postings API: https://github.com/lever/postings-api
- Greenhouse Job Board API: https://docs.greenhouse.io/job-board.html
- Example public board: https://jobs.lever.co/woven-by-toyota
