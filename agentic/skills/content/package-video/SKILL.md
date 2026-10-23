---
name: package-video
description: Use at a video's packaging stage, from youtube-producer, when the owner asks to write or redo a video's title, description, chapters, or tags, or once a video is published to record its link. Writes videos/<n>/packaging.json and description.md (a challenge title within title_max, a short description with the hook, chapters from the rendered scenes, the demo link, the verified sources, the synthetic-voice and paid-promotion disclosure, and up to three hashtags, plus 5-8 tags), refused naming each problem; with the published link, fills the demo README's video line locally.
---

# Package video

## Inputs and prerequisites

- The channel and `#<n>`, a content issue at stage `packaging` (from `youtube-producer`), or any later stage to record the published link. No channel or issue: ask the owner which.
- Written below: `C` for `uv run agentic/scripts/content_issue.py`, `P` for `uv run agentic/skills/content/package-video/scripts/package.py`, and `W` for the workspace `.projects/content/yt-<channel>/`.
- The channel workspace, checked with `uv run agentic/scripts/youtube_channel.py check <channel>`; exit 2: show its message and stop. Read the style guide sections `Metadata` (title, description, tags, hashtags, and disclosure rules) and `Writing rules`, and for a Short `Shorts`, and in `channel.yaml` the `title_max` and `banned_phrases` that `P` applies.
- The video's outputs in `W/videos/<n>/`: `script.json` (`write-video-script`), `render/scenes.json` (`render-video`), `demo.json` with its `link` (`build-video-demo`), and `citations.json`, every claim verified (`research-video`). Missing: stop and route the video back to the stage that writes it.
- For a Short, its long-form: `C status <n> --channel <channel>` gives `long_form`; `P` needs that video's `W/videos/<long_form>/packaging.json` with its `video_url`, so the long-form is packaged and published first.

## Procedure

1. **Check the stage:** `C status <n> --channel <channel>` must show stage `packaging`, with its `type`; else stop and report the stage. Recording the published link (step 6) works at any later stage.
2. **Write `W/videos/<n>/metadata.json`** under `Metadata` and `Writing rules`:
   - `title`: challenge style, such as "Spot the Bug: This AI Test Passes and Tests Nothing", at most `title_max` characters, answering the script's promise; start from `script.json` `title`.
   - `hook`: the description's first line, one sentence saying the problem the video shows.
   - `chapters`: for a long-form, a list of `{scene, title}` marking where each part starts: the first is scene 1, at least three, in scene order, each at least ten seconds long (`render/scenes.json` `frames` over `fps`); titles of a few plain words. For a Short, an empty list.
   - `tags`: five to eight: the topic, the tools, the pillar.
   - `hashtags`: up to three, each `#` and one word; YouTube shows them above the title.
   - `paid_promotion`: `null`, or the sponsor sentence when the video has one, such as "Example Tools sponsors this video".
   - For a Short, `related`: the `long_form` number from `C status`.
3. **Package:** `P <channel> <n>`. It builds the description: the hook, the chapters (a Short gets `Full video: <long-form link>` instead), `Code: <demo link>`, `Sources:` with each claim and its text-fragment link, the disclosure lines (`Narration uses a synthetic AI voice.`, then `Includes paid promotion: <sentence>.` or `No paid promotion.`), and the hashtags. It writes `W/videos/<n>/description.md` and `packaging.json`.
   - Exit 3: fix each problem it names in `metadata.json` and run `P` again; chapters a scene's length cannot meet: merge them into one; a Short whose long-form has no `video_url`: report blocked until the long-form is published. Missing demo link or citations: route the video back to `build-video-demo` or `research-video`. Exit 2: fix the file it names.
4. **Check the result** against `Metadata`: read `description.md` as a viewer would; the title, hook, and chapter titles match what the video shows, with no claim the sources do not back.
5. **Report on the issue:** write a scratch file of the line `YouTube: packaging`, then the title, the description, the tags, and the disclosure, and post it with `gh issue comment <n> --body-file <file>`. Remind the owner that in YouTube Studio the paid-promotion box is ticked when `paid_promotion` is true, and for a Short, the related video is set to the long-form. Return to the producer with `packaging.json`'s path.
6. **Record the published link,** when the owner gives the video's YouTube link after publishing: `P <channel> <n> --video-url <link>`. It records `video_url` in `packaging.json` and, when `demo.json`'s folder is this video's, fills that README's `- Video:` line in the local demo clone and rebuilds its Sources section from `citations.json`. Commit it in the clone as `build-video-demo` step 8 does: `git -C <clone> commit -am "docs(<folder>): link the video"`, then ask the owner's explicit yes to push. Exit 2: the link is not a YouTube video link; ask the owner for it again.

## Output

The `YouTube: packaging` comment's link, `packaging.json`'s path, the title, and the tag and chapter counts; after step 6, the recorded link and the README filled, and whether it is pushed. A refusal is reported with `P`'s problems; a Short waiting for its long-form's link, a missing output, or no yes to push is reported as blocked.

## Constraints

- Uploads, publishes, and schedules nothing on YouTube, and sets nothing in Studio; the owner pastes `packaging.json` values and sets the paid-promotion box and a Short's related video. Never pushes the demo repository without the owner's explicit yes in this session.
- Never writes a link to the private aksa tracker into the description or the demo README.
- Never edits `script.json`, `citations.json`, `demo.json`, `channel.yaml`, or the style guide; a claim the sources do not back goes back to `research-video`. `scripts/package.py` is a component: changes to it are new work requests (D-038).
- Never passes a gate, moves a stage, or edits labels or the body; `C` and `youtube-producer` own those (D-042). Never commits workspace or demo files to aksa.

## Done when

- `P <channel> <n>` exited 0: `W/videos/<n>/packaging.json` and `description.md` exist, and the description was read against `Metadata`.
- The `YouTube: packaging` comment is on the issue, with no placeholder and no em dash.
- After a published link: `packaging.json` holds it, the demo README's `- Video:` line shows it when the folder is this video's, and nothing was pushed without the owner's yes.
