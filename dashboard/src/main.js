import Vue from 'vue'
import VueResource from 'vue-resource'
Vue.use(VueResource);

var domoticzEndpoint = 'http://augustyip.mynetgear.com:58080/json.htm?type=devices&filter=all&used=true&order=Name'
var app = new Vue({
  el: '#app',
  data: {
    temp_humidity : []
  },
  methods: {
    loadData: function () {
      console.log('here')
      this.$http.get(domoticzEndpoint).then(response => {
        // // get body data
        console.log(response.data)
        this.temp_humidity = response.data
      }, response => {
        // error callback
      });
  }
  },
  mounted: function () {
    this.loadData();
    setInterval(function () {
      this.loadData();
    }.bind(this), 30000); 
  }
})
