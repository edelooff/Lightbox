function createLightbox(controller) {
  var previewNode = $('#preview'),
      outputStruct = $('.output').detach();

  // Create a number ouf live view outputs corresponding to the hardware
  for(var index = 0; index < controller.outputCount; index++) {
    createOutput(outputStruct, previewNode, index);
  }
  // Update periodically
  setInterval(updateLightbox(), 150);
}

function createOutput(outputStruct, previewNode, outputIndex) {
  // Adds an output to the previewNode
  var outputNode = outputStruct.clone();
  outputNode.find('strong').text('Output ' + outputIndex);
  previewNode.append(outputNode);
}

function updateLightbox() {
  outputNodes = $('#preview .output');
  return function() {
    // Updates the complete live view with current data from the API
    $.getJSON('/api/outputs', function (outputs) {
      outputNodes.each(updateOutput(outputs));
    });
  }
}

function updateOutput(outputs) {
  // Updates the mixed color and layer information for a single output
  return function(outputIndex) {
    var outputJson = outputs[outputIndex],
        outputNode = $(this);
    outputNode.find('.mixed').css('background-color',
                                  outputJson.mixedColorHex);
    outputNode.find('.layer').each(updateLayerInfo(outputJson));
  }
}

function updateLayerInfo(outputJson) {
  // Updates the color and assorted information for a single output layer
  return function(listIndex) {
    var currentLayer = outputJson.layerCount - 1 - listIndex,
        layerJson = outputJson.layers[currentLayer],
        layerNode = $(this);
    layerNode.find('.color').css('background-color', layerJson.colorHex);
    layerNode.find('.blender').text(layerJson.blender);
    layerNode.find('.envelope').text(layerJson.envelope);
    layerNode.find('.opacity').text(Math.round(layerJson.opacity * 100));
  }
}
