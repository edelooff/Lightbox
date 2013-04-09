/*jslint indent: 2, plusplus: true */

// Wrap all of this in a self-executing anonymous function. This prevents any
// scope bleeding, but also means that our "use strict" doesn't affect code
// outside this source file.
(function() {
  "use strict";

  $(document).ready(function() {
    $.getJSON('/api', function(data) {
      document.lightbox = new Lightbox(data);
    });
  });

  function Lightbox(controller) {
    this.node = $('#preview');
    this.outputTemplate = $('.output').detach();
    this.outputs = [];
    this.createOutputs(controller.outputCount);
    this.update();
    setInterval(this.update.bind(this), 150);
  }

  Lightbox.prototype.createOutputs = function(count) {
    var index, output;
    for (index = 0; index < count; index++) {
      output = new Output(index, this.outputTemplate);
      this.outputs.push(output);
      this.node.append(output.node);
    }
  };

  Lightbox.prototype.update = function () {
    $.getJSON('/api/outputs', this.updateOutputs.bind(this));
  };

  Lightbox.prototype.updateOutputs = function(info) {
    var index;
    for (index = 0; index < info.length; index++) {
      this.outputs[index].update(info[index]);
    }
  };

  function Output(index, template, layerCount) {
    this.index = index;
    this.node = template.clone();
    this.node.find('strong').text('Output ' + index + 1);
    this.layerContainer = this.node.find('.layers');
    this.layerTemplate = this.node.find('.layer').detach();
    this.layers = [];
    this.createLayers(layerCount || 3);
  }

  Output.prototype.createLayers = function(count) {
    var layer;
    while (count--) {
      layer = new Layer(this.layerTemplate, this);
      this.layers.splice(0, 0, layer);  // Insert at the beginning
      this.layerContainer.append(layer.node);
    }
  };

  Output.prototype.update = function(info) {
    this.node.find('.mixed').css('background-color', info.mixedColorHex);
    var i;
    for (i = 0; i < info.layerCount; i++) {
      this.layers[i].update(info.layers[i]);
    }
  };

  function Layer(template, output) {
    this.node = template.clone();
    this.output = output;
    // Layer color and opacity settings
    this.color = '#000';
    this.opacity = 1;
    this.blender = '';
    this.envelope = '';
    // Placed defaults, render this layer
    this.renderLayer();
  }

  Layer.prototype.renderLayer = function() {
    this.node.find('.color').css('background-color', this.color);
    this.node.find('.opacity').text(Math.round(this.opacity * 100));
    this.node.find('.blender').text(this.blender);
    this.node.find('.envelope').text(this.envelope);
  };

  Layer.prototype.update = function(info) {
    this.color = info.colorHex;
    this.opacity = info.opacity;
    this.blender = info.blender;
    this.envelope = info.envelope;
    this.renderLayer();
  };
}());
