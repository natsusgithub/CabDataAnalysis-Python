
//
// Global map.js variables
//

var map;
var rawDataIsLoading = false;
var locationMarker;
var marker;

var selectedStyle = 'light';

var map_data = {
	cabs: {}
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

  var marker = createSearchMarker();
  // hardcoded to central park ny/ny
  var newmarker = setupMarker({latitude:40.757485 , longitude:-73.978466});
  addMyLocationButton();
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

function pad(number) {
  return number <= 99 ? ("0" + number).slice(-2) : number;
}

function myLabel() {
  var str;
  
    str = `
      <div>
       this is a label!
      </div>`;
  
  return str;
}


function getGoogleSprite(index, sprite, display_height) {
  display_height = Math.max(display_height, 3);
  var scale = display_height / sprite.icon_height;
  // Crop icon just a tiny bit to avoid bleedover from neighbor
  var scaled_icon_size = new google.maps.Size(scale * sprite.icon_width - 1, scale * sprite.icon_height - 1);
  var scaled_icon_offset = new google.maps.Point(
    (index % sprite.columns) * sprite.icon_width * scale + 0.5,
    Math.floor(index / sprite.columns) * sprite.icon_height * scale + 0.5);
  var scaled_sprite_size = new google.maps.Size(scale * sprite.sprite_width, scale * sprite.sprite_height);
  var scaled_icon_center_offset = new google.maps.Point(scale * sprite.icon_width / 2, scale * sprite.icon_height / 2);

  return {
    url: sprite.filename,
    size: scaled_icon_size,
    scaledSize: scaled_sprite_size,
    origin: scaled_icon_offset,
    anchor: scaled_icon_center_offset
  };
}
function setupMarker(item, skipNotification, isBounceDisabled) {
  // Scale icon size up with the map exponentially
  
  var icon = "static/images/pickup.png"
  var animationDisabled = false;
  if (isBounceDisabled == true) {
    animationDisabled = true;
  }

  var marker = new google.maps.Marker({
    position: {
      lat: item.latitude,
      lng: item.longitude
    },
    zIndex: 9999,
    optimized: false,
    map: map,
    icon: icon,
    animationDisabled: true,
  });

  marker.addListener('click', function() {
    this.setAnimation(null);
    this.animationDisabled = true;
  });

  marker.infoWindow = new google.maps.InfoWindow({
    content: myLabel(),
    disableAutoPan: true
  });

  addListeners(marker);
  return marker;
}


function clearSelection() {
  if (document.selection) {
    document.selection.empty();
  } else if (window.getSelection) {
    window.getSelection().removeAllRanges();
  }
}

function addListeners(marker) {
  marker.addListener('click', function() {
    marker.infoWindow.open(map, marker);
    clearSelection();
    marker.persist = true;
  });

  google.maps.event.addListener(marker.infoWindow, 'closeclick', function() {
    marker.persist = null;
  });

  marker.addListener('mouseover', function() {
    marker.infoWindow.open(map, marker);
    clearSelection();
  });

  marker.addListener('mouseout', function() {
    if (!marker.persist) {
      marker.infoWindow.close();
    }
  });

  return marker
}

function clearMarkers() {
  // remove markers by key
  
}

function showInBoundsMarkers(markers) {
  $.each(markers, function(key, value) {
    var marker = markers[key].marker;
    var show = false;
    if (!markers[key].hidden) {
      if (typeof marker.getPosition === 'function') {
        if (map.getBounds().contains(marker.getPosition())) {
          show = true;
        }
      } else if (typeof marker.getCenter === 'function') {
        if (map.getBounds().contains(marker.getCenter())) {
          show = true;
        }
      }
    }

    if (show && !markers[key].marker.getMap()) {
      markers[key].marker.setMap(map);
    } else if (!show && markers[key].marker.getMap()) {
      markers[key].marker.setMap(null);
    }
  });
}

function loadRawData() {

  return $.ajax({
    url: "raw_data",
    type: 'GET',
    data: {
      
    },
    dataType: "json",
    beforeSend: function() {
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

function processMarkers(i, item) {
      item.marker = setupMarker(item);
      map_data.cabs[item.id] = item;
    }

function clearOldMarkers(){
	// this will clear
}
	
function updateMap() {
  loadRawData().done(function(result) {
    $.each(result.cabs, processMarkers);
    clearOldMarkers();
  });
}

function getPointDistance(pointA, pointB) {
  return google.maps.geometry.spherical.computeDistanceBetween(pointA, pointB);
}

function myLocationButton(map, marker) {
  var locationContainer = document.createElement('div');

  var locationButton = document.createElement('button');
  locationButton.style.backgroundColor = '#fff';
  locationButton.style.border = 'none';
  locationButton.style.outline = 'none';
  locationButton.style.width = '28px';
  locationButton.style.height = '28px';
  locationButton.style.borderRadius = '2px';
  locationButton.style.boxShadow = '0 1px 4px rgba(0,0,0,0.3)';
  locationButton.style.cursor = 'pointer';
  locationButton.style.marginRight = '10px';
  locationButton.style.padding = '0px';
  locationButton.title = 'Your Location';
  locationContainer.appendChild(locationButton);

  var locationIcon = document.createElement('div');
  locationIcon.style.margin = '5px';
  locationIcon.style.width = '18px';
  locationIcon.style.height = '18px';
  locationIcon.style.backgroundImage = 'url(static/images/mylocation-sprite-1x.png)';
  locationIcon.style.backgroundSize = '180px 18px';
  locationIcon.style.backgroundPosition = '0px 0px';
  locationIcon.style.backgroundRepeat = 'no-repeat';
  locationIcon.id = 'current-location';
  locationButton.appendChild(locationIcon);

  locationButton.addEventListener('click', function() {
    var currentLocation = document.getElementById('current-location');
    var imgX = '0';
    var animationInterval = setInterval(function() {
      if (imgX == '-18') imgX = '0';
      else imgX = '-18';
      currentLocation.style.backgroundPosition = imgX + 'px 0';
    }, 500);
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(function(position) {
        var latlng = new google.maps.LatLng(position.coords.latitude, position.coords.longitude);
        locationMarker.setVisible(true);
        locationMarker.setOptions({
          'opacity': 1
        });
        locationMarker.setPosition(latlng);
        map.setCenter(latlng);
        clearInterval(animationInterval);
        currentLocation.style.backgroundPosition = '-144px 0px';
      });
    } else {
      clearInterval(animationInterval);
      currentLocation.style.backgroundPosition = '0px 0px';
    }
  });

  locationContainer.index = 1;
  map.controls[google.maps.ControlPosition.RIGHT_BOTTOM].push(locationContainer);
}

function addMyLocationButton() {
  locationMarker = new google.maps.Marker({
    map: map,
    animation: google.maps.Animation.DROP,
    position: {
      lat: center_lat,
      lng: center_lng
    },
    icon: {
      path: google.maps.SymbolPath.CIRCLE,
      fillOpacity: 1,
      fillColor: '#1c8af6',
      scale: 6,
      strokeColor: '#1c8af6',
      strokeWeight: 8,
      strokeOpacity: 0.3
    }
  });
  locationMarker.setVisible(false);

  myLocationButton(map, locationMarker);

  google.maps.event.addListener(map, 'dragend', function() {
    var currentLocation = document.getElementById('current-location');
    currentLocation.style.backgroundPosition = '0px 0px';
    locationMarker.setOptions({
      'opacity': 0.5
    });
  });
}

function changeLocation(lat, lng) {
  var loc = new google.maps.LatLng(lat, lng);
  changeSearchLocation(lat, lng).done(function() {
    map.setCenter(loc);
    marker.setPosition(loc);
  });
}

function changeSearchLocation(lat, lng) {
  return $.post("next_loc?lat=" + lat + "&lon=" + lng, {});
}

function centerMap(lat, lng, zoom) {
  var loc = new google.maps.LatLng(lat, lng);

  map.setCenter(loc);

  if (zoom) {
    map.setZoom(zoom)
  }
}

//
// Page Ready Exection
//

$(function() {
  if (!Notification) {
    console.log('could not load notifications');
    return;
  }

  if (Notification.permission !== "granted") {
    Notification.requestPermission();
  }
});

$(function() {
  // run interval timers to regularly update map
  //window.setInterval(updateMap, 5000);
  updateMap // TODO: only call it once for demo purposes
  
  window.setInterval(function() {
    if (navigator.geolocation && Store.get('geoLocate')) {
      navigator.geolocation.getCurrentPosition(function(position) {
        var baseURL = location.protocol + "//" + location.hostname + (location.port ? ":" + location.port : "");
        var lat = position.coords.latitude;
        var lon = position.coords.longitude;

        //the search function makes any small movements cause a loop. Need to increase resolution
        if (getPointDistance(marker.getPosition(), (new google.maps.LatLng(lat, lon))) > 40) {
          $.post(baseURL + "/next_loc?lat=" + lat + "&lon=" + lon).done(function() {
            var center = new google.maps.LatLng(lat, lon);
            map.panTo(center);
            marker.setPosition(center);
          });
        }
      });
    }
  }, 1000);
  
  //Wipe off/restore map icons when switches are toggled
  function buildSwitchChangeListener(data, data_type, storageKey) {
    return function () {
      Store.set(storageKey, this.checked);
      if (this.checked) {
        updateMap();
      } else {
        $.each(data_type, function(d, d_type) {
          $.each(data[d_type], function (key, value) {
            data[d_type][key].marker.setMap(null);
          });
          data[d_type] = {}
        });
      }
    };
  }

  // Setup UI element interactions
  $('#dropoff-switch').change(buildSwitchChangeListener(map_data, ["dropoff"], "showDropoffs"));
  $('#pickup-switch').change(buildSwitchChangeListener(map_data, ["pickup"], "showPickups"));
  
});