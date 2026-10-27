# Starting your job search

You can begin while still deciding whether to move. The app is a local personal workspace; it does not require an existing resume to save a role.

## First session

1. Open `/dashboard#today` for follow-ups, pipeline counts, and quick actions. Choose **Search** and use **I'm exploring a job change**. Write role titles, location or remote preference, and what you want to improve. Save stores these direction notes on the local server. Previously stored browser notes are used as a fallback until you save them.
2. Use **Find live opportunities** to search selected supported company boards and save postings directly. See [live discovery](JOB_DISCOVERY.md) for source setup and coverage. External LinkedIn/Indeed links remain available for a broader search; the app does not import those search results or submit applications.
3. Read a few descriptions. Notice recurring responsibilities, qualifications, language, location, and work arrangements. In **Tracker**, save an interesting opportunity using its title, company, and link. Paste the job description so it is available later. No resume is required.
4. Record why it interests you in Notes and fill **My next action** with a specific step. Set a follow-up date if useful. Saved roles and notes are stored in PostgreSQL. Filter the tracker by status or search title, company, and notes.

## When ready to prepare a resume

Download the plain-text resume starter from the comparison panel. Fill it with your actual work and projects in a document editor, then export a text-based PDF. Upload it once and reuse it for other comparisons. Upload a new version after edits.

Paste a job description and compare. The current extractor supports a limited software/AI skill dictionary and English text processing. Other requirements still need your own review. The tracker can be used for any role.

The tailoring section quotes existing resume text and gives prompts for improving relevance. Fill the suggested bullet structure with facts; it is not a generated replacement resume. A missing skill means it was not recognized in the text, not proof you lack it. Select **Keep this comparison in my tracker** to save it with a role. From a saved role, use **Compare this saved description with my resume**, then save again to attach the new comparison.

## Apply and follow up

Open the posting link and apply through the employer or job board yourself. Change the saved role to Applied and record what you submitted. Later use Interview, Offer, or Closed. Today shows follow-ups due today or earlier and upcoming dates for active roles. Offer and Closed roles are excluded from reminder tasks. Dates use the browser's local calendar; there are no email notifications or background reminders.

To update a saved role, select **Review / update this role**. To create a separate opportunity, select **Start a new role / clear this form**. If an existing role is selected, a new comparison can be attached when you save it.

The page ignores old responses after you switch roles. A failed comparison keeps the previous saved comparison association. Role saves also carry a version token: if another tab saved a newer version, your stale save is rejected instead of replacing it. Your current text remains in the form; preserve any notes you want to merge, reopen the current saved version, then apply your changes deliberately. Legacy API clients that omit the version token do not receive this early stale-form check.

## Keep the full opportunity history

After saving or opening a role, use **Opportunity history** in Tracker. Add recruiter contacts, email summaries, preparation notes, tasks, and interviews. Scheduled items use the local time you enter, are stored with a timezone, and appear on Today for the next seven days plus incomplete overdue items. Mark completed tasks or interviews to remove them from the action list. Status changes are recorded automatically.

Attach the exact resume or cover letter you submitted, interview notes, calendar files, or exported correspondence. Files are limited to 10 MB each and download as attachments; no application is sent by this action. A timeline email summary is entered manually and is separate from Gmail authorization.

Use Accounts to create a private backup of your data and uploaded files. See [backup and recovery](BACKUP_AND_RECOVERY.md) for restoration and verification details.

## Ask for help preparing a saved opportunity

Open a role in Tracker and select **Review this opportunity** in its history panel. Choose a CV version if needed. The default is the CV used by the saved comparison, or your personal CV when configured. Save posting edits before reviewing.

The review quotes recognized skill evidence from your CV, lists skills not found in it, surfaces excerpts about language/location/qualifications/authorization/compensation, and suggests next steps for the role's current status. It does not decide whether you qualify. The requirement checks are keyword-based and may miss or misinterpret context; read the full posting yourself.

You can fill a suggested next action into the role form, then save it. Interview prompts and an editable email template can be saved to the timeline for preparation. No email is sent. Fill placeholders, verify claims, and edit drafts before using them elsewhere. This helper uses deterministic rules and templates rather than an external LLM.

With Gmail authorized, Accounts can show message headers from your search. Choose the relevant saved role and explicitly save a reference. Repeated saves of the same message to the same role are deduplicated. The reference contains subject, sender, date, and a Gmail link, not the message body. Saving an email never changes application status automatically.

## Storage and setup

After pulling these changes, run the additive local database initialization once:

```powershell
.\.venv\Scripts\python.exe scripts/run.py
```

Open http://127.0.0.1:8000/dashboard#today. The launcher applies additive local schema updates and starts the API. Stop any already running instance first, or add `--port 8001`. Uploaded files, extracted text, application notes, tracker data, and saved direction notes remain on this server. There is no authentication, deletion UI, cloud backup, or multi-user isolation; keep this personal workspace local. No applications or employer messages are sent by the app.
