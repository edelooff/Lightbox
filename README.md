# Lightbox

Lightbox is a Python library that controls hardware to drive LED-strips. It was originally written for the Twitterboom (http://twitterboom.nl) project at Frack, and has since seen continued development. All color transitions are performed in LAB color space, ensuring that there are no dips or peaks in perceived lightness during a transition.

## Overview

At the heart of Lightbox is the _Controller_, which interfaces with the attached hardware box. For our existing solution, this is plain serial at 57600 baud. This controller object maintains a number of _Outputs_, abstractions of the physically connected strips. Each output can only assume one color; individually addressable strips are not the target for this library.

Each of these outputs contains a number of _Layers_. With these layers (and the different blend options  exist a number of layers. This allows more advanced setups where you have combined effects, for example:
* a basic color pattern at the lowest layer that changes slowly over time
* a darkening layer that responds to the audio volume in the room
* and an alarm signaling layer at the top for events like a doorbell or incoming email

Lastly, each layer accepts _Transition_ objects, which contain instructions on how the given layer should change appearance. The transition specifies the RGB color and opacity, but also the transition envelope. This is a simple function that determines the transition strength.

The default envelope here is a cosine, which has a slow start and end, giving a smooth looking transition. The other provided option is a linear envelope, which makes the start and end of a transition very visible.

As mentioned, all color transitions are performed in LAB colorspace. When a transition begint, the current color of the layer is converted to LAB space, as well as the target color. The differences for _l_, _a_ and _b_ are determined and using the given envelope, all the intermediate colors between start and finish are determined as they're written to the controller.

The benefit of this is that a transition from red to blue will not dip in lightness (such as with linear RGB color conversions), or have a noticeable peak in lightness (such as with linear HSV conversions), while remaining essentially a linear transition that can be calculated individually for each step.
