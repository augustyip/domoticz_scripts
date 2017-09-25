import Vue from 'vue'


var domoticzEndpoint = 'http://augustyip.mynetgear.com:58080/json.htm?type=devices&rid=13'
var app = new Vue({
  el: '#app',
  data: {
    items : []
  },
  methods: {
    loadData: function () {
      this.$http.get(domoticzEndpoint).then(response => {
        // get body data
        this.items = response.json;
    
      }, response => {
        // error callback
      });
  }
  },
  ready: function () {
    this.loadData();

    setInterval(function () {
      this.loadData();
    }.bind(this), 30000); 
  }
})
