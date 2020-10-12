// creating angular object and injecting dependencies on the next line.
angular
  .module('musicViewer', ['ngMaterial', 'ngMessages','xeditable'])
  .controller('musicCtr', function($scope,$rootScope,$timeout,$http,$sce,$mdSidenav) {
    musicView = this; // controller defined here.
    // opens right sidenav
    // Using demo code from https://material.angularjs.org/latest/demo/sidenav
    this.openRightPanel = function(){
      $mdSidenav('right').toggle();
    };
    // closes right sidenav
    // Using demo code from https://material.angularjs.org/latest/demo/sidenav
    this.closeRightPanel = function(){
      $mdSidenav('right').close();
    };
    // safe apply function if needed
    $scope.safeApply = function(fn) {
      var phase = this.$root.$$phase;
      if(phase == '$apply' || phase == '$digest') {
        if(fn && (typeof(fn) === 'function')) {
          fn();
        }
      } else {
        this.$apply(fn);
      }
    };
    this.manualApplyCall = function(fn){
      $scope.safeApply(fn);
    }
    //Probably from stack overflow but I've been using this for ages, so who knows.
    this.guid = function() {
        function s4() {
            return Math.floor((1 + Math.random()) * 0x10000)
            .toString(16)
            .substring(1);
        }
        return s4() + s4() + s4() + s4() +
        s4() + s4() + s4() + s4();
    };
    // performs ajax get request and performs callbacks using promise pattern
    this.get_request = function(address,successCallback,errorCallback){
        $http({
            method: 'GET',
            url: address
        }).then(successCallback.bind(this),errorCallback.bind(this));
    };
    this.post_request = function(address,postData,successCallback,errorCallback){
      if(typeof postData === "object"){
        $http.post(address,JSON.stringify(postData)).then(successCallback.bind(this),errorCallback.bind(this));
      }
      if(typeof postData === "string"){
        $http.post(address,postData).then(successCallback.bind(this),errorCallback.bind(this));
      }
    };
    // url
    this.origin_url = window.location.origin;
    // code to handle opening angular material menu
    this.menuOpener = function($mdMenu, $event){
      $mdMenu.open();
    };
})
  .config(function($mdThemingProvider){ // configures angular material themes
    // Configure a dark theme with primary foreground yellow
    $mdThemingProvider.theme('docs-dark', 'default')
      .primaryPalette('blue')
      .dark();
  });
