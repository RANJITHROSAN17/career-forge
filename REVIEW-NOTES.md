# Career Forge 1.0.3 — review fixes

## Implemented

1. Removed **Pin Scan Card** and **Ask Anna Coach**, their handlers, chat permissions and chat-handoff marketing. This takes the removal option offered in Anna's review.
2. Added real Anna LLM calls (`anna.llm.complete`) for XYZ/keyword-first rewrites, cover letters, recruiter outreach and five interview questions with STAR coaching guides. Results render inside the app. The manifest explicitly grants `llm.complete`.
3. Left ATS scoring, keyword matching and audits deterministic. A scan no longer renders template rewrites as if they were AI output.
4. Added in-app AI/privacy disclosure and updated marketplace/README descriptions. Cloud Agent processing is no longer described as necessarily on-device; AI writing is no longer advertised as offline or zero LLM cost.
5. Added structured-output validation, busy-state handling, visible LLM errors, HTML escaping and no silent template fallback. Prompts prohibit fabricated qualifications and metrics, but human review remains necessary.
6. Corrected the clipboard failure message so it no longer claims success on failure.

Custom saved roles (optional review suggestion) are not implemented. Existing presets and custom paste remain available. Python legacy writing endpoints remain for backward compatibility but the UI does not use them for writing generation.

## Local checks completed

- `npm ci && npm test`: **8 passed**. Includes a fresh jsdom UI with a mocked Anna host: initial preset scan, another preset, blank/custom resume + JD, scan, rewrites, cover/outreach, five interview questions, permission-denied error and recovery, escaped output, absence of both removed buttons.
- `python3 -m unittest discover -s tests -v`: **2 passed** (existing tests report subprocess-pipe ResourceWarnings).
- `node --input-type=module --check < bundle/app.js`: passed.
- `anna-app validate --strict`: passed with CLI 0.1.59 / app schema dispatcher 0.27.0.
- `git diff --check`: passed.

**These checks do not establish Cloud Agent compatibility or successful real model generation.** The SDK response/request shape was checked against the publicly served Anna SDK v0.21.0 and CLI mock implementation. No authenticated Anna session was available. No publish, push, or resubmission has occurred.

## Required before resubmitting — fresh Cloud Agent

- [ ] Publish a candidate build with app version 1.0.3 using your authenticated Anna CLI. Follow the existing binary preparation instructions; the Python engine version is unchanged.
- [ ] Install the candidate from scratch on a Cloud Agent, with empty app storage/state. Verify the bundled engine resolves to the published tool ID and starts.
- [ ] Confirm the new LLM permission is accepted and the app connects.
- [ ] Select each preset, run ATS Match Scan, inspect scores and keywords.
- [ ] Use Blank / Paste My Own with a different resume and JD; run the scan.
- [ ] Generate XYZ rewrites. Confirm actual Anna model output renders, claims match the resume and unknown metrics remain placeholders.
- [ ] Generate cover letter/outreach in modern, technical and executive tones. Confirm changing the inputs affects the generated output.
- [ ] Generate five interview questions and inspect STAR guides.
- [ ] Confirm neither removed chat button appears and no chat handoff is promised.
- [ ] Reject LLM access or simulate a model error; confirm a visible error, no success toast, and usable buttons afterwards.
- [ ] Reload and inspect draft restoration/history. Check desktop/mobile layout.
- [ ] Replace marketplace screenshots if they still show the removed controls or old claims.
- [ ] Record Agent/SDK versions, actual model, date and screenshots; only then resubmit.

## Suggested review response (send only after Cloud checks pass)

Hi Anna,

We addressed the review in Career Forge 1.0.3. We removed Pin Scan Card and Ask Anna Coach, their chat permissions and the chat-handoff descriptions.

ATS scoring, keyword radar, section checks and bullet audits remain deterministic Python. The writing buttons now call Anna's LLM via anna.llm.complete: XYZ/keyword-first bullet rewrites, cover letters, recruiter outreach, and five interview questions with STAR coaching guides. Current resume/JD, role, company and selected tone are supplied to the model. Validated results render directly in the corresponding app tabs; failures show an error rather than falling back to templates. The app and listing disclose this data flow and the need to review all AI drafts.

[Add the actual fresh Cloud Agent test date/results here before sending.]

Thanks!
