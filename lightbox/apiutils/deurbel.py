from frack.libs.announce import transponder

for message in transponder.Receiver():
  message

# Door open: blink green and fade colours back in.

# Door closed: blink red and fade to black.
