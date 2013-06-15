# Lightbox

Lightbox is a Python library that controls hardware to drive LED-strips. It was originally written for the [Twitterboom](http://twitterboom.nl) project at [Frack](http://frack.nl/wiki), and has since seen continued development. All color transitions are performed in LAB color space, ensuring that there are no dips or peaks in perceived lightness during a transition.

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

## JSON API Documentation

There is a basic JSON API available for Lightbox. This can be started using the `api_server.py` script in the main repo directory. The controller used can be chosen with the `--controller` option (this defaults to `JTagController`), as well as the port that the http server binds to (`--port`, default 8000).

### Controller information

Information about the controller and commands that can be sent. The name for the controller is present under the key `controller`, the number of outputs is given as an integer under the key `outputs`. Command rates are specified on the key `commandRate`, this object has entries for both the `combined` and `perOutput` rates.

The number of outputs is provided in the `outputCount` key, the number of layers on each output is provided by the `layerCount` key.

The physical device information is provided, the `type` of this is always provided, other keys for this are present dependant on the type of the attached hardware.

For transitions, the action, layer blending method, and transition envelope can be configured. The available values for these can be gathered from the API output. The keys `layerBlenders`, `outputActions` and `transitionEnvelopes` have the information for this.

The controller information can be retrieved from `/api`.

```json
{
    "commandRate": {
        "combined": 200,
        "perOutput": 40
    },
    "controller": "JTagController",
    "device": {
        "baudrate": 57600,
        "port": "/dev/ttyUSB1"
        "type": "serial",
    },
    "layerBlenders": [
        "Darken",
        "Lighten",
        "LabAverage",
        "RgbAverage",
        "RootSumSquare"
    ],
    "layerCount": 3,
    "outputActions": [
        "Blink",
        "Constant",
        "Fade"
    ],
    "outputCount": 5,
    "transitionEnvelopes": [
        "CosineEnvelope",
        "LinearEnvelope"
    ]
}
```

### Output information

The current color information for each of the outputs can be requested. This will return an array of all outputs on the controller. For each of the outputs the following information will be provided:

* `layers`: Detailed information for each of the layers in this output, looks like this:
 * `colorHex`: Current color of the layer as hex string
 * `colorRgb`: As above, but as array of red, green and blue intensity (0-255)
 * `opacity`: Opacity of the layer, the fraction with which it blends over the layer under it
 * `blender`: Blend function that is used
 * `envelope`: Transition envelope function; Determines how the color/opacity transition eases in
* `mixedColorHex`: Resulting color after blending all layers, as hex string
* `mixedColorRgb`: As above, but as array of red, green and blue intensity (0-255)
* `outputNumber`: The output index (0-based)

Output information can be retrieved from `/api/outputs` and would look like this for a single output with three layers:

```json
[
  {
    "layers": [
      {
        "colorHex": "#6acfe3",
        "colorRgb": [106, 207, 227],
        "opacity": 1,
        "blender": "LabAverage",
        "envelope": "CosineEnvelope"
      },
      {
        "colorHex": "#000000",
        "colorRgb": [0, 0, 0],
        "opacity": 0,
        "blender": "LabAverage",
        "envelope": "CosineEnvelope"
      },
      {
        "colorHex": "#000000",
        "colorRgb": [0, 0, 0],
        "opacity": 0,
        "blender": "LabAverage",
        "envelope": "CosineEnvelope"
      }
    ],
    "mixedColorHex": "#6acfe3",
    "mixedColorRgb": [106, 207, 227],
    "outputNumber": 0
  }
]
```

### Sending commands

Send commands to `/api` using HTTP POST. The body of the request should be valid JSON and the `content-type` should be `application/json`.

The body should describe either a single transition, or a list of transitions. Each transition should indicate an `output` and a `layer` and typically describes a target `color` or `opacity`. The number of `steps` will determine how fast a transition occurs. The default number of steps is 1, causing an immediate transition.

Transitions are queued at the layer level, so sending multiple transitions for different layers or different outputs will cause the transitions to happen simultaneously. Sending multiple transitions for the same layer on the same output will cause them to be queued and performed in sequence.

Example to set the second output to teal:

```json
{
    "output": 1,
    "color": [0, 200, 200],
    "steps": 40
}
```

#### `output`

An integer to select the output for the transition. If none is provided, this defaults to the first output (`0`).

#### `layer`

An integer to select the layer for the transition. Layers are stacked on top of each other, with zero being the bottom layer. Additional layers are added on top of this and the resulting mixed color is based on the opacity and blend function. This defaults to the bottom layer (`0`).

#### `color`

An array of 3 integers (0-255) or a hex color string. This is the target color for the transition. Both the colo and the lightness will smoothly over the course of the transition. If the `color` argument is not provided, the color of the layer will remain the same.

#### `opacity`

A number (`float` or `int`) that should be the opacity at the end of the transition. The opacity change is performed smoothly over the course of the transition. If the `opacity` argument is not provided, the opacity of the layer will remain the same.

#### `steps`

This specifies the number of steps in which the transition will take place. The actual duration of the transition cannot be specified, but the per-output command rate can be gotten from the controller information API. Using this, animations can be carefully timed. If no `steps` argument is provided, the transition will occur in a single step.

#### `action`

The type of transition that should be performed. A list of actions can be retrieved using the controller information API.

* The default action is `Fade`, which fades from the current color and opacity to the given.
* The second action is `Blink` which causes a fade towards the given color and opacity, and then back to the original color and opacity. The steps argument is used as the number of steps for each fade in the action. A complete blink with `steps=10` takes 20 steps in total.
* A third action `Constant` immediately changes the color and opacity to the given values, the number of steps then indicates the minimum amount of time that the layer stays like that.

##### `count`

For `Blink` actions, this sets the number of blinks, defaulting to one. When the number of blinks is increased with the same number of steps, the transition will take longer. A `Blink` transition with `steps=10` and `count=3` will take 60 steps (10 * 3 * 2).

#### `envelope`

Selects an envelope function to use for the transition. These are also known as "easings", and a list of available options can be gotten from the controller information API. When not provided, the last selected transition for the layer is used, the initial envelope function is `CosineEnvelope`.

#### `blender`

Selects a blender function with which to blend this layer over the one below it. The opacity of the layer determines how much this layer affects the one below it. A list of available blend functions can be gotten from the controller information API.

**N.B.**: Changing blenders should generally not be done at opacities above zero, as they will result in immediate blended color changes. The exception here are the `average` blend methods, which can be changed between at full opacity without sudden shifts.

When not provided, the blend function remains the same, and the initial blender is `LabAverage`.
