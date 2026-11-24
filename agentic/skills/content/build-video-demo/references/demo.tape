# Records the terminal demo of {{folder}}. Run from this folder: vhs demo.tape
# The settings match the channel's screen capture rules; the Show part types the steps that prove the claim.
# Each "# scene" line starts one terminal scene's steps: record.py records each section alone, after the setup.
# Each step is a "# comment" line, its command, and its output, read as a group: the setup's zshaddhistory
# records whether the last line was a comment (preexec skips comment-only lines), and precmd prints one blank
# line before the next prompt unless it was, so a blank line comes before each comment, none after it.
# A step that changes the code (a mutation) prints the line before and after the change, then runs the tests.
Output demo.mp4
Set Shell zsh
Set FontFamily "Menlo"
Set FontSize 30
Set Width 1920
Set Height 1080
Set Padding 48
Set Theme "Dracula"
Set TypingSpeed 45ms
Set WindowBar Colorful

Hide
Type "setopt interactivecomments && alias pytest='uv run -q --with pytest python -m pytest -p no:cacheprovider' && export PS1='%F{green}{{prompt}}%f $ ' && c=1 && zshaddhistory() { [[ $1 == '#'* ]] && c=1 || c=0; } && precmd() { (( c )) || echo; } && clear" Enter
Show
Sleep 500ms
# scene
Type "# the claim, in one line" Enter
Sleep 800ms
Type "pytest -q tests" Sleep 300ms Enter
Sleep 4s
