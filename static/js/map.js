
//
// Global map.js variables
//

var map;
var rawDataIsLoading = false;
var locationMarker;
var marker;
var startrow = 1;
var numrecords = 1000;
var selectedStyle = 'light';

var map_data = {
	pickup_markers: [],
	dropoff_markers: []
};


//
// LocalStorage helpers
//

var StoreTypes = {
  Boolean: {
    parse: function(str) {
      switch (str.toLowerCase()) {
        case '1':
        case 'true':
        case 'yes':
          return true;
        default:
          return false;
      }
    },
    stringify: function(b) {
      return b ? 'true' : 'false';
    }
  },
  JSON: {
    parse: function(str) {
      return JSON.parse(str);
    },
    stringify: function(json) {
      return JSON.stringify(json);
    }
  },
  String: {
    parse: function(str) {
      return str;
    },
    stringify: function(str) {
      return str;
    }
  },
  Number: {
    parse: function(str) {
      return parseInt(str, 10);
    },
    stringify: function(number) {
      return number.toString();
    }
  }
};

var StoreOptions = {
  map_style: {
    default: 'roadmap',
    type: StoreTypes.String
  },
  showDropoffs: {
	  default: true,
	  type: StoreTypes.Boolean
  },
  showPickups: {
	  default: true,
	  type: StoreTypes.Boolean
  },
  showCongestion: {
	  default: false,
	  type: StoreTypes.Boolean
  }
  
};

var Store = {
  getOption: function(key) {
    var option = StoreOptions[key];
    if (!option) {
      throw "Store key was not defined " + key;
    }
    return option;
  },
  get: function(key) {
    var option = this.getOption(key);
    var optionType = option.type;
    var rawValue = localStorage[key];
    if (rawValue === null || rawValue === undefined) {
      return option.default;
    }
    var value = optionType.parse(rawValue);
    return value;
  },
  set: function(key, value) {
    var option = this.getOption(key);
    var optionType = option.type || StoreTypes.String;
    var rawValue = optionType.stringify(value);
    localStorage[key] = rawValue;
  },
  reset: function(key) {
    localStorage.removeItem(key);
  }
};

//
// Functions
//

function initMap() {
  map = new google.maps.Map(document.getElementById('map'), {
    center: {
      lat: center_lat,
      lng: center_lng
    },
    zoom: 13,
    fullscreenControl: true,
    streetViewControl: false,
    mapTypeControl: true,
    mapTypeControlOptions: {
      style: google.maps.MapTypeControlStyle.DROPDOWN_MENU,
      position: google.maps.ControlPosition.RIGHT_TOP,
    },

  });

  //var marker = createSearchMarker();
  // hardcoded to central park ny/ny
  //var newmarker = setupMarker({latitude:40.757485 , longitude:-73.978466});
  initSidebar();
  google.maps.event.addListenerOnce(map, 'idle', function() {
    updateMap();
  });

  google.maps.event.addListener(map, 'zoom_changed', function() {
    // redraw the markers
  });
}

function createSearchMarker() {
  marker = new google.maps.Marker({ //need to keep reference.
    position: {
      lat: center_lat,
      lng: center_lng
    },
    map: map,
    animation: google.maps.Animation.DROP,
    draggable: false
  });

  var oldLocation = null;
  google.maps.event.addListener(marker, 'dragstart', function() {
    oldLocation = marker.getPosition();
  });

  google.maps.event.addListener(marker, 'dragend', function() {
    var newLocation = marker.getPosition();
    changeSearchLocation(newLocation.lat(), newLocation.lng())
      .done(function() {
        oldLocation = null;
      })
      .fail(function() {
        if (oldLocation) {
          marker.setPosition(oldLocation);
        }
      });
  });

  return marker;
}

function initSidebar() {
  
  var searchBox = new google.maps.places.SearchBox(document.getElementById('next-location'));
  $("#next-location").css("background-color", $('#geoloc-switch').prop('checked') ? "#e0e0e0" : "#ffffff");

  searchBox.addListener('places_changed', function() {
    var places = searchBox.getPlaces();

    if (places.length == 0) {
      return;
    }

    var loc = places[0].geometry.location;
    changeLocation(loc.lat(), loc.lng());
  });
}

function clearSelection() {
  if (document.selection) {
    document.selection.empty();
  } else if (window.getSelection) {
    window.getSelection().removeAllRanges();
  }
}

function addListeners(marker) {
  
}

function clearMarkers() {
  // remove markers by key
  
}

function loadRawData() {

  return $.ajax({
    url: "raw_data",
    type: 'GET',
    data: {
      'startrow': startrow,
	  'numrecords': numrecords
    },
    dataType: "json",
    beforeSend: function() {
	  console.log("getting records: " + startrow.toString() + " to " + (startrow + numrecords).toString())
      if (rawDataIsLoading) {
        return false;
      } else {
        rawDataIsLoading = true;
      }
    },
    complete: function() {
      rawDataIsLoading = false;
    }
  })
}

function processClusterMarkers(item) {
	  
	  //map_data.cabs[item.id] = item
	  var latLng = new google.maps.LatLng(item.pickup_lat, item.pickup_long);
	  var pickup_marker = new google.maps.Marker({
		position: latLng,
    //icon: 'static/images/pickup.png'
		});
	  map_data.pickup_markers.push(pickup_marker)
	  return marker;
    }

function processMarkers(item) {
	  
	if (Store.get('showPickups')){
	  var pickup_latLng = new google.maps.LatLng(item.pickup_lat, item.pickup_long);
	  var pickup_marker = new google.maps.Marker({
	position: pickup_latLng,
    icon: 'static/images/pickup.png',
	map: map
		});
		map_data.pickup_markers.push(pickup_marker);
	}
	if (Store.get('showDropoffs')){
	  var dropoff_latLng = new google.maps.LatLng(item.dropoff_lat, item.dropoff_long);
	  var dropoff_marker = new google.maps.Marker({
	position: dropoff_latLng,
    icon: 'static/images/dropoff.png',
	map: map
		});
		map_data.dropoff_markers.push(dropoff_marker);
	}
}

 // Removes the markers from the map, but keeps them in the array.
      function clearMarkers() {
        setMapOnAll(null);
      }

      // Shows any markers currently in the array.
      function showMarkers() {
        setMapOnAll(map);
      }

      // Deletes all markers in the array by removing references to them.
      function deleteMarkers() {
		  console.log('deleting...')
        clearMarkers();
        markers = [];
      }
// Sets the map on all markers in the array.
      function setMapOnAll(map) {
        for (var i = 0; i < dropoff_markers.length; i++) {
			map_data["dropoff_markers"][i].setMap(map);
			map_data["pickup_markers"][i].setMap(map);
        }
      }

function updateMap() {
  loadRawData().done(function(result) {
    
	var options = {
		imagePath:'static/images/m'
	}
	var hasMarkers = false;
	$.each(result.cabs, function(){
		//processClusterMarkers($(this)[0])
		processMarkers($(this)[0])
		hasMarkers = true
	});
	
	if (hasMarkers){
		startrow += numrecords;
	}
		
	
	var markerCluster1 = new MarkerClusterer(map, map_data.dropoff_markers, options)
	var markerCluster2 = new MarkerClusterer(map, map_data.pickup_markers, options)
  });
}


function centerMap(lat, lng, zoom) {
  var loc = new google.maps.LatLng(lat, lng);

  map.setCenter(loc);

  if (zoom) {
    map.setZoom(zoom)
  }
}


$(function() {
  // run interval timers to regularly update map
  window.setInterval(updateMap, 5000);
  //updateMap // TODO: only call it once for demo purposes
  
  
  
  //Wipe off/restore map icons when switches are toggled
  function buildSwitchChangeListener(type, storageKey) {
    return function () {
      Store.set(storageKey, this.checked);
		  for (var i = 0; i < map_data[type].length; i++ ){
			  map_data[type][i].setMap(this.checked ? map : null);
		  }
	  }
  }

  // Setup UI element interactions
  $('#dropoff-switch').change(buildSwitchChangeListener(["dropoff_markers"], "showDropoffs"));
  $('#pickup-switch').change(buildSwitchChangeListener(["pickup_markers"], "showPickups"));
  $('#congestion-switch').change(buildSwitchChangeListener(["congestion"], "showCongestion"));
  
});