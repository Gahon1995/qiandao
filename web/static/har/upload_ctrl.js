// Generated by CoffeeScript 1.7.1
(function() {
  define(function(require, exports, module) {
    var analysis, utils;
    analysis = require('/static/har/analysis');
    utils = require('/static/utils');
    return angular.module('upload_ctrl', []).controller('UploadCtrl', function($scope, $rootScope, $http) {
      var element, m;
      element = angular.element('#upload-har');
      element.modal('show').on('hide.bs.modal', function() {
        return $scope.is_loaded != null;
      });
      element.find('input[type=file]').on('change', function(ev) {
        return $scope.file = this.files[0];
      });
      if (utils.storage.get('har_har') != null) {
        $scope.local_har = utils.storage.get('har_filename');
      }
      $scope.alert = function(message) {
        return element.find('.alert').text(message).show();
      };
      $scope.loaded = function(loaded) {
        $scope.is_loaded = true;
        $rootScope.$emit('har-loaded', loaded);
        angular.element('#upload-har').modal('hide');
        return true;
      };
      $scope.load_remote = function(id) {
        element.find('button').button('loading');
        return $http.post("/har/edit/" + id).success(function(data, status, headers, config) {
          element.find('button').button('reset');
          return $scope.loaded(data);
        }).error(function(data, status, headers, config) {
          $scope.alert(data);
          return element.find('button').button('reset');
        });
      };
      if (!$scope.local_har && (m = location.pathname.match(/\/har\/edit\/(\d+)/))) {
        $scope.load_remote(m[1]);
      }
      $scope.load_file = function(data) {
        var loaded;
        loaded = {
          filename: $scope.file.name,
          har: analysis.analyze(data, {
            username: $scope.username,
            password: $scope.password
          }),
          env: {
            username: $scope.username,
            password: $scope.password
          },
          upload: true
        };
        return $scope.loaded(loaded);
      };
      $scope.load_local_har = function() {
        var loaded;
        loaded = {
          filename: utils.storage.get('har_filename'),
          har: utils.storage.get('har_har'),
          env: utils.storage.get('har_env'),
          upload: true
        };
        return $scope.loaded(loaded);
      };
      $scope.delete_local = function() {
        utils.storage.del('har_har');
        utils.storage.del('har_env');
        utils.storage.del('har_filename');
        $scope.local_har = void 0;
        if (!$scope.local_har && (m = location.pathname.match(/\/har\/edit\/(\d+)/))) {
          return $scope.load_remote(m[1]);
        }
      };
      return $scope.upload = function() {
        var reader;
        if ($scope.file == null) {
          $scope.alert('还没选择文件啊，亲');
          return false;
        }
        if ($scope.file.size > 50 * 1024 * 1024) {
          $scope.alert('文件大小超过50M');
          return false;
        }
        element.find('button').button('loading');
        reader = new FileReader();
        reader.onload = function(ev) {
          return $scope.$apply(function() {
            var error;
            $scope.uploaded = true;
            try {
              return $scope.load_file(angular.fromJson(ev.target.result));
            } catch (_error) {
              error = _error;
              console.log(error);
              return $scope.alert('HAR 格式错误');
            } finally {
              element.find('button').button('reset');
            }
          });
        };
        return reader.readAsText($scope.file);
      };
    });
  });

}).call(this);