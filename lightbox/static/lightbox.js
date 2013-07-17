/*jslint indent: 2, plusplus: true */

// Wrap all of this in a self-executing anonymous function. This prevents any
// scope bleeding, but also means that our "use strict" doesn't affect code
// outside this source file.
(function() {
  "use strict";
  var lightbox, picker;

  $(document).ready(function() {
    lightbox = new Lightbox('#preview');
    lightbox.init();
    lightbox.automaticUpdates(150);
    picker = $('#picker_popup').detach();
  });

  function Lightbox(node) {
    this.node = $(node);
    this.apiController = '/api';
    this.apiCommand = '/api';
    this.apiOutputs = '/api/outputs';
    this.controllerInfo = undefined;
    this.outputTemplate = $('.output').detach();
    this.outputs = [];
  }

  Lightbox.prototype.automaticUpdates = function(interval) {
    this.update();
    setInterval(this.update.bind(this), interval);
  };

  Lightbox.prototype.init = function() {
    $.getJSON(this.apiCommand, this.createOutputs.bind(this));
  };

  Lightbox.prototype.createOutputs = function(apiInfo) {
    this.controllerInfo = apiInfo;
    var index, output, outputNode;
    for (index = 0; index < apiInfo.outputCount; index++) {
      outputNode = this.outputTemplate.clone();
      output = new Output(index, outputNode, apiInfo);
      this.outputs.push(output);
      this.node.append(output.node);
    }
    var blenders = picker.find('#blender');
    blenders.empty();
    $.each(lightbox.controllerInfo.layerBlenders, function(_, blender) {
      blenders.append($('<option>', {"value": blender}).text(blender));
    });
    var envelopes = picker.find('#envelope');
    envelopes.empty();
    $.each(lightbox.controllerInfo.transitionEnvelopes, function(_, envelope) {
      envelopes.append(
          $('<option>', {"value": envelope}).text(envelope));
    });
  };

  Lightbox.prototype.update = function() {
    $.getJSON(this.apiOutputs, this.updateOutputs.bind(this));
  };

  Lightbox.prototype.updateOutputs = function(info) {
    var index;
    for (index = 0; index < info.length; index++) {
      this.outputs[index].update(info[index]);
    }
  };

  function Output(index, node, apiInfo) {
    this.index = index;
    this.node = node;
    this.layerNodes = node.find('.layers');
    this.layerTemplate = node.find('.layer').detach();
    this.layers = [];
    this.setTitle('Output ' + (index + 1));
    this.addLayers(apiInfo.layerCount);
  }

  Output.prototype.addLayer = function(index) {
    var layer = new Layer(index, this.layerTemplate.clone(), this);
    this.layers.splice(0, 0, layer);  // Insert at the beginning
    this.layerNodes.append(layer.node);
  };

  Output.prototype.addLayers = function(count) {
    // Creates a number of layers for the output.
    while (count--) {
      this.addLayer(count);
    }
  };

  Output.prototype.setTitle = function(title) {
    // Sets the title that is displayed on the output node.
    this.node.find('h3').text(title);
  };

  Output.prototype.update = function(info) {
    this.node.find('.mixed').css('background-color', info.mixedColorHex);
    var i;
    for (i = 0; i < info.layers.length; i++) {
      this.layers[i].update(info.layers[i]);
    }
  };

  function Layer(index, node, output) {
    this.index = index;
    this.node = node;
    this.node.on('click', this.colorPicker.bind(this));
    this.output = output;
    // Default layer color and opacity values
    this.color = '#000';
    this.opacity = 1;
    this.blender = '';
    this.envelope = '';
    // Placed defaults, render this layer
    this.render();
  }

  Layer.prototype.colorPicker = function(event) {
    new LayerColorPicker(this);
    event.preventDefault();
  };

  Layer.prototype.render = function() {
    this.node.find('.color').css('background-color', this.color);
    this.node.find('.color').css('opacity', this.opacity);
    this.node.find('.opacity').text(Math.round(this.opacity * 100) + '%');
    this.node.find('.blender').text(this.blender);
    this.node.find('.envelope').text(this.envelope);
  };

  Layer.prototype.update = function(layerData) {
    this.color = layerData.colorHex;
    this.opacity = layerData.opacity;
    this.blender = layerData.blender;
    this.envelope = layerData.envelope;
    this.render();
  };

  function LayerColorPicker(layer) {
    this.layer = layer;
    // Color and other variables controlled by the user
    this.color = this.layer.color;
    this.opacity = this.layer.opacity;
    this.steps = 40;
    this.blender = this.layer.blender;
    this.envelope = this.layer.envelope;
    this.updateImmediate = false;
    this.updateQueued = false;
    // Initialize color picker
    this.node = this.createWindow(picker);
    this.picker = new ColorPicker($('#picker')[0], this.newColor.bind(this));
    // Command rate management
    this.setUpdateThrottler();
  }

  LayerColorPicker.prototype.createWindow = function(node) {
    var opacityPercents = Math.round(this.opacity * 100);
    node.appendTo('body');
    node.find('#opacityValue').text(opacityPercents);
    node.find('#opacitySlider').slider({
      range: 'min',
      max: 100,
      value: opacityPercents,
      slide: this.newOpacity.bind(this),
      change: this.newOpacity.bind(this),
    });
    node.find('#stepsValue').text(40);
    node.find('#stepsSlider').slider({
      range: 'min',
      min: 1,
      max: 200,
      value: 40,
      slide: this.newSteps.bind(this),
      change: this.newSteps.bind(this),
    });
    node.find('#blender')
        .val(this.blender)
        .off('change')
        .on('change', this.newBlender.bind(this));
    node.find('#envelope')
        .val(this.envelope)
        .off('change')
        .on('change', this.newEnvelope.bind(this));
    node.find('#updateImmediate')
        .off('change')
        .on('change', this.setImmediate.bind(this));
    node.find('#updateQueued')
        .off('change')
        .on('change', this.setQueued.bind(this));
    node.find('.submit')
        .off('click')
        .on('click', this.submit.bind(this));
    node.lightbox_me({
      centered: true,
      destroyOnClose: true,
      onLoad: this.updatePicker.bind(this)
    });
    return node;
  };

  LayerColorPicker.prototype.updatePicker = function() {
    this.picker.setHex(this.color);
    this.updateImmediate = this.node.find('#updateImmediate').is(':checked');
    this.updateQueued = this.node.find('#updateQueued').is(':checked');
  };

  LayerColorPicker.prototype.newColor = function(hex) {
    this.color = hex;
    this.node.find('.preview .color').css('background-color', hex);
    this.node.find('.preview .opacity').css('opacity', this.opacity);
    if (this.updateImmediate) {
      this.updateThrottler(this.currentCommand());
    }
  };

  LayerColorPicker.prototype.newOpacity = function(event, ui) {
    this.opacity = ui.value / 100;
    this.node.find('#opacityValue').text(ui.value);
    this.node.find('.preview .opacity').css('opacity', this.opacity);
    if (this.updateImmediate) {
      this.updateThrottler(this.currentCommand());
    }
  };

  LayerColorPicker.prototype.newBlender = function(event) {
    this.blender = event.target.value;
  };

  LayerColorPicker.prototype.newEnvelope = function(event) {
    this.envelope = event.target.value;
  };

  LayerColorPicker.prototype.newSteps = function(event, ui) {
    this.steps = ui.value;
    this.node.find('#stepsValue').text(this.steps);
    this.setUpdateThrottler();
  };

  LayerColorPicker.prototype.currentCommand = function() {
    return {
      color: this.color,
      opacity: this.opacity,
      steps: this.steps,
      queue: this.updateQueued,
      blender: this.blender,
      envelope: this.envelope,
    };
  };

  LayerColorPicker.prototype.setImmediate = function(event) {
    this.updateImmediate = event.target.checked;
  };

  LayerColorPicker.prototype.setQueued = function(event) {
    this.updateQueued = event.target.checked;
  };

  LayerColorPicker.prototype.setUpdateThrottler = function() {
    this.updateThrottler = $.throttle(
        1000 * this.steps / lightbox.controllerInfo.commandRate.perOutput,
        this.sendCommand.bind(this));
  };

  LayerColorPicker.prototype.sendCommand = function(command) {
    command.output = this.layer.output.index;
    command.layer = this.layer.index;
    $.ajax(lightbox.apiCommand, {
        data: JSON.stringify(command),
        contentType: 'application/json',
        type: 'POST'
      });
  };

  LayerColorPicker.prototype.submit = function() {
    this.sendCommand(this.currentCommand());
    this.node.trigger('close');
  };

}());
