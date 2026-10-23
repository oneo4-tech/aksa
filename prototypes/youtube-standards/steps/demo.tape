# PROTOTYPE: scripted terminal demo. Run from prototypes/youtube-standards: vhs steps/demo.tape
Output out/capture/vhs.mp4
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
Type "cd ../youtube-tools/demo && setopt interactivecomments && alias pytest='uv run -q --with pytest pytest -p no:cacheprovider' && export PS1='%F{green}testlab%f $ ' && clear" Enter
Show
Sleep 500ms
Type "cat test_discount_ai.py | sed -n '7,11p'" Sleep 300ms Enter
Sleep 2.5s
Type "pytest -q test_discount_ai.py" Sleep 300ms Enter
Sleep 4s
Type "# now break the code: discount becomes markup" Enter
Sleep 800ms
Type "./mutate.sh" Sleep 300ms Enter
Sleep 6s
