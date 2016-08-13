
//
// Global map.js variables
//

var map;
var heatmap;
var rawDataIsLoading = false;
var locationMarker;
var marker;
var pointArray; 

var map_data = {
	markers: [],
	neighborhoods: [],
	heatmapdata: [],
	cabs: [],
	avgtip: '0.00',
	percentcongestion: '0%',
	percentagetip:'0%',
	avgtimeminutes: '0.00',
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
	scrollwheel: false,
	zoomControl:false,
	disableDoubleClickZoom: true,
	navigationControl: false,
	scaleControl: false,
	streetViewControl: false,
    mapTypeControl: true,
    mapTypeControlOptions: {
      style: google.maps.MapTypeControlStyle.DROPDOWN_MENU,
      position: google.maps.ControlPosition.RIGHT_TOP,
    },
  });
	
  google.maps.event.addListenerOnce(map, 'idle', function() {
    updateMap();
  });
	Store.set("showCongestion", false);
	Store.set("showPickups", false);
  
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
 console.log($('#time').val())
  return $.ajax({
    url: "raw_data",
    type: 'GET',
    data: {
      'neighborhood': $('#neighborhood').val(),
	  'neighborhoodtype': $('input[name=neighborhood-type]:checked').val(),
	  'date': $('#datepicker').val(),
	  'time': $('#timevalue').val(),
	  'ispickup': Store.get('showPickups')
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


function processMarkers(item) {
	  
	  var myicon
	  if (Store.get('showPickups') == true){
		  myicon = 'static/images/pickup_norence.png';
	  }else{
		  myicon = 'static/images/dropoff_norence.png';
	  }
	  var latLng = new google.maps.LatLng(item.latitude, item.longitude);
	  var marker = new google.maps.Marker({
		position: latLng,
		icon: myicon,
		map: null
		});
		map_data.markers.push(marker);
	 // var heatmapmarker = {location: latLng, weight: item.congestion_index}	
		
		map_data.heatmapdata.push(latLng);
	
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
		  if (Store.get("showCongestion") == true){
			  
				heatmap.setMap(map)
				clearMarkers();
		  }else{
			for (var i = 0; i < map_data.markers.length; i++) {
				map_data.markers[i].setMap(map);
			}
			heatmap.setMap(null);
		  }
      }
	  
function updateMap() {

	
	  for (var i = 0; i < map_data.markers.length; i++ ){
			  map_data.markers[i].setMap(null);
		  }
		map_data.markers = []
		map_data.heatmapdata =  [];
		loadRawData().done(function(result) {
			
			//process markers
			$.each(result.cabs, function(){
				processMarkers($(this)[0])
			});
		
			// if heatmap doesn't exist yet then create it.  this will be loaded once
			if (!heatmap){
				pointArray = new google.maps.MVCArray(map_data.heatmapdata);
				heatmap = new google.maps.visualization.HeatmapLayer({
					data: pointArray,
					radius: 10,
				});
			}else{
				pointArray.clear();
				for(i = 0; i < map_data.heatmapdata.length; i++){
					pointArray.push(map_data.heatmapdata[i]);
				}
			}
			
			showMarkers();
			map_data.avgtip = (result.avgtip);
			map_data.percentcongestion = (result.percentcongestion);
			map_data.avgtimeminutes = (result.avgtimeminutes);
			map_data.percentagetip = (result.percentagetip);
			
			//update summaries
			$('#tipsummary').html(map_data.avgtip);
			$('#percentagetipsummary').html(map_data.percentagetip);
			$('#congestionsummary').html(map_data.percentcongestion);
			$('#triptimesummary').html(map_data.avgtimeminutes);
			$('.tripcount').html((result.cabs.length));
			
			
  });

}


function centerMap(lat, lng, zoom) {
  var loc = new google.maps.LatLng(lat, lng);

  map.setCenter(loc);

  if (zoom) {
    map.setZoom(zoom)
  }
}

function clearMarkers(deleteMarker){
	for (var i = 0; i < map_data.markers.length; i++ ){
			  map_data.markers[i].setMap(null);
			  if (deleteMarker == true){
				  map_data.markers[i] = null
			  }
		  }
}

$(function() {
  // run interval timers to regularly update map
  //window.setInterval(updateMap, 5000);
  //updateMap() // TODO: only call it once for demo purposes

});