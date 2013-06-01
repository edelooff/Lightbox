/*jslint indent: 2, plusplus: true */

// Wrap all of this in a self-executing anonymous function. This prevents any
// scope bleeding, but also means that our "use strict" doesn't affect code
// outside this source file.
(function() {
  "use strict";

  $(document).ready(function() {
    var lightbox = new Lightbox('#preview');
    lightbox.init();
    lightbox.automaticUpdates(150);
  });

  function Lightbox(node) {
    this.node = $(node);
    this.apiController = '/api';
    this.apiOutputs = '/api/outputs';
    this.outputTemplate = $('.output').detach();
    this.outputs = [];
  }

  Lightbox.prototype.automaticUpdates = function(interval) {
    this.update();
    setInterval(this.update.bind(this), interval);
  };

  Lightbox.prototype.init = function() {
    $.getJSON(this.apiController, this.createOutputs.bind(this));
  };

  Lightbox.prototype.createOutputs = function(controller) {
    var index, output;
    for (index = 0; index < controller.outputCount; index++) {
      output = new Output(index, this.outputTemplate.clone());
      output.addLayers(controller.layerCount);
      this.outputs.push(output);
      this.node.append(output.node);
    }
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

  function Output(index, node) {
    this.index = index;
    this.node = node;
    this.layerNodes = node.find('.layers');
    this.layerTemplate = node.find('.layer').detach();
    this.layers = [];
    this.setTitle('Output ' + (index + 1));
  }

  Output.prototype.addLayer = function() {
    var layer = new Layer(this.layerTemplate.clone(), this);
    this.layers.splice(0, 0, layer);  // Insert at the beginning
    this.layerNodes.append(layer.node);
  };

  Output.prototype.addLayers = function(count) {
    // Creates a number of layers for the output.
    while (count--) {
      this.addLayer();
    }
  };

  Output.prototype.setTitle = function(title) {
    // Sets the title that is displayed on the output node.
    this.node.find('strong').text(title);
  };

  Output.prototype.update = function(info) {
    this.node.find('.mixed').css('background-color', info.mixedColorHex);
    var i;
    for (i = 0; i < info.layers.length; i++) {
      this.layers[i].update(info.layers[i]);
    }
  };

  function Layer(node, output) {
    this.node = node;
    this.output = output;
    // Default layer color and opacity values
    this.color = '#000';
    this.opacity = 1;
    this.blender = '';
    this.envelope = '';
    // Placed defaults, render this layer
    this.render();
  }

  Layer.prototype.render = function() {
    this.node.find('.color').css('background-color', this.color);
    this.node.find('.opacity').text(Math.round(this.opacity * 100));
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
}());
