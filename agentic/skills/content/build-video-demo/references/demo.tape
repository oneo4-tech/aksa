# Records the terminal demo of {{folder}}. Run from this folder: vhs demo.tape
# The settings match the channel's screen capture rules; the Show part types the steps that prove the claim.
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
Type "setopt interactivecomments && alias pytest='uv run -q --with pytest python -m pytest -p no:cacheprovider' && export PS1='%F{green}{{prompt}}%f $ ' && clear" Enter
Show
Sleep 500ms
Type "# the claim, in one line" Enter
Sleep 800ms
Type "pytest -q tests" Sleep 300ms Enter
Sleep 4s
